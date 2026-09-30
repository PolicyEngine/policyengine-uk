"""Property-based tests for who can claim Housing Benefit.

New Housing Benefit claims are barred except where the claimant, and any
partner, has reached the qualifying age for State Pension Credit (SI 2014/1230
reg 6A(4)); Universal Credit is not available to them (Welfare Reform Act 2012
s.4(1)(b)). Other families keep Housing Benefit only while they continue an
existing award and do not claim Universal Credit.

Invariants, for any generated population of families:

1. Structural: 0 <= housing_benefit <= benunit_rent; Housing Benefit never
   exceeds the LHA cap for LHA tenants; it is never paid to non-renters or
   above the capital limit; and no family gets both Housing Benefit and
   Universal Credit.
2. Calculator mode (no reported benefits): a family is eligible exactly when
   the claimant and any partner are over State Pension age, it rents, and its
   capital is within the limit; eligible families are paid their full
   entitlement (pensioners are exempt from the benefit cap).
3. Dataset mode (claims_all_entitled_benefits False, as in the FRS): Housing
   Benefit is paid only to reported claimants, and for families with a
   working-age adult eligibility equals the continuing-award rule (reported,
   not claiming Universal Credit, renting, capital within the limit).
4. Metamorphic: flipping would_claim_uc never changes a wholly pension-age
   family's Housing Benefit.
5. Metamorphic: a wholly pension-age family's Housing Benefit is
   non-increasing in private pension income.

A pensioner with an 18 or 19 year old dependant is a pension-age claimant for
Housing Benefit, Pension Credit and Universal Credit alike (the dependant is
not a claimant or partner), so that family can claim Housing Benefit and not
Universal Credit, and the mutual exclusion holds for that shape too.
"""

import numpy as np
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation

YEAR = 2026
PROPERTY_SETTINGS = settings(
    max_examples=10,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)
TENURES = [
    "RENT_FROM_COUNCIL",
    "RENT_FROM_HA",
    "RENT_PRIVATELY",
    "OWNED_OUTRIGHT",
    "OWNED_WITH_MORTGAGE",
]
# State Pension age is 66 until 2026-27 finishes phasing up; 67 and over is
# unambiguously pension age and 60 and under unambiguously working age.
PENSION_AGE = st.integers(67, 100)
WORKING_AGE = st.integers(18, 60)
SHAPES = {
    "single_pension": [("claimant", PENSION_AGE)],
    "couple_pension": [("claimant", PENSION_AGE), ("partner", PENSION_AGE)],
    "mixed_age": [("claimant", PENSION_AGE), ("partner", WORKING_AGE)],
    "single_working": [("claimant", WORKING_AGE)],
    "couple_working": [("claimant", WORKING_AGE), ("partner", WORKING_AGE)],
    "pension_with_dependant": [
        ("claimant", PENSION_AGE),
        ("dependant", st.integers(18, 19)),
    ],
}
money = st.floats(0, 20_000, allow_nan=False, allow_infinity=False)


@st.composite
def families(draw, reported_allowed):
    shape = draw(st.sampled_from(sorted(SHAPES)))
    return dict(
        shape=shape,
        members=[(role, draw(age)) for role, age in SHAPES[shape]],
        tenure=draw(st.sampled_from(TENURES)),
        rent=draw(money),
        savings=draw(st.one_of(st.just(0.0), st.floats(0, 40_000))),
        state_pension=draw(money),
        private_pension=draw(st.one_of(st.just(0.0), st.floats(0, 30_000))),
        would_claim_uc=draw(st.booleans()),
        hb_reported=draw(st.sampled_from([0.0, 1.0])) if reported_allowed else 0.0,
    )


def situation(units, claims_all=None, flip_would_claim_uc=False, pension_bump=0.0):
    people, benunits, households = {}, {}, {}
    for i, unit in enumerate(units):
        names = []
        for j, (role, age) in enumerate(unit["members"]):
            name = f"p{i}_{j}"
            person = {"age": {YEAR: age}}
            if role != "dependant" and age >= 67:
                person["state_pension_reported"] = {YEAR: unit["state_pension"]}
                person["private_pension_income"] = {
                    YEAR: unit["private_pension"] + pension_bump
                }
            if role == "claimant":
                person["is_parent"] = {YEAR: unit["shape"] == "pension_with_dependant"}
                if unit["hb_reported"]:
                    person["housing_benefit_reported"] = {YEAR: unit["hb_reported"]}
            if role == "dependant":
                person["current_education"] = {YEAR: "UPPER_SECONDARY"}
            people[name] = person
            names.append(name)
        benunit = {
            "members": names,
            "would_claim_uc": {YEAR: unit["would_claim_uc"] ^ flip_would_claim_uc},
        }
        # claims_all_entitled_benefits sums reported benefits across the whole
        # simulation, so set it per family whenever any family reports one.
        if claims_all is not None:
            benunit["claims_all_entitled_benefits"] = {YEAR: claims_all}
        benunits[f"b{i}"] = benunit
        households[f"h{i}"] = {
            "members": names,
            "rent": {YEAR: unit["rent"]},
            "tenure_type": {YEAR: unit["tenure"]},
            "savings": {YEAR: unit["savings"]},
        }
    return {"people": people, "benunits": benunits, "households": households}


