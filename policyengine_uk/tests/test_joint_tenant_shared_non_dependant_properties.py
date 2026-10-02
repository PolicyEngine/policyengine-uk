"""Property-based tests for non-dependants of joint occupiers in Housing
Benefit and Council Tax Reduction (non_dependant_normally_resides_with).

Invariants, for any generated population of households:

1. Conservation (HB reg 74(5)): in every household, the families' Housing
   Benefit non-dependant deductions sum to the household's individual
   deductions for its non-dependants, whichever joint occupiers each one
   resides with.
2. Bounds (CTR Sch 1 para 8(5)): each family's Council Tax Reduction part is
   between zero and the household's deductions, and the parts sum to at most
   the household's deductions (equal shares per liable person, with a couple
   bearing one person's part).
3. Differential: with every non-dependant shared (the default), the Housing
   Benefit deductions equal the previous formula (each family's share of the
   rent times the household's deductions) and the Council Tax Reduction
   deductions equal the previous formula (the deductions outside the family
   times council_tax_reduction_joint_liability_share).
4. Attribution: a shared non-dependant counts in the household head's
   family's size criteria exactly as when they are the head family's only,
   and in a sharer's exactly as when they are the other joint occupiers'
   only; a family that is not a joint occupier bears no deduction.
5. No-op: in a household with no sharers, the residence input changes
   nothing.
6. Universal Credit does not depend on the residence input.
7. Monotonicity: marking a non-dependant as one joint occupier's only never
   raises another joint occupier's bedrooms or deductions.
"""

import numpy as np
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation

YEAR = 2026
PROPERTY_SETTINGS = settings(
    max_examples=8,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)
RESIDENCE = [
    "EVERY_JOINT_OCCUPIER",
    "HOUSEHOLD_HEAD_FAMILY",
    "OTHER_JOINT_OCCUPIERS",
]
income = st.floats(0, 60_000, allow_nan=False, allow_infinity=False)


@st.composite
def family(draw, max_adults=2):
    return dict(
        ages=draw(st.lists(st.integers(18, 70), min_size=1, max_size=max_adults)),
        child_age=draw(st.one_of(st.none(), st.integers(0, 15))),
        income=draw(income),
    )


@st.composite
def households(draw):
    return dict(
        head=draw(family()),
        sharers=draw(st.lists(family(), min_size=0, max_size=2)),
        non_dependants=draw(
            st.lists(
                st.tuples(family(), st.sampled_from(RESIDENCE)),
                min_size=0,
                max_size=2,
            )
        ),
        lodger=draw(st.booleans()),
        rent=draw(st.floats(2_000, 30_000, allow_nan=False)),
    )


population = st.lists(households(), min_size=1, max_size=5)


def build(population, residence_override=None):
    """One situation for the whole population, with each family's role."""
    people, benunits, homes, roles = {}, {}, {}, []
    for h, house in enumerate(population):
        members = []

        def add_family(name, fam, role, extra):
            ids = []
            for i, age in enumerate(fam["ages"]):
                pid = f"{name}_adult_{i}"
                people[pid] = {
                    "age": {YEAR: age},
                    "is_claimant_or_partner": {YEAR: True},
                    "is_household_head": {YEAR: False},
                    "employment_income": {YEAR: fam["income"] if i == 0 else 0},
                }
                ids.append(pid)
            if fam["child_age"] is not None:
                pid = f"{name}_child"
                people[pid] = {
                    "age": {YEAR: fam["child_age"]},
                    "is_claimant_or_partner": {YEAR: False},
                    "is_household_head": {YEAR: False},
                }
                ids.append(pid)
            benunits[name] = {"members": ids, **extra}
            members.extend(ids)
            roles.append(role)
            return ids

        head_ids = add_family(f"h{h}_head", house["head"], "head", {})
        people[head_ids[0]]["is_household_head"] = {YEAR: True}
        for f, sharer in enumerate(house["sharers"]):
            add_family(
                f"h{h}_s{f}",
                sharer,
                "sharer",
                {"liable_for_share_of_household_rent": {YEAR: True}},
            )
        for f, (non_dep, residence) in enumerate(house["non_dependants"]):
            add_family(
                f"h{h}_n{f}",
                non_dep,
                "non_dependant",
                {
                    "non_dependant_normally_resides_with": {
                        YEAR: residence_override or residence
                    }
                },
            )
        if house["lodger"]:
            ids = add_family(
                f"h{h}_l",
                dict(ages=[40], child_age=None, income=10_000),
                "lodger",
                {},
            )
            people[ids[0]]["rent_paid_as_lodger"] = {YEAR: 4_000}
        homes[f"h{h}"] = {
            "members": members,
            "rent": {YEAR: house["rent"]},
            "tenure_type": {YEAR: "RENT_PRIVATELY"},
            "brma": {YEAR: "MAIDSTONE"},
        }
    situation = {"people": people, "benunits": benunits, "households": homes}
    return Simulation(situation=situation), np.array(roles)


def calc(sim, variable):
    return np.asarray(sim.calculate(variable, YEAR), dtype=float)


def benunit_household(sim):
    """Household index of each benefit unit."""
    person_benunit = sim.populations["benunit"].members_entity_id
    person_household = sim.populations["household"].members_entity_id
    out = np.zeros(sim.populations["benunit"].count, dtype=int)
    out[person_benunit] = person_household
    return out


def per_household(sim, benunit_values):
    return np.bincount(
        benunit_household(sim),
        weights=benunit_values,
        minlength=sim.populations["household"].count,
    )


