"""The Marriage Allowance gives its recipient a tax reduction at Step 6.

Parliament gives the recipient a tax reduction of the appropriate percentage
of the transferable amount (ITA 2007 s. 55B(1)) at Step 6 (s. 55A(2)): the
basic rate, or for a Scottish taxpayer the Scottish basic rate (s. 55B(3)).
The reduction comes off only so far as Step 5 tax remains after the
reductions already deducted (s. 29(2) and (3)).

Invariants, for generated married couples in England, Scotland, Wales and
Northern Ireland, with pay, pensions, savings and dividends drawn freely:

1. For every person, income_tax equals the income tax with
   would_claim_marriage_allowance false, less the smaller of the appropriate
   percentage of marriage_allowance and the Step 5 tax the earlier reductions
   leave.
2. The reduction does not depend on the recipient's marginal rate: under the
   CPS expanded reform, which gives the allowance to recipients in every band,
   a recipient with enough tax gets exactly the appropriate percentage of the
   allowance, and income tax falls by that amount.
3. The election does not move the rate test:
   meets_marriage_allowance_income_conditions gives the same result with
   would_claim_marriage_allowance true and false.
4. The reduction lies between zero and the appropriate percentage of the
   allowance, and the Step 6 reductions together never exceed the Step 5 tax.
"""

import numpy as np
import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation
from policyengine_uk.reforms.cps.marriage_tax_reforms import expanded_ma_reform

pytestmark = pytest.mark.usefixtures("cloned_uk_tax_benefit_system")

TOLERANCE = 0.01
COUPLES = 8
REGIONS = ["LONDON", "SCOTLAND", "WALES", "NORTHERN_IRELAND"]
YEARS = [2016, 2017, 2018, 2021, 2025, 2026]

small = st.integers(min_value=0, max_value=20_000)
person_strategy = st.tuples(
    st.integers(min_value=0, max_value=160_000),  # employment income
    st.integers(min_value=0, max_value=30_000),  # private pension income
    small,  # savings interest
    small,  # dividends
)
couple_strategy = st.tuples(person_strategy, person_strategy, st.sampled_from(REGIONS))
couples_strategy = st.lists(couple_strategy, min_size=COUPLES, max_size=COUPLES)

VARIABLES = [
    "income_tax",
    "income_tax_pre_charges",
    "income_tax_reductions",
    "marriage_allowance",
    "marriage_allowance_tax_reduction",
    "marriage_allowance_appropriate_percentage",
    "meets_marriage_allowance_income_conditions",
]


def situation(couples, year, would_claim):
    people, benunits, households = {}, {}, {}
    for i, (first, second, region) in enumerate(couples):
        members = [f"first_{i}", f"second_{i}"]
        for name, (pay, pension, savings, dividends) in zip(members, (first, second)):
            people[name] = {
                "age": {year: 45},
                "marital_status": {year: "MARRIED"},
                "employment_income": {year: pay},
                "private_pension_income": {year: pension},
                "savings_interest_income": {year: savings},
                "dividend_income": {year: dividends},
                "would_claim_marriage_allowance": {year: would_claim},
            }
        benunits[f"benunit_{i}"] = {"members": members, "is_married": {year: True}}
        households[f"household_{i}"] = {
            "members": members,
            "region": {year: region},
        }
    return {"people": people, "benunits": benunits, "households": households}


def calculate(couples, year, would_claim, reform=None):
    simulation = Simulation(
        situation=situation(couples, year, would_claim), reform=reform
    )
    values = {name: np.asarray(simulation.calculate(name, year)) for name in VARIABLES}
    step_6 = simulation.tax_benefit_system.parameters(
        year
    ).gov.hmrc.income_tax.step_6_tax_reductions
    earlier = list(step_6)[: list(step_6).index("marriage_allowance_tax_reduction")]
    values["earlier_reductions"] = sum(
        np.asarray(simulation.calculate(name, year)) for name in earlier
    )
    values["step_6_reductions"] = sum(
        np.asarray(simulation.calculate(name, year)) for name in step_6
    )
    return values


SETTINGS = settings(
    max_examples=12,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)


