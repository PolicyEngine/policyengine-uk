"""Exhaustive tests of the houseboat, caravan and mobile home LHA exclusion.

A local authority determines no maximum rent (LHA) where a Housing Benefit
claim relates to rent for "a houseboat, caravan or mobile home which he
occupies as his home" (SI 2006/213 and SI 2006/214 reg 13C(5)(d)(i); Northern
Ireland: SR 2006/405 and SR 2006/406 reg 14C(5)(d)(i)). Housing Benefit can
still meet those payments (reg 12(1); NI reg 13(1)), so the family stays
eligible where it rents. The DWP makes no such exception in Universal Credit
(SI 2013/376 Sch 4 Part 4), where qualifying private-sector rent payments
stay subject to the LHA cap.

The grid crosses five families, five tenures, five regions, two rents and two
incomes: 500 families, none of whose rent includes meals. One simulation
holds each family three times: in a caravan, in one other known type of home
(the grid cycles through the six by index), and in a home of unknown type.

Invariants, for every family in the grid:

1. Definition: LHA_eligible holds exactly for a private renter whose home is
   not a houseboat, caravan or mobile home. The expectation comes from the
   tenure and accommodation the grid sets, not from the model.
2. Eligibility: a family is eligible for Housing Benefit exactly when it
   rents and has either reached pension age or kept an existing award,
   whatever its home. So moving a family between a caravan and any other home
   never changes its eligibility.
3. Entitlement: moving a family from a caravan to another home never raises
   its Housing Benefit entitlement, a caravan family's entitlement never
   exceeds its rent, and where the LHA applies in neither home the two
   entitlements match. This holds because no rent in the grid includes meals:
   a local authority deducts a charge for meals from a caravan renter's
   eligible rent, and not from a maximum rent (LHA).
4. Universal Credit: the home never changes the housing element.
5. Other homes: among homes other than a houseboat, caravan or mobile home,
   the type changes none of the variables the test computes.

A fixed example then shows the LHA at work: freezing LHA rates lowers the
entitlement of a pensioner in a flat and leaves the same pensioner's
entitlement in a caravan at the rent.
"""

from itertools import product

import numpy as np

from policyengine_uk import Simulation
from policyengine_uk.variables.household.demographic.accommodation_type import (
    AccommodationType,
)

YEAR = 2025
FREEZE_YEAR = 2026
# Each family: its members' ages, and whether it reports a Housing Benefit
# award and doesn't claim Universal Credit (the continuing-award route).
FAMILIES = {
    "pensioner": ([70], False),
    "pensioner couple": ([70, 72], False),
    "working-age adult": ([40], False),
    "working-age adult with an award": ([40], True),
    "working-age couple with an award": ([40, 38], True),
}
TENURES = [
    "RENT_FROM_COUNCIL",
    "RENT_FROM_HA",
    "RENT_PRIVATELY",
    "OWNED_OUTRIGHT",
    "OWNED_WITH_MORTGAGE",
]
REGIONS = ["LONDON", "NORTH_EAST", "WALES", "SCOTLAND", "NORTHERN_IRELAND"]
# Below and above every one-bedroom LHA rate in these regions.
RENTS = [3_000, 30_000]
INCOMES = [0, 15_000]
OTHER_KNOWN = [
    value.name for value in AccommodationType if value.name not in ("MOBILE", "UNKNOWN")
]
GRID = [
    dict(family=family, tenure=tenure, region=region, rent=rent, income=income)
    for family, tenure, region, rent, income in product(
        FAMILIES, TENURES, REGIONS, RENTS, INCOMES
    )
]
VARIABLES = [
    "LHA_eligible",
    "LHA_cap",
    "benunit_rent",
    "benunit_is_renting",
    "housing_benefit_eligible",
    "housing_benefit_entitlement",
    "uc_housing_costs_element",
]


def add_household(situation, name, unit, accommodation, year):
    ages, has_award = FAMILIES[unit["family"]]
    members = []
    for j, age in enumerate(ages):
        person = {"age": {year: age}}
        if j == 0:
            source = "private_pension_income" if age >= 67 else "employment_income"
            person[source] = {year: unit["income"]}
            if has_award:
                person["housing_benefit_reported"] = {year: 5_000}
        member = f"{name}_{j}"
        situation["people"][member] = person
        members.append(member)
    benunit = {"members": members}
    if has_award:
        benunit["would_claim_uc"] = {year: False}
    situation["benunits"][name] = benunit
    situation["households"][name] = {
        "members": members,
        "rent": {year: unit["rent"]},
        "tenure_type": {year: unit["tenure"]},
        "region": {year: unit["region"]},
        "accommodation_type": {year: accommodation},
    }


