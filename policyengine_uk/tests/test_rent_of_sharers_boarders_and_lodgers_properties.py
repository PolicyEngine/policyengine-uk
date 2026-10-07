"""Property-based tests for the rent, tenure and housing support of families
other than the household head's: sharers of the rent, boarders and lodgers.

Every generated population also contains one fixed household with a sharer,
a boarder, a lodger and a non-dependant, so no selection below is empty.
Adults have generated earnings, so non-dependant deductions are positive.

Invariants, for any generated population of households:

1. Conservation: the families' shares of the household's rent sum to one
   wherever anyone is liable for it, and the families' rents sum to the
   household's rent plus what boarders and lodgers pay the householder.
2. Bounds: each share is in [0, 1]; each family's rent is non-negative; a
   family that is neither the household head's, nor a sharer, nor a boarder
   or lodger has no rent.
3. Tenure: a boarder's or lodger's family rents privately, is never in social
   housing, and is LHA-eligible.
4. Non-dependants: nobody in a family liable for rent is a non-dependant; at
   most one family per household counts the household's non-dependants for
   Universal Credit, it is liable for the household's rent, and only it has
   Universal Credit deductions; Housing Benefit deductions over the families
   liable for the rent sum to the household's non-dependants' deductions; a
   boarder's or lodger's family has no Universal Credit or Housing Benefit
   deductions; no sharer, boarder or lodger is a Council Tax Reduction
   non-dependant.
5. Category: the Universal Credit LHA category does not depend on the
   household input is_shared_accommodation; the Housing Benefit category is
   the shared rate for any family entitled to one bedroom that lacks
   exclusive use and does not meet the severe disability premium conditions.
6. Meals: the Housing Benefit meals deduction is non-negative; on the LHA
   route (no rent officer board finding) the eligible rent does not depend
   on the meals in the rent; with a board finding it is the rent less the
   deduction, floored at zero.
7. Council tax: in a household whose rent is shared, the jointly liable
   claim shares never exceed one in total, each claim's scheme follows its
   own family's pensioner status, and the simulated reductions of the
   household's claims never exceed its eligible council tax.
8. Monotonicity: a family's rent is non-decreasing in the household's rent.
9. No-op: in a household with no sharers, boarders or lodgers, the household
   head's family has the whole rent and everyone else none, as before; and
   where the head's family claims Universal Credit, its non-dependant
   deductions and bedrooms equal the previous formulas (a deduction for
   everyone outside the family and a bedroom for each of them aged 16 or
   over); and Council Tax Reduction keeps the household's single claim,
   scheme and simulated-or-reported choice.
"""

import numpy as np
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from policyengine_core.periods import period as make_period

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
earnings = st.one_of(st.just(0.0), st.floats(1_000, 60_000, allow_nan=False))
adult = st.tuples(st.integers(18, 85), earnings)
# One household with every role, and a lodger who meets the severe disability
# premium conditions, so that no selection is empty.
SENTINEL = dict(
    head_adults=[(45, 0.0)],
    head_child_age=None,
    tenure="RENT_PRIVATELY",
    rent=18_000.0,
    council_tax=1_800.0,
    others=[
        dict(role=role, adults=[(age, pay)], child_age=None, payment=5_200.0)
        | dict(meals="AT_LEAST_THREE_A_DAY", pip=pip)
        for role, age, pay, pip in [
            ("sharer", 40, 0.0, False),
            ("boarder", 50, 0.0, False),
            ("lodger", 30, 0.0, False),
            ("lodger", 35, 0.0, True),
            ("non_dependant", 25, 25_000.0, False),
        ]
    ],
    shared=False,
)


@st.composite
def other_family(draw):
    return dict(
        role=draw(st.sampled_from(ROLES)),
        adults=draw(st.lists(adult, min_size=1, max_size=2)),
        child_age=draw(st.one_of(st.none(), st.integers(0, 15))),
        payment=draw(st.floats(1, 15_000, allow_nan=False)),
        meals=draw(st.sampled_from(MEALS)),
        pip=draw(st.booleans()),
    )