@SETTINGS
@given(couples=couples_strategy, year=st.sampled_from(YEARS))
def test_reduction_takes_the_appropriate_percentage_off_step_5_tax(couples, year):
    claimed = calculate(couples, year, would_claim=True)
    unclaimed = calculate(couples, year, would_claim=False)
    rate = claimed["marriage_allowance_appropriate_percentage"]
    allowance = claimed["marriage_allowance"]
    reduction = claimed["marriage_allowance_tax_reduction"]
    tax_left = np.maximum(
        0, unclaimed["income_tax_pre_charges"] - unclaimed["earlier_reductions"]
    )
    expected = np.minimum(rate * allowance, tax_left)
    # Invariant 1.
    np.testing.assert_allclose(
        claimed["income_tax"], unclaimed["income_tax"] - expected, atol=TOLERANCE
    )
    np.testing.assert_allclose(reduction, expected, atol=TOLERANCE)
    # Invariant 3.
    np.testing.assert_array_equal(
        claimed["meets_marriage_allowance_income_conditions"],
        unclaimed["meets_marriage_allowance_income_conditions"],
    )
    # Invariant 4.
    assert (reduction >= -TOLERANCE).all()
    assert (reduction <= rate * allowance + TOLERANCE).all()
    step_5 = np.maximum(0, claimed["income_tax_pre_charges"])
    assert (claimed["step_6_reductions"] <= step_5 + TOLERANCE).all()
    assert (claimed["income_tax_reductions"] <= step_5 + TOLERANCE).all()
    # The allowance never changes the Step 5 tax.
    np.testing.assert_allclose(
        claimed["income_tax_pre_charges"],
        unclaimed["income_tax_pre_charges"],
        atol=TOLERANCE,
    )


@SETTINGS
@given(couples=couples_strategy, year=st.sampled_from([2018, 2021, 2025, 2026]))
def test_reduction_does_not_depend_on_the_marginal_rate(couples, year):
    # Invariant 2. The CPS expanded reform, with no child condition, gives the
    # allowance to married recipients in every band.
    claimed = calculate(couples, year, would_claim=True, reform=expanded_ma_reform)
    unclaimed = calculate(couples, year, would_claim=False, reform=expanded_ma_reform)
    rate = claimed["marriage_allowance_appropriate_percentage"]
    allowance = claimed["marriage_allowance"]
    full = rate * allowance
    enough_tax = (
        unclaimed["income_tax_pre_charges"] - unclaimed["earlier_reductions"]
        >= full + TOLERANCE
    )
    np.testing.assert_allclose(
        claimed["marriage_allowance_tax_reduction"][enough_tax],
        full[enough_tax],
        atol=TOLERANCE,
    )
    np.testing.assert_allclose(
        unclaimed["income_tax"][enough_tax] - claimed["income_tax"][enough_tax],
        full[enough_tax],
        atol=TOLERANCE,
    )
    # The appropriate percentage is the basic rate or the Scottish basic rate,
    # 20% in each of these years, whatever the recipient's income.
    np.testing.assert_allclose(rate, 0.2)


def test_higher_rate_recipients_under_the_expanded_reform_get_20_percent():
    # 2025-26, England: pay of 60,000 and 150,000 put the recipients in the
    # higher and additional rate bands. The CPS expanded reform gives each the
    # 1,260 allowance, and the reduction is 20% x 1,260 = 252, not 40% or 45%
    # of it.
    couples = [
        ((60_000, 0, 0, 0), (0, 0, 0, 0), "LONDON"),
        ((150_000, 0, 0, 0), (0, 0, 0, 0), "LONDON"),
        ((60_000, 0, 0, 0), (0, 0, 0, 0), "SCOTLAND"),
    ]
    claimed = calculate(couples, 2025, would_claim=True, reform=expanded_ma_reform)
    unclaimed = calculate(couples, 2025, would_claim=False, reform=expanded_ma_reform)
    np.testing.assert_allclose(
        claimed["marriage_allowance"], [1_260, 0, 1_260, 0, 1_260, 0]
    )
    np.testing.assert_allclose(
        unclaimed["income_tax"] - claimed["income_tax"],
        [252, 0, 252, 0, 252, 0],
        atol=TOLERANCE,
    )
