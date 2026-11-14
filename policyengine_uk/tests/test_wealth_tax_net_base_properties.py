"""Wealth tax base (#2556).

``gov.contrib.ubi_center.wealth_tax`` is a hypothetical annual tax on household
net wealth, a marginal schedule of three bands with zero rates at baseline.
Its base is ``net_wealth``: property, corporate and private pension wealth and
savings, less mortgage, consumer and student loan debt. Before #2556 the
schedule applied to gross ``total_wealth``, so wealth held against a mortgage
was taxed.

Invariants, for households in 2026 with assets and debts drawn freely and a
schedule drawn freely (thresholds non-negative and ascending, rates between 0
and 10%):

1. Differential: ``wealth_tax`` equals a reference marginal schedule applied to
   assets less debts, computed here from the inputs.
2. Debts never raise the tax: more mortgage, consumer or student loan debt
   leaves ``wealth_tax`` the same or lower, and more assets never lower it.
3. Debts at or above assets leave no tax, whatever the schedule.
4. Debt-free households are unchanged: with no debt the base is
   ``total_wealth``, the base before #2556.
5. Bounds: 0 <= ``wealth_tax`` <= top rate x max(net wealth, 0).
"""

import math

from hypothesis import HealthCheck, example, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation

YEAR = 2026
PARAMETER = "gov.contrib.ubi_center.wealth_tax"
ASSETS = ("property_wealth", "corporate_wealth", "private_pension_wealth", "savings")
HOUSEHOLD_DEBTS = ("mortgage_debt", "consumer_debt")
# The model stores money as float32. Every amount drawn here is a whole number
# of thousands of pounds, and every sum stays below £134m (2**27), so float32
# holds each one exactly; the tolerance covers rounding the tax itself.
TOLERANCE = 2.0


def _reference_tax(base, thresholds, rates):
    """A marginal schedule: each rate applies to the part of the base between
    its threshold and the next one."""
    tax = 0.0
    uppers = list(thresholds[1:]) + [math.inf]
    for lower, upper, rate in zip(thresholds, uppers, rates):
        if base > lower:
            tax += rate * (min(base, upper) - lower)
    return tax


def _net_wealth(household):
    return (
        sum(household.get(name, 0) for name in ASSETS)
        - sum(household.get(name, 0) for name in HOUSEHOLD_DEBTS)
        - sum(household.get("student_loans", ()))
    )


def _simulate(households, thresholds, rates):
    """Run every household in one simulation under the drawn schedule and
    return each household's wealth tax, net wealth and total wealth."""
    people, benunits, situation_households = {}, {}, {}
    for i, household in enumerate(households):
        members = []
        for j, balance in enumerate(household.get("student_loans", (0,))):
            person = f"h{i}p{j}"
            people[person] = {
                "age": {YEAR: 50},
                "student_loan_balance": {YEAR: balance},
            }
            members.append(person)
        benunits[f"b{i}"] = {"members": members}
        situation_households[f"h{i}"] = {
            "members": members,
            **{
                name: {YEAR: household.get(name, 0)}
                for name in ASSETS + HOUSEHOLD_DEBTS
            },
        }
    reform = {}
    for i, (threshold, rate) in enumerate(zip(thresholds, rates)):
        reform[f"{PARAMETER}[{i}].threshold"] = {
            f"{YEAR}-01-01.{YEAR}-12-31": threshold
        }
        reform[f"{PARAMETER}[{i}].rate"] = {f"{YEAR}-01-01.{YEAR}-12-31": rate}
    sim = Simulation(
        situation={
            "people": people,
            "benunits": benunits,
            "households": situation_households,
        },
        reform=reform,
    )
    return {
        name: [float(value) for value in sim.calculate(name, YEAR)]
        for name in ("wealth_tax", "net_wealth", "total_wealth")
    }


thousands = st.integers(min_value=0, max_value=50_000).map(lambda k: k * 1_000)
small_thousands = st.integers(min_value=0, max_value=5_000).map(lambda k: k * 1_000)
household_strategy = st.fixed_dictionaries(
    {
        "property_wealth": thousands,
        "corporate_wealth": thousands,
        "private_pension_wealth": small_thousands,
        "savings": small_thousands,
        "mortgage_debt": thousands,
        "consumer_debt": small_thousands,
        "student_loans": st.lists(small_thousands, min_size=1, max_size=2),
    }
)
schedule_strategy = st.tuples(
    st.lists(
        st.integers(min_value=0, max_value=60_000).map(lambda k: k * 1_000),
        min_size=3,
        max_size=3,
        unique=True,
    ).map(sorted),
    st.lists(
        st.integers(min_value=0, max_value=100).map(lambda k: k / 1_000),
        min_size=3,
        max_size=3,
    ),
)
extra = st.integers(min_value=1, max_value=20_000).map(lambda k: k * 1_000)

