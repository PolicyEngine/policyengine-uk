"""share_like_capital replaces corporate_wealth in the means-test capital lists.

Invariants:
1. share_like_capital is corporate_wealth as supplied (any sign, any fraction)
   unless the itemised components are positive and exceed it by more than the
   float32 rounding tolerance, in which case it is exactly their sum.
2. Differential: for identical inputs that carry no components, or components
   consistent with corporate_wealth, every programme's assessable capital, and
   UC eligibility, equal those under the original lists (corporate_wealth),
   exactly, annually and monthly.
3. A household given only the components has them counted, down to a penny.
4. A disregarded company holding (UC reg 77(2)) is budgeted against, and
   leaves the UC financial pool from, share_like_capital, whether it was
   entered within corporate_wealth or as an itemised component.
"""

import numpy as np
import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from policyengine_uk import CountryTaxBenefitSystem, Simulation
from policyengine_uk.variables.household.wealth.share_like_capital import (
    RELATIVE_TOLERANCE,
)

COMPONENTS = (
    "directly_held_shares",
    "unit_and_investment_trusts",
    "stocks_and_shares_isa",
)
SOURCE_LISTS = {
    "uc_assessable_capital": "gov.dwp.universal_credit.means_test.capital.sources",
    "housing_benefit_assessable_capital": "gov.dwp.housing_benefit.means_test.capital.sources",
    "income_support_assessable_capital": "gov.dwp.income_support.means_test.capital.sources",
    "jsa_income_assessable_capital": "gov.dwp.JSA.income.capital.sources",
    "esa_income_assessable_capital": "gov.dwp.ESA.income.capital.sources",
    "pension_credit_assessable_capital": "gov.dwp.pension_credit.income.capital.sources",
}
YEAR = 2026
SETTINGS = settings(
    max_examples=25,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)

system = CountryTaxBenefitSystem()


def _node(path):
    node = system.parameters
    for part in path.split("."):
        node = getattr(node, part)
    return node


def _parameter(path):
    return _node(path)(f"{YEAR}-01-01")


ORIGINAL_LISTS = {
    path: [
        "corporate_wealth" if source == "share_like_capital" else source
        for source in _parameter(path)
    ]
    for path in SOURCE_LISTS.values()
}
ORIGINAL_REFORM = {
    path: {f"{YEAR}-01-01.{YEAR + 4}-12-31": sources}
    for path, sources in ORIGINAL_LISTS.items()
}

# Pounds and pence, as a dataset stores them in float64; the engine rounds
# each to float32, which is the rounding the tolerance has to absorb.
money = st.integers(min_value=0, max_value=20_000_000).map(lambda pence: pence / 100)
signed_money = st.integers(min_value=-500_000, max_value=20_000_000).map(
    lambda pence: pence / 100
)


def _situation(households):
    """One single-adult household per entry; ages alternate 30 and 70."""
    people, benunits, hhs = {}, {}, {}
    for i, assets in enumerate(households):
        people[f"p{i}"] = {"age": {YEAR: 70 if i % 2 else 30}}
        benunits[f"b{i}"] = {"members": [f"p{i}"], "would_claim_uc": {YEAR: True}}
        hhs[f"h{i}"] = {
            "members": [f"p{i}"],
            **{name: {YEAR: float(value)} for name, value in assets.items()},
        }
    return {"people": people, "benunits": benunits, "households": hhs}


def _results(households, reform=None, period=YEAR):
    sim = Simulation(situation=_situation(households), reform=reform)
    out = {v: sim.calculate(v, period) for v in SOURCE_LISTS}
    out["is_uc_eligible"] = sim.calculate("is_uc_eligible", period)
    out["share_like_capital"] = sim.calculate("share_like_capital", YEAR)
    return out


def _assert_same_as_original(households):
    # A projected year as well, where the inputs are uprated.
    for period in (YEAR, f"{YEAR}-01", YEAR + 1, f"{YEAR + 1}-01"):
        new = _results(households, period=period)
        old = _results(households, reform=ORIGINAL_REFORM, period=period)
        for variable in (*SOURCE_LISTS, "is_uc_eligible"):
            assert np.array_equal(new[variable], old[variable]), (variable, period)


@pytest.mark.parametrize("variable", SOURCE_LISTS)
def test_lists_name_share_like_capital_only(variable):
    sources = list(_parameter(SOURCE_LISTS[variable]))
    assert "share_like_capital" in sources
    assert "corporate_wealth" not in sources
    assert not set(COMPONENTS) & set(sources)
    # Where a programme lists the sources whose sale incurs expenses, it names
    # the same share-like variable, or shares would silently lose the
    # deduction.
    node = _node(SOURCE_LISTS[variable].rsplit(".", 1)[0])
    if "sale_expenses" in node.children:
        sale = list(node.sale_expenses.sources(f"{YEAR}-01-01"))
        assert not {"corporate_wealth", *COMPONENTS} & set(sale)


@SETTINGS
@given(
    st.lists(
        st.tuples(signed_money, st.tuples(money, money, money), st.booleans()),
        min_size=1,
        max_size=40,
    )
)
def test_share_like_capital_keeps_the_supplied_aggregate(rows):
    households = []
    for corporate_wealth, components, itemise in rows:
        assets = {"corporate_wealth": corporate_wealth}
        if itemise:
            assets |= dict(zip(COMPONENTS, components))
        households.append(assets)
    got = _results(households)["share_like_capital"]
    for value, assets in zip(got, households):
        cw = np.float32(assets["corporate_wealth"])
        itemised = np.float32(0)
        for component in COMPONENTS:
            itemised = np.float32(itemised + np.float32(assets.get(component, 0)))
        tolerance = RELATIVE_TOLERANCE * max(abs(cw), itemised)
        if itemised > 0 and itemised - cw > tolerance:
            assert value == itemised  # exactly the components' sum
        else:
            assert value == cw  # exactly the supplied aggregate


