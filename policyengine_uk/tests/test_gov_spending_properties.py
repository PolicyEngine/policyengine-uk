"""Property-based tests that government spending counts household benefits.

gov_spending adds every entry of GOV_SPENDING_VARIABLES and gov_balance is
gov_tax less gov_spending. household_benefits adds every entry of
HOUSEHOLD_BENEFIT_VARIABLES to household net income. The Scottish Child
Payment, Healthy Start vouchers and the Two Child Limit Payment were in the
second list but not the first, so households received them at no cost to the
government and gov_balance was overstated by the amount paid.

Invariants, for any generated population of households:

1. Sum identity: gov_spending equals the sum, over the distinct names in
   GOV_SPENDING_VARIABLES, of each variable summed to the household.
2. Balance identity: gov_balance equals gov_tax less gov_spending.
3. Conservation: what households receive in benefits, less any benefit that
   government does not pay (NOT_PAID_BY_GOVERNMENT), equals gov_spending less
   the spending that is not a household benefit. So a pound of benefit from
   government is a pound of government spending.
4. Metamorphic: paying a household d more of the Scottish Child Payment,
   Healthy Start vouchers or the Two Child Limit Payment raises
   household_benefits and gov_spending by d each, lowers gov_balance by d and
   leaves gov_tax unchanged.

Invariants 3 and 4 fail on the earlier list whenever a household receives one
of the three payments.

The three payments are entered directly for every member, so the properties
test the lists and not the payments' own eligibility rules.
"""

import numpy as np
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation
from policyengine_uk.tests.code_health.test_household_benefits_in_government_spending import (
    NOT_PAID_BY_GOVERNMENT,
)
from policyengine_uk.variables.gov.gov_spending import GOV_SPENDING_VARIABLES
from policyengine_uk.variables.household.income.household_benefits import (
    HOUSEHOLD_BENEFIT_VARIABLES,
)

YEAR = 2026
PROPERTY_SETTINGS = settings(
    max_examples=10,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)
SPENDING = list(dict.fromkeys(GOV_SPENDING_VARIABLES))
BENEFITS = list(dict.fromkeys(HOUSEHOLD_BENEFIT_VARIABLES))
# Spending that is not a benefit a household receives.
NOT_HOUSEHOLD_BENEFITS = [name for name in SPENDING if name not in BENEFITS]
# The payments that were missing from government spending, with the entity
# each is paid to.
PAYMENTS = {
    "scottish_child_payment": "child",
    "healthy_start_vouchers": "child",
    "two_child_limit_payment": "benunit",
}
REGIONS = ["SCOTLAND", "NORTH_EAST", "LONDON", "WALES", "NORTHERN_IRELAND"]
TENURES = ["RENT_FROM_COUNCIL", "RENT_PRIVATELY", "OWNED_OUTRIGHT"]
# Float32 household totals of tens of thousands of pounds are exact to about
# a penny.
TOLERANCE = 0.05

money = st.floats(0, 60_000, allow_nan=False, allow_infinity=False)
payment = st.one_of(st.just(0.0), st.floats(1, 4_000, allow_nan=False))


@st.composite
def households(draw):
    return dict(
        adults=[
            dict(
                age=draw(st.integers(18, 80)),
                employment_income=draw(st.one_of(st.just(0.0), money)),
            )
            for _ in range(draw(st.integers(1, 2)))
        ],
        children=[
            dict(
                age=draw(st.integers(0, 15)),
                scottish_child_payment=draw(payment),
                healthy_start_vouchers=draw(payment),
            )
            for _ in range(draw(st.integers(0, 3)))
        ],
        two_child_limit_payment=draw(payment),
        would_claim_uc=draw(st.booleans()),
        region=draw(st.sampled_from(REGIONS)),
        tenure=draw(st.sampled_from(TENURES)),
        rent=draw(st.floats(0, 15_000, allow_nan=False)),
    )