VARIABLES = [
    "housing_benefit",
    "housing_benefit_eligible",
    "housing_benefit_entitlement",
    "housing_benefit_assessable_capital",
    "universal_credit",
    "benunit_rent",
    "LHA_eligible",
    "LHA_cap",
]


def calculate(units, **kwargs):
    sim = Simulation(situation=situation(units, **kwargs))
    values = {v: np.asarray(sim.calculate(v, YEAR)) for v in VARIABLES}
    values["social"] = (
        np.asarray(sim.calculate("in_social_housing", YEAR, map_to="benunit")) > 0
    )
    values["renting"] = values["social"] | values["LHA_eligible"].astype(bool)
    capital = sim.tax_benefit_system.parameters(
        YEAR
    ).gov.dwp.housing_benefit.means_test.capital
    # Both limits are 16,000; the test holds families to the lower of them.
    limit = min(capital.pension_age.limit, capital.working_age.limit)
    values["capital_ok"] = values["housing_benefit_assessable_capital"] <= limit
    return values


def wholly_pension_age(unit):
    # The claimant and any partner, not dependants (SI 2014/1230 reg 6A(4)).
    return all(age >= 67 for role, age in unit["members"] if role != "dependant")


def check_structural(values):
    hb = values["housing_benefit"]
    lha = values["LHA_eligible"].astype(bool)
    assert np.all(hb >= 0)
    assert np.all(hb <= values["benunit_rent"] + 0.01)
    assert np.all(hb[lha] <= values["LHA_cap"][lha] + 0.01)
    assert not np.any((hb > 0) & (values["universal_credit"] > 0))
    assert not np.any((hb > 0) & ~values["renting"])
    assert not np.any((hb > 0) & ~values["capital_ok"])


@PROPERTY_SETTINGS
@given(st.lists(families(reported_allowed=False), min_size=1, max_size=30))
def test_new_claims_follow_the_pension_age_route(units):
    values = calculate(units)
    check_structural(values)
    for i, unit in enumerate(units):
        expected = (
            wholly_pension_age(unit)
            and values["renting"][i]
            and values["capital_ok"][i]
        )
        assert bool(values["housing_benefit_eligible"][i]) == expected, unit
        if expected:
            assert (
                abs(
                    values["housing_benefit"][i]
                    - values["housing_benefit_entitlement"][i]
                )
                < 0.01
            ), unit


@PROPERTY_SETTINGS
@given(st.lists(families(reported_allowed=True), min_size=1, max_size=30))
def test_dataset_take_up_stays_anchored_to_reported_claims(units):
    values = calculate(units, claims_all=False)
    check_structural(values)
    for i, unit in enumerate(units):
        if values["housing_benefit"][i] > 0:
            assert unit["hb_reported"] > 0, unit
        if not wholly_pension_age(unit):
            continuing_award = (
                unit["hb_reported"] > 0
                and not unit["would_claim_uc"]
                and values["renting"][i]
                and values["capital_ok"][i]
            )
            assert bool(values["housing_benefit_eligible"][i]) == continuing_award


@PROPERTY_SETTINGS
@given(st.lists(families(reported_allowed=True), min_size=1, max_size=30))
def test_would_claim_uc_does_not_affect_pension_age_housing_benefit(units):
    before = calculate(units, claims_all=True)
    after = calculate(units, claims_all=True, flip_would_claim_uc=True)
    for i, unit in enumerate(units):
        if wholly_pension_age(unit):
            assert (
                abs(before["housing_benefit"][i] - after["housing_benefit"][i]) < 0.01
            ), unit


@PROPERTY_SETTINGS
@given(
    st.lists(families(reported_allowed=False), min_size=1, max_size=30),
    st.floats(1, 10_000, allow_nan=False, allow_infinity=False),
)
def test_pension_age_housing_benefit_is_non_increasing_in_income(units, bump):
    before = calculate(units)
    after = calculate(units, pension_bump=bump)
    for i, unit in enumerate(units):
        if wholly_pension_age(unit):
            assert after["housing_benefit"][i] <= before["housing_benefit"][i] + 0.01, (
                unit,
                bump,
            )