@st.composite
def households(draw):
    return dict(
        head_adults=draw(st.lists(adult, min_size=1, max_size=2)),
        head_child_age=draw(st.one_of(st.none(), st.integers(0, 15))),
        tenure=draw(st.sampled_from(TENURES)),
        rent=draw(money),
        council_tax=draw(st.floats(0, 3_000, allow_nan=False)),
        others=draw(st.lists(other_family(), min_size=0, max_size=3)),
        shared=draw(st.booleans()),
    )


population = st.lists(households(), min_size=0, max_size=5).map(
    lambda generated: [SENTINEL] + generated
)


def build(
    population,
    shared_override=None,
    meals_override=None,
    board_finding=False,
    rent_bump=0.0,
    roles_override=None,
):
    """One situation for the whole population; returns it and family roles."""
    people, benunits, homes, roles = {}, {}, {}, []
    for h, house in enumerate(population):
        members = []

        def add_family(name, adults, child_age, role, extra, pip=False):
            ids = []
            for i, (age, pay) in enumerate(adults):
                pid = f"{name}_adult_{i}"
                people[pid] = {
                    "age": age,
                    "employment_income": pay,
                    "is_claimant_or_partner": True,
                    "is_household_head": False,
                }
                if pip:
                    people[pid]["pip_dl"] = 3_988.40
                ids.append(pid)
            if child_age is not None:
                pid = f"{name}_child"
                people[pid] = {
                    "age": child_age,
                    "is_claimant_or_partner": False,
                    "is_household_head": False,
                }
                ids.append(pid)
            benunits[name] = {"members": ids, **extra}
            members.extend(ids)
            roles.append(role)
            return ids

        head_ids = add_family(
            f"h{h}_head", house["head_adults"], house["head_child_age"], "head", {}
        )
        people[head_ids[0]]["is_household_head"] = True
        for f, other in enumerate(house["others"]):
            role = roles_override or other["role"]
            boarder = role == "boarder"
            extra = {
                "liable_for_share_of_household_rent": role == "sharer",
                "meals_included_in_rent": (
                    (meals_override or other["meals"]) if boarder else "NONE"
                ),
                "housing_benefit_board_and_attendance_determination": (
                    board_finding and boarder
                ),
            }
            ids = add_family(
                f"h{h}_f{f}",
                other["adults"],
                other["child_age"],
                role,
                extra,
                pip=other["pip"],
            )
            if role in ("boarder", "lodger"):
                people[ids[0]][f"rent_paid_as_{role}"] = other["payment"]
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


def per_household(simulation, benunit_values):
    return simulation.map_result(benunit_values, "benunit", "household")


def of_household(simulation, variable):
    """A household variable's value for each family in the household."""
    families = simulation.populations["benunit"]
    return np.asarray(families.household(variable, make_period(YEAR)))


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
    assert np.allclose(per_household(sim, share), 1, atol=1e-6)
    assert np.allclose(
        per_household(sim, rent), household_rent + paid, rtol=1e-6, atol=0.01
    )
    # 2. Bounds.
    assert np.all((share >= -1e-9) & (share <= 1 + 1e-9))
    assert np.all(rent >= 0)
    assert np.all(rent[roles == "non_dependant"] == 0)
    assert np.all(share[np.isin(roles, ["boarder", "lodger", "non_dependant"])] == 0)
    # 3. Tenure.
    payer = np.isin(roles, ["boarder", "lodger"])
    assert payer.any()
    tenure = calc(sim, "benunit_tenure_type")
    assert np.all(tenure[payer] == "RENT_PRIVATELY")
    social = calc(sim, "in_social_housing", "benunit") > 0
    assert not np.any(social[payer])
    assert np.all(calc(sim, "LHA_eligible")[payer])