def situation(units, bumped=None, bump=0.0, start=0):
    """The households, paying `bump` more of the `bumped` payment.

    A child payment rises for every child; the benefit unit payment rises
    once. Households are numbered from `start`.
    """
    people, benunits, homes = {}, {}, {}
    for i, unit in enumerate(units, start):
        names = []
        for j, adult in enumerate(unit["adults"]):
            name = f"a{i}_{j}"
            people[name] = {
                "age": {YEAR: adult["age"]},
                "employment_income": {YEAR: adult["employment_income"]},
                "scottish_child_payment": {YEAR: 0.0},
                "healthy_start_vouchers": {YEAR: 0.0},
            }
            names.append(name)
        for j, child in enumerate(unit["children"]):
            name = f"c{i}_{j}"
            people[name] = {
                "age": {YEAR: child["age"]},
                "employment_income": {YEAR: 0.0},
            }
            for paid in ["scottish_child_payment", "healthy_start_vouchers"]:
                people[name][paid] = {
                    YEAR: child[paid] + (bump if paid == bumped else 0.0)
                }
            names.append(name)
        benunits[f"b{i}"] = {
            "members": names,
            "would_claim_uc": {YEAR: unit["would_claim_uc"]},
            "two_child_limit_payment": {
                YEAR: unit["two_child_limit_payment"]
                + (bump if bumped == "two_child_limit_payment" else 0.0)
            },
        }
        homes[f"h{i}"] = {
            "members": names,
            "region": {YEAR: unit["region"]},
            "tenure_type": {YEAR: unit["tenure"]},
            "rent": {YEAR: unit["rent"]},
        }
    return {"people": people, "benunits": benunits, "households": homes}


def calc(sim, name):
    return np.asarray(sim.calculate(name, YEAR, map_to="household"), dtype=float)


def household_sum(sim, names):
    return sum((calc(sim, name) for name in names), np.zeros(1))


@PROPERTY_SETTINGS
@given(st.lists(households(), min_size=1, max_size=12))
def test_government_spending_counts_every_benefit_government_pays(units):
    sim = Simulation(situation=situation(units))
    spending = calc(sim, "gov_spending")
    # Invariant 1.
    np.testing.assert_allclose(
        spending, household_sum(sim, SPENDING), atol=TOLERANCE, rtol=1e-6
    )
    # Invariant 2.
    np.testing.assert_allclose(
        calc(sim, "gov_balance"),
        calc(sim, "gov_tax") - spending,
        atol=TOLERANCE,
        rtol=1e-6,
    )
    # Invariant 3.
    np.testing.assert_allclose(
        calc(sim, "household_benefits")
        - household_sum(sim, list(NOT_PAID_BY_GOVERNMENT)),
        spending - household_sum(sim, NOT_HOUSEHOLD_BENEFITS),
        atol=TOLERANCE,
        rtol=1e-6,
    )
    # The payments under test are in the population, so invariant 3 can fail.
    entered = sum(
        child[name]
        for unit in units
        for child in unit["children"]
        for name in ["scottish_child_payment", "healthy_start_vouchers"]
    ) + sum(unit["two_child_limit_payment"] for unit in units)
    np.testing.assert_allclose(
        household_sum(sim, list(PAYMENTS)).sum(), entered, rtol=1e-5, atol=TOLERANCE
    )


@PROPERTY_SETTINGS
@given(
    st.lists(households(), min_size=1, max_size=12),
    st.sampled_from(list(PAYMENTS)),
    st.floats(1, 3_000, allow_nan=False),
)
def test_a_pound_more_of_a_payment_is_a_pound_of_government_spending(
    units, bumped, bump
):
    # One simulation holds every household twice: as drawn, then with the
    # extra payment.
    as_drawn = situation(units)
    with_bump = situation(units, bumped=bumped, bump=bump, start=len(units))
    sim = Simulation(
        situation={
            entity: {**as_drawn[entity], **with_bump[entity]} for entity in as_drawn
        }
    )
    recipients = np.array(
        [len(unit["children"]) if PAYMENTS[bumped] == "child" else 1 for unit in units]
    )
    paid = recipients * bump

    def change(name):
        values = calc(sim, name)
        return values[len(units) :] - values[: len(units)]

    np.testing.assert_allclose(change(bumped), paid, rtol=1e-5, atol=TOLERANCE)
    np.testing.assert_allclose(
        change("household_benefits"), paid, rtol=1e-5, atol=TOLERANCE
    )
    np.testing.assert_allclose(change("gov_spending"), paid, rtol=1e-5, atol=TOLERANCE)
    np.testing.assert_allclose(change("gov_tax"), 0, atol=TOLERANCE)
    np.testing.assert_allclose(change("gov_balance"), -paid, rtol=1e-5, atol=TOLERANCE)
