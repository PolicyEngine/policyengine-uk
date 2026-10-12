"""Engineering checks for the branches behind the Marriage Allowance election.

makes_marriage_allowance_election weighs each couple's income tax in two
policyengine-core branches (ITA 2007 ss. 55B, 55C), and uses_property_allowance
weighs income tax in branches of its own (ITTOIA 2005 s. 783BL), so the two
nest whenever a spouse has property income with finance costs. For any
generated population of couples and singles:

1. Determinism under query order: the election, the Marriage Allowance
   reduction, personal allowances, income tax, the property allowance route,
   the finance-cost reduction, Universal Credit and household net income are
   bit-for-bit the same whichever of them is asked for first, with and without
   a reform to the personal allowance dated to the year.
2. Baseline isolation: a reformed simulation's baseline gives bit-for-bit the
   same election, reduction, allowances and income tax as a simulation with no
   reform, whether the reform or the baseline is computed first, and the
   reform's own results do not depend on that order either.
3. Branches are dropped: computing six years leaves no branch behind.
"""

import numpy as np
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation
from policyengine_uk.utils.scenario import Scenario

PROPERTY_SETTINGS = settings(
    max_examples=3,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)
YEARS = [2026, 2027]
ELECTION = "makes_marriage_allowance_election"
OUTPUTS = [
    ELECTION,
    "marriage_allowance_tax_reduction",
    "personal_allowance",
    "income_tax",
    "uses_property_allowance",
    "property_finance_cost_relief",
    "universal_credit",
    "household_net_income",
]
# Each order asks for one output first; the rest follow in list order.
FIRST = [
    ELECTION,
    "universal_credit",
    "income_tax",
    "uses_property_allowance",
    "personal_allowance",
]
BASELINE_OUTPUTS = [
    ELECTION,
    "marriage_allowance_transferable_amount",
    "marriage_allowance_tax_reduction",
    "personal_allowance",
    "income_tax",
]
TENURES = ["RENT_FROM_COUNCIL", "RENT_PRIVATELY", "OWNED_OUTRIGHT"]
REGIONS = ["LONDON", "WALES", "SCOTLAND"]


def personal_allowance_reform(year):
    # A 15,000 allowance for this tax year only (a bare year is the UK fiscal
    # year), so the transferable amount is 1,500 (s. 55B(4)(b), (5)).
    return Scenario(
        parameter_changes={
            "gov.hmrc.income_tax.allowances.personal_allowance.amount": {
                str(year): 15_000
            }
        }
    )


def amounts(cap):
    return st.one_of(st.just(0.0), st.floats(0, cap))


@st.composite
def adults(draw):
    adult = dict(
        age=draw(st.integers(18, 80)),
        employment_income=draw(amounts(50_000)),
        savings_interest_income=draw(amounts(10_000)),
        dividend_income=draw(amounts(5_000)),
        property_income=draw(amounts(15_000)),
        property_finance_costs=draw(amounts(10_000)),
    )
    # Gross receipts are the profit plus expenses; with expenses under the
    # 1,000 property allowance, and finance costs, the route is a choice
    # weighed in branches (ITTOIA 2005 s. 783BH, s. 783BL).
    adult["property_rental_income"] = adult["property_income"] + draw(amounts(1_500))
    if adult["age"] >= 67:
        adult["state_pension"] = draw(amounts(15_000))
    return adult


@st.composite
def families(draw):
    return dict(
        adults=[draw(adults()) for _ in range(draw(st.sampled_from([1, 2, 2])))],
        married=draw(st.sampled_from([True, True, False])),
        children=[draw(st.integers(0, 15)) for _ in range(draw(st.integers(0, 2)))],
        tenure=draw(st.sampled_from(TENURES)),
        rent=draw(amounts(15_000)),
        region=draw(st.sampled_from(REGIONS)),
    )


# Small populations: every adult may have property receipts and finance
# costs, so most simulations run both kinds of branch.
populations = st.lists(families(), min_size=1, max_size=3)