@PROPERTY_SETTINGS
@given(population)
def test_non_dependants(population):
    situation, roles = build(population)
    sim = Simulation(situation=situation)
    payer = np.isin(roles, ["boarder", "lodger"])
    liable_for_rent = calc(sim, "benunit_is_rent_liable")
    non_dependant = calc(sim, "is_non_dependant_of_household_head")
    person_liable = sim.map_result(liable_for_rent, "benunit", "person") > 0
    assert not np.any(non_dependant & person_liable)
    assert non_dependant.any()
    # Universal Credit: one claim per household counts the non-dependants.
    counted = calc(sim, "uc_non_dependants_counted")
    assert np.all(per_household(sim, counted) <= 1)
    household_liable = (
        sim.map_result(calc(sim, "is_liable_for_household_rent"), "person", "benunit")
        > 0
    )
    assert not np.any(counted & ~household_liable)
    uc = calc(sim, "uc_non_dep_deductions")
    assert np.all(uc[~counted] == 0)
    individual = calc(sim, "uc_individual_non_dep_deduction") * non_dependant
    total = sim.map_result(individual, "person", "household")
    assert np.all(per_household(sim, uc) <= total + 0.01)
    # Housing Benefit: apportioned over the families liable for the rent.
    hb = calc(sim, "housing_benefit_non_dep_deductions")
    hb_individual = (
        calc(sim, "household_benefits_individual_non_dep_deduction") * non_dependant
    )
    hb_total = sim.map_result(hb_individual, "person", "household")
    assert hb_total.max() > 0
    assert np.allclose(per_household(sim, hb), hb_total, rtol=1e-5, atol=0.01)
    assert np.all(hb[payer] == 0)
    assert np.all(uc[payer] == 0)
    # Council Tax Reduction: sharers, boarders and lodgers are not
    # non-dependants.
    ctr_eligible = (
        sim.map_result(
            calc(sim, "council_tax_reduction_individual_non_dep_deduction_eligible"),
            "person",
            "benunit",
        )
        > 0
    )
    assert not np.any(ctr_eligible[np.isin(roles, ["sharer", "boarder", "lodger"])])


@PROPERTY_SETTINGS
@given(population)
def test_lha_categories(population):
    with_input, _ = build(population, shared_override=True)
    without_input, _ = build(population, shared_override=False)
    a = Simulation(situation=with_input)
    b = Simulation(situation=without_input)
    # 5. The UC category is set by entitlement alone.
    assert np.array_equal(calc(a, "LHA_category"), calc(b, "LHA_category"))
    for sim in (a, b):
        rooms = calc(sim, "housing_benefit_LHA_allowed_bedrooms")
        shares = calc(sim, "housing_benefit_shares_accommodation")
        sdp = calc(sim, "housing_benefit_severe_disability_premium_applies")
        category = calc(sim, "housing_benefit_LHA_category")
        selected = (rooms == 1) & shares & ~sdp
        assert selected.any()
        assert np.all(category[selected] == "A")
        # The severe disability premium conditions keep a claimant off the
        # shared rate (reg 13D(2)(a)).
        assert sdp.any()
        assert not np.any(category[sdp] == "A")