ISSUE_HOUSEHOLD = {
    "property_wealth": 15_000_000,
    "corporate_wealth": 0,
    "private_pension_wealth": 0,
    "savings": 0,
    "mortgage_debt": 6_000_000,
    "consumer_debt": 0,
    "student_loans": [0],
}
# The measure reported for the 28 October 2026 Budget: 2% on net assets above
# £10m, with the default third threshold (£1bn) also at 2%.
BUDGET_SCHEDULE = ([0, 10_000_000, 1_000_000_000], [0, 0.02, 0.02])


@settings(
    max_examples=10,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow],
)
@given(
    household=household_strategy,
    schedule=schedule_strategy,
    more_debt=extra,
    more_assets=extra,
)
# The reproduction in #2556: £15m of property against a £6m mortgage is £9m of
# net wealth, below the £10m threshold, so no tax (£100,000 before the fix).
@example(
    household=ISSUE_HOUSEHOLD,
    schedule=BUDGET_SCHEDULE,
    more_debt=1_000_000,
    more_assets=2_000_000,
)
def test_wealth_tax_is_the_schedule_on_net_wealth(
    household, schedule, more_debt, more_assets
):
    thresholds, rates = schedule
    first_loan, *other_loans = household["student_loans"]
    debt_free = {
        **household,
        "mortgage_debt": 0,
        "consumer_debt": 0,
        "student_loans": [0] * len(household["student_loans"]),
    }
    underwater = {**household, "mortgage_debt": sum(household[a] for a in ASSETS)}
    variants = [
        household,
        {**household, "mortgage_debt": household["mortgage_debt"] + more_debt},
        {**household, "consumer_debt": household["consumer_debt"] + more_debt},
        {**household, "student_loans": [first_loan + more_debt, *other_loans]},
        {**household, "savings": household["savings"] + more_assets},
        {
            **household,
            "property_wealth": household["property_wealth"] + more_assets,
        },
        debt_free,
        underwater,
    ]
    result = _simulate(variants, thresholds, rates)
    taxes = result["wealth_tax"]

    for i, variant in enumerate(variants):
        net = _net_wealth(variant)
        # 1. Differential against the reference schedule on net wealth.
        assert abs(result["net_wealth"][i] - net) <= TOLERANCE, i
        expected = _reference_tax(net, thresholds, rates)
        assert abs(taxes[i] - expected) <= TOLERANCE, (i, taxes[i], expected)
        # 5. Bounds.
        assert taxes[i] >= 0, i
        assert taxes[i] <= max(rates) * max(net, 0) + TOLERANCE, i

    base, more_mortgage, more_consumer, more_loan, more_savings, more_property = taxes[
        :6
    ]
    # 2. Debts never raise the tax; assets never lower it.
    for with_more_debt in (more_mortgage, more_consumer, more_loan):
        assert with_more_debt <= base + TOLERANCE
    for with_more_assets in (more_savings, more_property):
        assert with_more_assets >= base - TOLERANCE
    # 3. Debts at or above assets: no tax.
    assert taxes[7] <= TOLERANCE
    # 4. A debt-free household's base is total wealth, as before #2556.
    assert abs(result["net_wealth"][6] - result["total_wealth"][6]) <= TOLERANCE
    assert (
        abs(taxes[6] - _reference_tax(result["total_wealth"][6], thresholds, rates))
        <= TOLERANCE
    )
    assert base <= taxes[6] + TOLERANCE


def test_issue_2556_household_owes_nothing_under_the_budget_measure():
    """£15m of property and a £6m mortgage is £9m of net wealth. A 2% tax on
    net wealth above £10m charges nothing; on gross wealth it charged
    2% x £5m = £100,000."""
    result = _simulate([ISSUE_HOUSEHOLD], *BUDGET_SCHEDULE)
    assert result["total_wealth"] == [15_000_000]
    assert result["net_wealth"] == [9_000_000]
    assert result["wealth_tax"] == [0]