def person_per_household(sim, person_values):
    return np.bincount(
        sim.populations["household"].members_entity_id,
        weights=person_values,
        minlength=sim.populations["household"].count,
    )


def has_sharer(sim, roles):
    return (
        per_household(sim, (roles == "sharer").astype(float))[benunit_household(sim)]
        > 0
    )


@PROPERTY_SETTINGS
@given(population)
def test_housing_benefit_deductions_are_conserved(population):
    sim, roles = build(population)
    deductions = calc(sim, "household_benefits_individual_non_dep_deduction") * calc(
        sim, "is_non_dependant_of_household_head"
    )
    families = calc(sim, "housing_benefit_non_dep_deductions")
    np.testing.assert_allclose(
        per_household(sim, families), person_per_household(sim, deductions), atol=1e-6
    )
    # A family that is not a joint occupier bears none.
    assert np.all(families[(roles == "non_dependant") | (roles == "lodger")] == 0)


@PROPERTY_SETTINGS
@given(population)
def test_council_tax_reduction_deductions_are_bounded(population):
    sim, roles = build(population)
    deductions = calc(sim, "council_tax_reduction_individual_non_dep_deduction")
    in_household = person_per_household(sim, deductions)
    families = calc(sim, "council_tax_reduction_non_dep_deductions")
    assert np.all(families >= -1e-9)
    assert np.all(families <= in_household[benunit_household(sim)] + 1e-6)
    assert np.all(per_household(sim, families) <= in_household + 1e-6)
    assert np.all(families[(roles == "non_dependant") | (roles == "lodger")] == 0)


@PROPERTY_SETTINGS
@given(population)
def test_shared_default_matches_the_previous_formulas(population):
    sim, roles = build(population, residence_override="EVERY_JOINT_OCCUPIER")
    household = benunit_household(sim)
    hb_individual = calc(sim, "household_benefits_individual_non_dep_deduction") * calc(
        sim, "is_non_dependant_of_household_head"
    )
    share = calc(sim, "share_of_household_rent")
    np.testing.assert_allclose(
        calc(sim, "housing_benefit_non_dep_deductions"),
        share * person_per_household(sim, hb_individual)[household],
        atol=1e-6,
    )
    ctr_individual = calc(sim, "council_tax_reduction_individual_non_dep_deduction")
    own = np.bincount(
        sim.populations["benunit"].members_entity_id,
        weights=ctr_individual,
        minlength=sim.populations["benunit"].count,
    )
    previous = (person_per_household(sim, ctr_individual)[household] - own) * calc(
        sim, "council_tax_reduction_joint_liability_share"
    )
    joint_occupier = (roles == "head") | (roles == "sharer")
    np.testing.assert_allclose(
        calc(sim, "council_tax_reduction_non_dep_deductions")[joint_occupier],
        previous[joint_occupier],
        atol=1e-6,
    )


@PROPERTY_SETTINGS
@given(population)
def test_shared_counts_as_head_only_for_the_head_and_as_others_only_for_sharers(
    population,
):
    shared, roles = build(population, residence_override="EVERY_JOINT_OCCUPIER")
    head_only, _ = build(population, residence_override="HOUSEHOLD_HEAD_FAMILY")
    others_only, _ = build(population, residence_override="OTHER_JOINT_OCCUPIERS")
    rooms = "housing_benefit_LHA_allowed_bedrooms"
    head = roles == "head"
    sharer = roles == "sharer"
    np.testing.assert_array_equal(
        calc(shared, rooms)[head], calc(head_only, rooms)[head]
    )
    np.testing.assert_array_equal(
        calc(shared, rooms)[sharer], calc(others_only, rooms)[sharer]
    )
    # Monotonicity: one joint occupier's non-dependant never raises another's
    # bedrooms or deductions.
    deductions = "housing_benefit_non_dep_deductions"
    assert np.all(calc(head_only, rooms)[sharer] <= calc(shared, rooms)[sharer])
    assert np.all(
        calc(head_only, deductions)[sharer] <= calc(shared, deductions)[sharer] + 1e-6
    )
    with_sharer = has_sharer(shared, roles)
    assert np.all(
        calc(others_only, rooms)[head & with_sharer]
        <= calc(shared, rooms)[head & with_sharer]
    )
    assert np.all(
        calc(others_only, deductions)[head & with_sharer]
        <= calc(shared, deductions)[head & with_sharer] + 1e-6
    )


@PROPERTY_SETTINGS
@given(population)
def test_residence_is_a_no_op_without_sharers_and_for_universal_credit(population):
    sims = [build(population, residence_override=r) for r in RESIDENCE]
    roles = sims[0][1]
    without_sharer = ~has_sharer(sims[0][0], roles)
    for variable in [
        "housing_benefit_LHA_allowed_bedrooms",
        "housing_benefit_LHA_additional_bedrooms",
        "housing_benefit_non_dep_deductions",
        "council_tax_reduction_non_dep_deductions",
        "housing_benefit_claimant_has_non_dependant",
    ]:
        reference = calc(sims[0][0], variable)[without_sharer]
        for sim, _ in sims[1:]:
            np.testing.assert_allclose(
                calc(sim, variable)[without_sharer], reference, atol=1e-6
            )
    for variable in [
        "LHA_allowed_bedrooms",
        "uc_non_dep_deductions",
        "lha_renter_has_non_dependant",
    ]:
        reference = calc(sims[0][0], variable)
        for sim, _ in sims[1:]:
            np.testing.assert_allclose(calc(sim, variable), reference, atol=1e-6)