@PROPERTY_SETTINGS
@given(population)
def test_meals_and_council_tax(population):
    with_meals, roles = build(population, meals_override="AT_LEAST_THREE_A_DAY")
    no_meals, _ = build(population, meals_override="NONE")
    finding, _ = build(
        population, meals_override="AT_LEAST_THREE_A_DAY", board_finding=True
    )
    a = Simulation(situation=with_meals)
    b = Simulation(situation=no_meals)
    c = Simulation(situation=finding)
    boarder = roles == "boarder"
    # 6. Meals.
    deduction = calc(a, "housing_benefit_meals_deduction")
    assert np.all(deduction >= 0)
    assert np.all(deduction[boarder] > 0)
    assert np.allclose(calc(a, "LHA_cap"), calc(b, "LHA_cap"), atol=0.01)
    rent = calc(c, "benunit_rent")
    assert np.allclose(
        calc(c, "LHA_cap")[boarder],
        np.maximum(0, rent - deduction)[boarder],
        atol=0.01,
    )
    # 7. Council tax shares, where the rent is shared. (Elsewhere only the
    # household head's family claims: test_council_tax_reduction_claimant_
    # properties.py.)
    claimant = calc(a, "council_tax_reduction_claimant_benunit")
    share = calc(a, "council_tax_reduction_joint_liability_share")
    total = per_household(a, claimant * share)
    sharer = calc(a, "liable_for_share_of_household_rent")
    shared = per_household(a, sharer) > 0
    assert shared.any()
    assert np.all(total[shared] <= 1 + 1e-6)
    # Each claim there follows its own family's pensioner status, not the
    # household head's family's (SI 2012/2885 reg 3).
    in_shared = of_household(a, "council_tax_reduction_claims_are_joint")
    assert np.array_equal(
        calc(a, "council_tax_reduction_claim_pensioner")[in_shared],
        calc(a, "council_tax_reduction_pensioner")[in_shared],
    )
    # The simulated reductions of the household's claims never exceed its
    # eligible council tax.
    simulated = calc(a, "simulated_council_tax_reduction_benunit")
    liability = calc(a, "council_tax_reduction_maximum_eligible_liability")
    assert np.all(per_household(a, simulated)[shared] <= liability[shared] + 0.01)


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
    situation, roles = build(population, roles_override="non_dependant")
    sim = Simulation(situation=situation)
    # 9. The head's family has the whole rent; everyone else none.
    rent = calc(sim, "benunit_rent")
    head = roles == "head"
    assert np.all(rent[~head] == 0)
    assert np.allclose(per_household(sim, rent), calc(sim, "rent"), atol=0.01)
    # The previous formulas charged a family for everyone outside it, and
    # gave it a bedroom for everyone aged 16 or over outside it.
    claims_uc = calc(sim, "uc_non_dependants_counted")
    assert np.array_equal(
        claims_uc,
        head & calc(sim, "is_uc_eligible") & calc(sim, "would_claim_uc"),
    )
    person_head_family = sim.map_result(head, "benunit", "person") > 0
    individual = calc(sim, "uc_individual_non_dep_deduction")
    outside = sim.map_result(individual * ~person_head_family, "person", "household")
    head_deductions = per_household(sim, calc(sim, "uc_non_dep_deductions") * head)
    head_claims = per_household(sim, claims_uc) > 0
    assert np.allclose(head_deductions[head_claims], outside[head_claims], atol=0.01)
    # Bedrooms: what the head's family would have alone, plus one for each
    # person aged 16 or over outside it.
    alone = [dict(house, others=[]) for house in population]
    alone_situation, _ = build(alone)
    alone_sim = Simulation(situation=alone_situation)
    bedrooms_alone = calc(alone_sim, "LHA_allowed_bedrooms")
    aged_16_or_over = calc(sim, "age") >= 16
    adults_outside = sim.map_result(
        aged_16_or_over & ~person_head_family, "person", "household"
    )
    head_bedrooms = per_household(sim, calc(sim, "LHA_allowed_bedrooms") * head)
    assert np.allclose(
        head_bedrooms[head_claims],
        (bedrooms_alone + adults_outside)[head_claims],
    )
    # Council Tax Reduction: one claim, on the household's scheme, simulated
    # or reported as the household's scheme is.
    assert not calc(sim, "council_tax_reduction_claims_are_joint").any()
    assert np.array_equal(
        calc(sim, "council_tax_reduction_claim_pensioner"),
        of_household(sim, "council_tax_reduction_household_has_pensioner"),
    )
    supported = of_household(sim, "council_tax_reduction_scheme_supported")
    assert np.array_equal(
        calc(sim, "council_tax_reduction_claim_scheme_supported"), supported
    )
    assert np.allclose(
        calc(sim, "council_tax_benefit"),
        np.where(
            supported,
            calc(sim, "simulated_council_tax_reduction_benunit"),
            calc(sim, "council_tax_benefit_reported", "benunit"),
        ),
        atol=0.01,
    )
