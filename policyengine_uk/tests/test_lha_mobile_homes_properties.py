"""Property-based tests for the houseboat, caravan and mobile home LHA exclusion.

No maximum rent (LHA) is determined where a Housing Benefit claim relates to
rent for "a houseboat, caravan or mobile home which he occupies as his home"
(SI 2006/213 and SI 2006/214 reg 13C(5)(d)(i)). Those payments are still rent
(reg 12(1)), so the family can still get Housing Benefit. Universal Credit has
no such exception (SI 2013/376 Sch 4 Part 4), so its housing element keeps the
LHA.

Invariants, for any generated population of families:

1. Definition: LHA_eligible is exactly renting, no member in social housing,
   and accommodation other than a houseboat, caravan or mobile home.
2. Metamorphic: moving a family between a caravan and any other accommodation
   type never changes whether it is eligible for Housing Benefit.
3. Metamorphic: moving a family from a caravan to other accommodation never
   raises its Housing Benefit entitlement, and a caravan family's entitlement
   never exceeds its rent.
4. Metamorphic: freezing the LHA never changes a caravan family's Housing
   Benefit entitlement.
5. Metamorphic: accommodation type never changes the Universal Credit housing
   element.
"""

import numpy as np
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation
from policyengine_uk.variables.household.demographic.accommodation_type import (
    AccommodationType,
)

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
ACCOMMODATION = [value.name for value in AccommodationType]
NOT_MOBILE = [name for name in ACCOMMODATION if name != "MOBILE"]
REGIONS = ["LONDON", "NORTH_EAST", "SOUTH_EAST", "WALES", "SCOTLAND"]
money = st.floats(0, 30_000, allow_nan=False, allow_infinity=False)


@st.composite
def families(draw):
    return dict(
        # 67 and over is unambiguously pension age, 60 and under working age.
        ages=draw(
            st.sampled_from(
                [
                    [draw(st.integers(67, 100))],
                    [draw(st.integers(67, 100)), draw(st.integers(67, 100))],
                    [draw(st.integers(18, 60))],
                    [draw(st.integers(18, 60)), draw(st.integers(18, 60))],
                ]
            )
        ),
        tenure=draw(st.sampled_from(TENURES)),
        accommodation=draw(st.sampled_from(ACCOMMODATION)),
        other_accommodation=draw(st.sampled_from(NOT_MOBILE)),
        region=draw(st.sampled_from(REGIONS)),
        rent=draw(money),
        pension=draw(st.one_of(st.just(0.0), money)),
        earnings=draw(st.one_of(st.just(0.0), money)),
    )


def situation(units, accommodation=None):
    people, benunits, households = {}, {}, {}
    for i, unit in enumerate(units):
        names = []
        for j, age in enumerate(unit["ages"]):
            name = f"p{i}_{j}"
            person = {"age": {YEAR: age}}
            if age >= 67:
                person["private_pension_income"] = {YEAR: unit["pension"]}
            else:
                person["employment_income"] = {YEAR: unit["earnings"]}
            people[name] = person
            names.append(name)
        benunits[f"b{i}"] = {"members": names}
        households[f"h{i}"] = {
            "members": names,
            "rent": {YEAR: unit["rent"]},
            "tenure_type": {YEAR: unit["tenure"]},
            "region": {YEAR: unit["region"]},
            "accommodation_type": {
                YEAR: (
                    accommodation(unit)
                    if accommodation is not None
                    else unit["accommodation"]
                )
            },
        }
    return {"people": people, "benunits": benunits, "households": households}


VARIABLES = [
    "LHA_eligible",
    "LHA_cap",
    "benunit_rent",
    "benunit_is_renting",
    "housing_benefit_eligible",
    "housing_benefit_entitlement",
    "uc_housing_costs_element",
]


def calculate(units, accommodation=None, reform=None):
    sim = Simulation(situation=situation(units, accommodation), reform=reform)
    values = {v: np.asarray(sim.calculate(v, YEAR)) for v in VARIABLES}
    values["social"] = (
        np.asarray(sim.calculate("in_social_housing", YEAR, map_to="benunit")) > 0
    )
    return values


def as_mobile(unit):
    return "MOBILE"


def as_other(unit):
    return unit["other_accommodation"]


unit_lists = st.lists(families(), min_size=1, max_size=30)


@PROPERTY_SETTINGS
@given(unit_lists)
def test_lha_eligible_excludes_houseboats_caravans_and_mobile_homes(units):
    values = calculate(units)
    mobile = np.array([unit["accommodation"] == "MOBILE" for unit in units])
    expected = values["benunit_is_renting"] & ~values["social"] & ~mobile
    assert (values["LHA_eligible"] == expected).all(), units


@PROPERTY_SETTINGS
@given(unit_lists)
def test_accommodation_type_never_changes_housing_benefit_eligibility(units):
    mobile = calculate(units, as_mobile)
    other = calculate(units, as_other)
    assert not mobile["LHA_eligible"].any()
    assert (
        mobile["housing_benefit_eligible"] == other["housing_benefit_eligible"]
    ).all(), units


@PROPERTY_SETTINGS
@given(unit_lists)
def test_lha_only_lowers_housing_benefit_entitlement(units):
    mobile = calculate(units, as_mobile)
    other = calculate(units, as_other)
    entitlement = mobile["housing_benefit_entitlement"]
    assert np.all(entitlement <= mobile["benunit_rent"] + 0.01), units
    assert np.all(other["housing_benefit_entitlement"] <= entitlement + 0.01), units
    # Where the LHA does not apply in either case, nothing else changes.
    same = ~other["LHA_eligible"]
    assert np.allclose(
        other["housing_benefit_entitlement"][same], entitlement[same], atol=0.01
    ), units


@PROPERTY_SETTINGS
@given(unit_lists)
def test_lha_freeze_never_changes_caravan_housing_benefit(units):
    frozen = calculate(units, as_mobile, reform={"gov.dwp.LHA.freeze": {"2026": True}})
    unfrozen = calculate(
        units, as_mobile, reform={"gov.dwp.LHA.freeze": {"2026": False}}
    )
    assert np.allclose(
        frozen["housing_benefit_entitlement"],
        unfrozen["housing_benefit_entitlement"],
        atol=0.01,
    ), units


@PROPERTY_SETTINGS
@given(unit_lists)
def test_accommodation_type_never_changes_universal_credit_housing(units):
    mobile = calculate(units, as_mobile)
    other = calculate(units, as_other)
    assert np.allclose(
        mobile["uc_housing_costs_element"],
        other["uc_housing_costs_element"],
        atol=0.01,
    ), units
