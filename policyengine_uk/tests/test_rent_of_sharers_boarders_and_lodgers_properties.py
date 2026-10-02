"""Property-based tests for the rent, tenure and housing support of families
other than the household head's: sharers of the rent, boarders and lodgers.

Invariants, for any generated population of households:

1. Conservation: the families' shares of the household's rent sum to one
   wherever anyone is liable for it, and the families' rents sum to the
   household's rent plus what boarders and lodgers pay the householder.
2. Bounds: each share is in [0, 1]; each family's rent is non-negative; a
   family that is neither the household head's, nor a sharer, nor a boarder
   or lodger has no rent.
3. Tenure: a boarder's or lodger's family rents privately, is never in social
   housing, and is LHA-eligible.
4. Non-dependants: a family liable for rent is never a non-dependant; only
   the household head's family has Universal Credit non-dependant
   deductions; a boarder's or lodger's family has no Housing Benefit or
   Council Tax Reduction non-dependant deductions.
5. Category: the Universal Credit LHA category does not depend on the
   household input is_shared_accommodation; the Housing Benefit category is
   the shared rate for any family entitled to one bedroom that lacks
   exclusive use and has no severe disability premium.
6. Meals: the Housing Benefit meals deduction is non-negative, and adding
   meals never raises the Housing Benefit eligible rent (LHA_cap).
7. Council tax: in a household whose rent is shared, the jointly liable
   claim shares never exceed one in total.
8. Monotonicity: a family's rent is non-decreasing in the household's rent.
9. No-op: in a household with no sharers, boarders or lodgers, the household
   head's family has the whole rent and everyone else none, as before, and
   the head's Universal Credit non-dependant deductions equal the previous
   formula (every other family's deductions).
"""

import numpy as np
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation

YEAR = 2025
PROPERTY_SETTINGS = settings(
    max_examples=8,
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
ROLES = ["sharer", "boarder", "lodger", "non_dependant"]
MEALS = ["NONE", "BREAKFAST_ONLY", "FEWER_THAN_THREE_A_DAY", "AT_LEAST_THREE_A_DAY"]
money = st.floats(0, 30_000, allow_nan=False, allow_infinity=False)


@st.composite
def other_family(draw):
    return dict(
        role=draw(st.sampled_from(ROLES)),
        ages=draw(st.lists(st.integers(18, 85), min_size=1, max_size=2)),
        child_age=draw(st.one_of(st.none(), st.integers(0, 15))),
        payment=draw(st.floats(1, 15_000, allow_nan=False)),
        meals=draw(st.sampled_from(MEALS)),
        sdp=draw(st.booleans()),
    )


@st.composite
def households(draw):
    return dict(
        head_ages=draw(st.lists(st.integers(18, 85), min_size=1, max_size=2)),
        head_child_age=draw(st.one_of(st.none(), st.integers(0, 15))),
        tenure=draw(st.sampled_from(TENURES)),
        rent=draw(money),
        council_tax=draw(st.floats(0, 3_000, allow_nan=False)),
        others=draw(st.lists(other_family(), min_size=0, max_size=3)),
        shared=draw(st.booleans()),
    )


population = st.lists(households(), min_size=1, max_size=6)


def build(population, shared_override=None, meals_override=None, rent_bump=0.0):
    """One situation for the whole population; returns it and family roles."""
    people, benunits, homes, roles = {}, {}, {}, []
    for h, house in enumerate(population):
        members = []

        def add_family(name, ages, child_age, role, extra):
            ids = []
            for i, age in enumerate(ages):
                pid = f"{name}_adult_{i}"
                people[pid] = {"age": age, "is_claimant_or_partner": True}
                ids.append(pid)
            if child_age is not None:
                pid = f"{name}_child"
                people[pid] = {"age": child_age, "is_claimant_or_partner": False}
                ids.append(pid)
            benunits[name] = {"members": ids, **extra}
            members.extend(ids)
            roles.append(role)
            return ids

        head_ids = add_family(
            f"h{h}_head", house["head_ages"], house["head_child_age"], "head", {}
        )
        for pid in head_ids:
            people[pid]["is_household_head"] = False
        people[head_ids[0]]["is_household_head"] = True
        for f, other in enumerate(house["others"]):
            name = f"h{h}_f{f}"
            extra = {
                "liable_for_share_of_household_rent": other["role"] == "sharer",
                "meals_included_in_rent": (
                    meals_override or other["meals"]
                    if other["role"] == "boarder"
                    else "NONE"
                ),
            }
            if other["sdp"]:
                extra["severe_disability_premium"] = 3_000
            ids = add_family(
                name, other["ages"], other["child_age"], other["role"], extra
            )
            for pid in ids:
                people[pid]["is_household_head"] = False
            if other["role"] in ("boarder", "lodger"):
                variable = f"rent_paid_as_{other['role']}"
                people[ids[0]][variable] = other["payment"]
        homes[f"h{h}"] = {
            "members": members,
            "tenure_type": house["tenure"],
            "rent": house["rent"] + rent_bump,
            "council_tax": house["council_tax"],
            "is_shared_accommodation": (
                house["shared"] if shared_override is None else shared_override
            ),
            "brma": "MAIDSTONE",
        }
    situation = {"people": people, "benunits": benunits, "households": homes}
    return situation, np.array(roles)


def calc(simulation, variable, map_to=None):
    """Values as a plain array (enumerations come back decoded)."""
    result = simulation.calculate(variable, YEAR, map_to=map_to)
    return np.asarray(result)


@PROPERTY_SETTINGS
@given(population)
def test_conservation_bounds_and_tenure(population):
    situation, roles = build(population)
    sim = Simulation(situation=situation)
    share = calc(sim, "share_of_household_rent")
    rent = calc(sim, "benunit_rent")
    household_rent = calc(sim, "rent")
    paid = calc(sim, "rent_paid_as_boarder", "household") + calc(
        sim, "rent_paid_as_lodger", "household"
    )
    # 1. Conservation.
    share_total = sim.map_result(share, "benunit", "household")
    assert np.allclose(share_total, 1, atol=1e-6)
    rent_total = sim.map_result(rent, "benunit", "household")
    assert np.allclose(rent_total, household_rent + paid, rtol=1e-6, atol=0.01)
    # 2. Bounds.
    assert np.all((share >= -1e-9) & (share <= 1 + 1e-9))
    assert np.all(rent >= 0)
    assert np.all(rent[roles == "non_dependant"] == 0)
    assert np.all(share[np.isin(roles, ["boarder", "lodger", "non_dependant"])] == 0)
    # 3. Tenure.
    payer = np.isin(roles, ["boarder", "lodger"])
    tenure = sim.calculate("benunit_tenure_type", YEAR)
    assert np.all(tenure[payer] == "RENT_PRIVATELY")
    social = calc(sim, "in_social_housing", "benunit") > 0
    assert not np.any(social[payer])
    assert np.all(calc(sim, "LHA_eligible")[payer])


@PROPERTY_SETTINGS
@given(population)
def test_non_dependants(population):
    situation, roles = build(population)
    sim = Simulation(situation=situation)
    liable = calc(sim, "benunit_is_rent_liable")
    non_dependant = calc(sim, "is_non_dependant_of_household_head", "benunit") > 0
    assert not np.any(non_dependant & liable)
    uc = calc(sim, "uc_non_dep_deductions")
    assert np.all(uc[roles != "head"] == 0)
    payer = np.isin(roles, ["boarder", "lodger"])
    assert np.all(calc(sim, "housing_benefit_non_dep_deductions")[payer] == 0)
    assert np.all(calc(sim, "council_tax_reduction_non_dep_deductions")[payer] == 0)


@PROPERTY_SETTINGS
@given(population)
def test_lha_categories(population):
    with_input, _ = build(population, shared_override=True)
    without_input, _ = build(population, shared_override=False)
    a = Simulation(situation=with_input)
    b = Simulation(situation=without_input)
    # 5. The UC category is set by entitlement alone.
    assert np.array_equal(
        a.calculate("LHA_category", YEAR),
        b.calculate("LHA_category", YEAR),
    )
    for sim in (a, b):
        rooms = calc(sim, "housing_benefit_LHA_allowed_bedrooms")
        shares = calc(sim, "housing_benefit_shares_accommodation")
        sdp = calc(sim, "severe_disability_premium") > 0
        category = sim.calculate("housing_benefit_LHA_category", YEAR)
        assert np.all(category[(rooms == 1) & shares & ~sdp] == "A")


@PROPERTY_SETTINGS
@given(population)
def test_meals_and_council_tax(population):
    with_meals, roles = build(population, meals_override="AT_LEAST_THREE_A_DAY")
    no_meals, _ = build(population, meals_override="NONE")
    a = Simulation(situation=with_meals)
    b = Simulation(situation=no_meals)
    # 6. Meals.
    assert np.all(calc(a, "housing_benefit_meals_deduction") >= 0)
    assert np.all(calc(a, "LHA_cap") <= calc(b, "LHA_cap") + 1e-6)
    # 7. Council tax shares, where the rent is shared. (Elsewhere only the
    # household head's family claims: test_council_tax_reduction_claimant_
    # properties.py.)
    claimant = calc(a, "council_tax_reduction_claimant_benunit")
    share = calc(a, "council_tax_reduction_joint_liability_share")
    total = a.map_result(claimant * share, "benunit", "household")
    sharer = calc(a, "liable_for_share_of_household_rent")
    shared = a.map_result(sharer, "benunit", "household") > 0
    assert np.all(total[shared] <= 1 + 1e-6)


@PROPERTY_SETTINGS
@given(population, st.floats(1, 10_000, allow_nan=False))
def test_rent_is_monotone_in_household_rent(population, bump):
    base, _ = build(population)
    raised, _ = build(population, rent_bump=bump)
    before = calc(Simulation(situation=base), "benunit_rent")
    after = calc(Simulation(situation=raised), "benunit_rent")
    assert np.all(after >= before - 1e-6)


@PROPERTY_SETTINGS
@given(population)
def test_no_op_without_sharers_boarders_or_lodgers(population):
    for house in population:
        for other in house["others"]:
            other["role"] = "non_dependant"
    situation, roles = build(population)
    sim = Simulation(situation=situation)
    # 9. The head's family has the whole rent; everyone else none.
    rent = calc(sim, "benunit_rent")
    head = roles == "head"
    assert np.all(rent[~head] == 0)
    rent_total = sim.map_result(rent, "benunit", "household")
    assert np.allclose(rent_total, calc(sim, "rent"), atol=0.01)
    # The previous formula: the head's family was charged for everyone
    # outside it (and every other family likewise).
    individual = calc(sim, "uc_individual_non_dep_deduction")
    person_head_family = sim.map_result(head, "benunit", "person") > 0
    everyone = sim.map_result(individual, "person", "household")
    head_family_own = sim.map_result(
        individual * person_head_family, "person", "household"
    )
    head_deductions = sim.map_result(
        calc(sim, "uc_non_dep_deductions") * head, "benunit", "household"
    )
    assert np.allclose(head_deductions, everyone - head_family_own, atol=0.01)