@SETTINGS
@given(
    st.lists(
        st.tuples(money, signed_money, st.tuples(money, money, money), st.booleans()),
        min_size=1,
        max_size=30,
    )
)
def test_capital_matches_the_original_lists(rows):
    """Unsplit, or split consistently: identical to listing corporate_wealth."""
    households = []
    for savings, corporate_wealth, components, split in rows:
        assets = {"savings": savings, "corporate_wealth": corporate_wealth}
        if split:
            assets |= dict(zip(COMPONENTS, components))
            assets["corporate_wealth"] = float(sum(components))
        households.append(assets)
    _assert_same_as_original(households)


def test_float32_rounding_at_the_limit_keeps_eligibility():
    """Components whose float32 sum overshoots £16,000 by a fraction of a penny."""
    households = [
        {
            "savings": 0,
            "corporate_wealth": 16_000,
            "directly_held_shares": 6_744.81,
            "unit_and_investment_trusts": 6_581.24,
            "stocks_and_shares_isa": 2_673.95,
        },
        {"savings": 6_001, "corporate_wealth": -2},
        {"savings": 15_999.99, "corporate_wealth": 0.01},
    ]
    _assert_same_as_original(households)
    assert _results(households)["share_like_capital"][0] == 16_000


def test_one_unit_of_float32_rounding_above_a_power_of_two_keeps_the_aggregate():
    """Pence-valued components whose float32 sum lands one unit in the last place
    (£0.00195) above £16,384.01: more than 1e-7 of the value, less than 1e-6."""
    households = [
        {
            "savings": 0,
            "corporate_wealth": 16_384.01,
            "directly_held_shares": 16_015.98,
            "unit_and_investment_trusts": 286.98,
            "stocks_and_shares_isa": 81.05,
        }
    ]
    itemised = np.float32(
        np.float32(np.float32(16_015.98) + np.float32(286.98)) + np.float32(81.05)
    )
    assert itemised - np.float32(16_384.01) == np.float32(0.001953125)
    assert _results(households)["share_like_capital"][0] == np.float32(16_384.01)
    _assert_same_as_original(households)


def test_a_component_penny_at_the_limit_counts():
    """A penny of shares with no corporate_wealth counts like a penny of it."""
    as_component = [{"savings": 16_000, "directly_held_shares": 0.01}]
    as_aggregate = [{"savings": 16_000, "corporate_wealth": 0.01}]
    for period in (YEAR, f"{YEAR}-01"):
        component = _results(as_component, period=period)
        aggregate = _results(as_aggregate, period=period)
        assert component["share_like_capital"][0] == np.float32(0.01)
        for variable in (*SOURCE_LISTS, "is_uc_eligible"):
            assert np.array_equal(component[variable], aggregate[variable]), variable
        assert not component["is_uc_eligible"][0]


def test_a_genuine_excess_over_the_aggregate_counts():
    """Ten pence of components above the aggregate is a holding, not rounding."""
    households = [
        {
            "corporate_wealth": 16_000,
            "directly_held_shares": 10_000.10,
            "stocks_and_shares_isa": 6_000,
        }
    ]
    assert _results(households)["share_like_capital"][0] == np.float32(16_000.10)


def test_components_alone_are_counted():
    households = [
        {
            "savings": 1_000,
            "directly_held_shares": 4_000,
            "unit_and_investment_trusts": 3_000,
            "stocks_and_shares_isa": 5_000,
        }
    ]
    got = _results(households)
    assert got["share_like_capital"][0] == 12_000
    assert got["uc_assessable_capital"][0] == 13_000


def test_a_disregarded_company_holding_leaves_the_capital_that_counts_it():
    """UC reg 77(2): a holding entered as an itemised component leaves the
    pool as one entered within corporate_wealth does. Two unreported adults
    share £10,000 of savings once the owner's £30,000 holding is disregarded."""
    from policyengine_uk.variables.gov.dwp.universal_credit.household_uc_company_holding_pool_scale import (
        HOLDINGS_SOURCE,
    )

    assert HOLDINGS_SOURCE in _parameter(SOURCE_LISTS["uc_assessable_capital"])
    for shares in ({"corporate_wealth": 30_000}, {"directly_held_shares": 30_000}):
        situation = {
            "people": {
                "owner": {
                    "age": {YEAR: 40},
                    "stands_as_sole_owner_or_partner_of_company": {YEAR: True},
                    "owned_company_carries_on_trade": {YEAR: True},
                    "owned_company_holding_value": {YEAR: 30_000},
                },
                "lodger": {"age": {YEAR: 30}},
            },
            "benunits": {
                "owner_unit": {"members": ["owner"]},
                "lodger_unit": {"members": ["lodger"]},
            },
            "households": {
                "household": {
                    "members": ["owner", "lodger"],
                    "savings": {YEAR: 10_000},
                    **{name: {YEAR: value} for name, value in shares.items()},
                }
            },
        }
        sim = Simulation(situation=situation)
        assert sim.calculate("household_uc_company_holding_pool_scale", YEAR)[0] == 1
        assert sim.calculate("household_uc_pool_company_holdings", YEAR)[0] == 30_000
        assert list(sim.calculate("uc_assessable_capital", YEAR)) == [5_000, 5_000]
