"""Property-based tests that household_benefits counts each benefit once.

household_benefits adds every entry of HOUSEHOLD_BENEFIT_VARIABLES, and it
listed "jsa_contrib" twice, so contributory JSA was counted twice in
household_benefits and in the income measures built on it.

Invariants, for any generated population of households:

1. Sum identity: household_benefits equals the sum, over the distinct names in
   HOUSEHOLD_BENEFIT_VARIABLES, of each benefit summed to the household.
2. Uprating identity: with gov.contrib.benefit_uprating.all = a and
   .non_sp = b, household_benefits equals S + a * S_general + b * S_non_sp,
   where S sums the distinct benefits, S_general leaves out basic income and
   S_non_sp also leaves out the State Pension.
3. Chain: household_gross_income = household_market_income + household_benefits,
   and household_net_income = household_market_income + household_benefits
   - household_tax - pension_contributions.
4. Metamorphic: for childless working-age households that do not claim
   Universal Credit, raising each adult's contributory JSA by d leaves every
   other benefit in the list unchanged and raises household_benefits by d per
   adult, not 2d. (With children, the extra income can legitimately reduce
   means-tested support such as the targeted childcare entitlement, so the
   metamorphic case excludes them; invariant 1 covers those households.)

Invariants 1, 2 and 4 fail on the duplicated list whenever a household
receives contributory JSA.
"""

import numpy as np
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation
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
BENEFITS = list(dict.fromkeys(HOUSEHOLD_BENEFIT_VARIABLES))
GENERAL = [name for name in BENEFITS if name != "basic_income"]
NON_SP = [name for name in GENERAL if name != "state_pension"]
TENURES = ["RENT_FROM_COUNCIL", "RENT_PRIVATELY", "OWNED_OUTRIGHT"]

money = st.floats(0, 60_000, allow_nan=False, allow_infinity=False)
jsa = st.one_of(st.just(0.0), st.floats(1, 6_000, allow_nan=False))


@st.composite
def households(draw, working_age_only=False):
    adult_age = st.integers(18, 60) if working_age_only else st.integers(18, 90)
    return dict(
        adults=[
            dict(
                age=draw(adult_age),
                employment_income=draw(st.one_of(st.just(0.0), money)),
                jsa_contrib_reported=draw(jsa),
                esa_contrib_reported=draw(
                    st.one_of(st.just(0.0), st.floats(1, 6_000, allow_nan=False))
                ),
            )
            for _ in range(draw(st.integers(1, 2)))
        ],
        children=[]
        if working_age_only
        else draw(st.lists(st.integers(0, 17), max_size=3)),
        would_claim_uc=False if working_age_only else draw(st.booleans()),
        tenure=draw(st.sampled_from(TENURES)),
        rent=draw(st.floats(0, 15_000, allow_nan=False)),
    )


def situation(units, jsa_bump=0.0):
    people, benunits, homes = {}, {}, {}
    for i, unit in enumerate(units):
        names = []
        for j, adult in enumerate(unit["adults"]):
            name = f"a{i}_{j}"
            people[name] = {
                "age": {YEAR: adult["age"]},
                "employment_income": {YEAR: adult["employment_income"]},
                "jsa_contrib_reported": {
                    YEAR: adult["jsa_contrib_reported"] + jsa_bump
                },
                "esa_contrib_reported": {YEAR: adult["esa_contrib_reported"]},
            }
            names.append(name)
        for j, age in enumerate(unit["children"]):
            name = f"c{i}_{j}"
            people[name] = {"age": {YEAR: age}}
            names.append(name)
        benunits[f"b{i}"] = {
            "members": names,
            "would_claim_uc": {YEAR: unit["would_claim_uc"]},
        }
        homes[f"h{i}"] = {
            "members": names,
            "tenure_type": {YEAR: unit["tenure"]},
            "rent": {YEAR: unit["rent"]},
        }
    return {"people": people, "benunits": benunits, "households": homes}


def household_sum(sim, names):
    return sum(
        np.asarray(sim.calculate(name, YEAR, map_to="household")) for name in names
    )


def calc(sim, name):
    return np.asarray(sim.calculate(name, YEAR, map_to="household"))


@PROPERTY_SETTINGS
@given(st.lists(households(), min_size=1, max_size=12))
def test_household_benefits_sums_each_benefit_once(units):
    sim = Simulation(situation=situation(units))
    np.testing.assert_allclose(
        calc(sim, "household_benefits"), household_sum(sim, BENEFITS), atol=0.01
    )
    market = calc(sim, "household_market_income")
    benefits = calc(sim, "household_benefits")
    np.testing.assert_allclose(
        calc(sim, "household_gross_income"), market + benefits, atol=0.01
    )
    np.testing.assert_allclose(
        calc(sim, "household_net_income"),
        market
        + benefits
        - calc(sim, "household_tax")
        - calc(sim, "pension_contributions"),
        atol=0.01,
    )


@PROPERTY_SETTINGS
@given(
    st.lists(households(), min_size=1, max_size=12),
    st.floats(-0.5, 0.5, allow_nan=False),
    st.floats(-0.5, 0.5, allow_nan=False),
)
def test_benefit_uprating_applies_to_each_benefit_once(
    units, uprate_all, uprate_non_sp
):
    sim = Simulation(
        situation=situation(units),
        reform={
            "gov.contrib.benefit_uprating.all": uprate_all,
            "gov.contrib.benefit_uprating.non_sp": uprate_non_sp,
        },
    )
    expected = (
        household_sum(sim, BENEFITS)
        + uprate_all * household_sum(sim, GENERAL)
        + uprate_non_sp * household_sum(sim, NON_SP)
    )
    np.testing.assert_allclose(calc(sim, "household_benefits"), expected, atol=0.01)


@PROPERTY_SETTINGS
@given(
    st.lists(households(working_age_only=True), min_size=1, max_size=12),
    st.floats(1, 5_000, allow_nan=False),
)
def test_contributory_jsa_raises_household_benefits_one_for_one(units, bump):
    before = Simulation(situation=situation(units))
    after = Simulation(situation=situation(units, jsa_bump=bump))
    adults = np.array([len(unit["adults"]) for unit in units])
    # Nothing else in household_benefits responds for these households, so
    # the change is exactly the extra JSA.
    np.testing.assert_allclose(
        household_sum(after, [name for name in BENEFITS if name != "jsa_contrib"]),
        household_sum(before, [name for name in BENEFITS if name != "jsa_contrib"]),
        atol=0.01,
    )
    np.testing.assert_allclose(
        calc(after, "household_benefits") - calc(before, "household_benefits"),
        adults * bump,
        rtol=1e-6,
        atol=0.01,
    )