def situation(units, years):
    """One simulation holding every family, with the same inputs each year."""
    years = [years] if isinstance(years, int) else years

    def each_year(value):
        return {year: value for year in years}

    people, benunits, households = {}, {}, {}
    for i, unit in enumerate(units):
        names = []
        for j, adult in enumerate(unit["adults"]):
            person = {variable: each_year(value) for variable, value in adult.items()}
            person["is_claimant_or_partner"] = each_year(True)
            people[f"p{i}_{j}"] = person
            names.append(f"p{i}_{j}")
        for k, age in enumerate(unit["children"]):
            people[f"c{i}_{k}"] = {
                "age": each_year(age),
                "is_claimant_or_partner": each_year(False),
            }
            names.append(f"c{i}_{k}")
        benunits[f"b{i}"] = {
            "members": names,
            "is_married": each_year(unit["married"] and len(unit["adults"]) == 2),
        }
        households[f"h{i}"] = {
            "members": names,
            "rent": each_year(unit["rent"]),
            "tenure_type": each_year(unit["tenure"]),
            "region": each_year(unit["region"]),
        }
    return {"people": people, "benunits": benunits, "households": households}


def calculate(simulation, year, variables, first=None):
    order = [first] + [v for v in variables if v != first] if first else variables
    for variable in order:
        simulation.calculate(variable, year)
    return {v: np.asarray(simulation.calculate(v, year)) for v in variables}


def assert_identical(a, b, message):
    for variable in a:
        assert a[variable].dtype == b[variable].dtype, (variable, message)
        assert np.array_equal(a[variable], b[variable]), (variable, message)


@PROPERTY_SETTINGS
@given(
    units=populations,
    year=st.sampled_from(YEARS),
    reformed=st.booleans(),
)
def test_results_do_not_depend_on_query_order(units, year, reformed):
    scenario = personal_allowance_reform(year) if reformed else None
    results = [
        calculate(
            Simulation(situation=situation(units, year), scenario=scenario),
            year,
            OUTPUTS,
            first=first,
        )
        for first in FIRST
    ]
    for first, result in zip(FIRST[1:], results[1:]):
        assert_identical(results[0], result, f"{first} first: {units}")


@PROPERTY_SETTINGS
@given(units=populations, year=st.sampled_from(YEARS))
def test_reform_leaves_the_baseline_unchanged(units, year):
    plain = calculate(
        Simulation(situation=situation(units, year)), year, BASELINE_OUTPUTS
    )
    # Reform first, then its baseline.
    reformed = Simulation(
        situation=situation(units, year), scenario=personal_allowance_reform(year)
    )
    reform_first = calculate(reformed, year, BASELINE_OUTPUTS)
    baseline_second = calculate(reformed.baseline, year, BASELINE_OUTPUTS)
    # Baseline first, then the reform.
    reformed = Simulation(
        situation=situation(units, year), scenario=personal_allowance_reform(year)
    )
    baseline_first = calculate(reformed.baseline, year, BASELINE_OUTPUTS)
    reform_second = calculate(reformed, year, BASELINE_OUTPUTS)
    assert_identical(plain, baseline_second, f"baseline after reform: {units}")
    assert_identical(plain, baseline_first, f"baseline before reform: {units}")
    assert_identical(reform_first, reform_second, f"reform: {units}")
    # The reform reached the simulation: the transferable amount is 10% of
    # 15,000 (s. 55B(4)(b)), and 1,260 in the baseline.
    assert np.all(reform_first["marriage_allowance_transferable_amount"] == 1_500)
    assert np.all(plain["marriage_allowance_transferable_amount"] == 1_260)


def test_no_branch_is_left_after_any_year():
    # A couple who elect every year: 30,000 and 9,000 of earnings, so electing
    # costs the lower earner nothing and saves the other 252 (s. 55B). The
    # lower earner's property receipts are within the property allowance and
    # carry finance costs, so the property route is weighed in branches too.
    units = [
        dict(
            adults=[
                dict(age=40, employment_income=30_000.0),
                dict(
                    age=38,
                    employment_income=9_000.0,
                    property_rental_income=800.0,
                    property_income=800.0,
                    property_finance_costs=200.0,
                ),
            ],
            married=True,
            children=[4],
            tenure="RENT_PRIVATELY",
            rent=9_000.0,
            region="LONDON",
        )
    ]
    years = list(range(2025, 2031))
    simulation = Simulation(situation=situation(units, years))
    before = set(simulation.branches)
    elected = []
    for year in years:
        simulation.calculate("household_net_income", year)
        elected.append(bool(simulation.calculate(ELECTION, year).any()))
        assert set(simulation.branches) == before, (year, list(simulation.branches))
    assert all(elected), elected