def calculate(homes, year=YEAR, reform=None):
    """Compute VARIABLES for (name, unit, accommodation) homes, in order."""
    situation = {"people": {}, "benunits": {}, "households": {}}
    for name, unit, accommodation in homes:
        add_household(situation, name, unit, accommodation, year)
    sim = Simulation(situation=situation, reform=reform)
    return {v: np.asarray(sim.calculate(v, year)) for v in VARIABLES}


def test_accommodation_type_invariants():
    size = len(GRID)
    homes = (
        [(f"mobile{i}", unit, "MOBILE") for i, unit in enumerate(GRID)]
        + [
            (f"other{i}", unit, OTHER_KNOWN[i % len(OTHER_KNOWN)])
            for i, unit in enumerate(GRID)
        ]
        + [(f"unknown{i}", unit, "UNKNOWN") for i, unit in enumerate(GRID)]
    )
    values = calculate(homes)
    mobile = {v: values[v][:size] for v in VARIABLES}
    other = {v: values[v][size : 2 * size] for v in VARIABLES}
    unknown = {v: values[v][2 * size :] for v in VARIABLES}

    private = np.array([unit["tenure"] == "RENT_PRIVATELY" for unit in GRID])
    renting = np.array([unit["tenure"].startswith("RENT_") for unit in GRID])
    pension_age = np.array([unit["family"].startswith("pensioner") for unit in GRID])
    has_award = np.array([FAMILIES[unit["family"]][1] for unit in GRID])

    # 1. Definition.
    assert not mobile["LHA_eligible"].any()
    assert (other["LHA_eligible"] == private).all()
    assert (unknown["LHA_eligible"] == private).all()

    # 2. Eligibility ignores the home.
    eligible = renting & (pension_age | has_award)
    for home in (mobile, other, unknown):
        assert (home["housing_benefit_eligible"] == eligible).all()
    # The grid holds eligible caravan renters of both kinds.
    assert (eligible & private & pension_age).any()
    assert (eligible & private & has_award).any()

    # 3. The LHA only lowers the entitlement, and a caravan family's
    # entitlement never exceeds its rent.
    entitlement = mobile["housing_benefit_entitlement"]
    assert np.all(entitlement <= mobile["benunit_rent"] + 0.01)
    assert np.all(other["housing_benefit_entitlement"] <= entitlement + 0.01)
    # Where the LHA applies in neither home, nothing changes.
    assert np.allclose(
        other["housing_benefit_entitlement"][~private], entitlement[~private], atol=0.01
    )
    # The LHA cuts the entitlement of some private renters in other homes.
    assert (other["housing_benefit_entitlement"][private] < entitlement[private]).any()

    # 4. Universal Credit ignores the home.
    for home in (other, unknown):
        assert np.allclose(
            mobile["uc_housing_costs_element"],
            home["uc_housing_costs_element"],
            atol=0.01,
        )

    # 5. Other homes change nothing.
    for variable in VARIABLES:
        assert np.allclose(other[variable], unknown[variable], atol=0.01), variable


def test_lha_freeze_moves_a_flat_renter_but_not_a_caravan_renter():
    """A pensioner with no income renting privately in London for 30,000."""
    unit = dict(
        family="pensioner",
        tenure="RENT_PRIVATELY",
        region="LONDON",
        rent=30_000,
        income=0,
    )
    homes = [("flat", unit, "FLAT"), ("caravan", unit, "MOBILE")]
    frozen, unfrozen = (
        calculate(
            homes,
            year=FREEZE_YEAR,
            reform={"gov.dwp.LHA.freeze": {str(FREEZE_YEAR): freeze}},
        )["housing_benefit_entitlement"]
        for freeze in (True, False)
    )
    flat, caravan = 0, 1
    assert frozen[flat] < unfrozen[flat] < 30_000
    assert frozen[caravan] == unfrozen[caravan] == 30_000
