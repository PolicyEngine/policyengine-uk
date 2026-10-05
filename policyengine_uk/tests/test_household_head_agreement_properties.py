"""Property-based tests that every programme reads one household head.

The input is_household_head can flag several members of a household, or none:
in user situations, and in any household left without the input once another
household has it (it then defaults to false). is_resolved_household_head
settles on exactly one head per household, and every programme reads it or
benunit_contains_household_head.

Invariants, for any generated population of households and any flag input
(one member, several, both members of a couple, everyone, none, or no input
at all), with families of non-dependants, sharers, boarders and lodgers,
families of a child alone, and ties in age. Invariants marked "pin" restate the formula, so they guard
against regressions rather than check it independently.

1. One head: exactly one member of each household is the head: the eldest
   flagged member where the input flags any member of the household, else the
   eldest member, a tie in age going to the member listed first. Checked
   against an independent implementation.
2. One family: benunit_contains_household_head holds for the head's family
   and no other.
3. Agreement: every programme treats that family as the household head's.
   - Rent: only the head's family and sharers have a share of the household's
     rent; the head's family's share sits on the head alone; and the shares
     sum to the household's rent. Beyond that, a person's rent is only what
     they pay the householder as a boarder or lodger.
   - Non-dependants (pin): a person is a non-dependant of the household head
     if and only if their family is neither the head's nor liable for rent.
   - Universal Credit non-dependant deductions fall only on the claim that
     counts the household's non-dependants (uc_non_dependants_counted); at
     most one family in a household is counted, and where the head's family
     is liable for the rent and claims Universal Credit, it is the head's.
     Only families with a share of the rent have Housing Benefit ones.
   - Council Tax Reduction: only the head's family and sharers claim; where
     the head is 18 or over, the head's family claims and no one in it is a
     non-dependant.
   - A family paying the householder as boarders or lodgers is never the
     head's, and the maintenance loan never has the head living with parents.
4. Metamorphic: every value the simulation computes, other than the
   is_household_head input itself, is identical to the simulation whose input
   flags exactly the head from invariant 1. That input is well formed, so all
   programmes agree on the head there; no flag input can make them disagree.
5. Structural: no module outside is_resolved_household_head reads
   is_household_head, so a new formula cannot bypass the resolved head.
"""

import re
from pathlib import Path

import numpy as np
from hypothesis import HealthCheck, example, given, settings
from hypothesis import strategies as st

import policyengine_uk
from policyengine_uk import Simulation

YEAR = 2026
PROPERTY_SETTINGS = settings(
    max_examples=15,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)
SCHEMES = [
    ("ENGLAND", "MAIDSTONE"),
    ("ENGLAND", "MERTON"),
    ("ENGLAND", "OXFORD"),
    ("SCOTLAND", "CITY_OF_EDINBURGH"),
    ("WALES", "CARDIFF"),
]
TENURES = [
    "RENT_PRIVATELY",
    "RENT_FROM_COUNCIL",
    "RENT_FROM_HA",
    "OWNED_OUTRIGHT",
    "OWNED_WITH_MORTGAGE",
]
# Roles of the families after the first.
ROLES = ["non_dependant", "sharer", "boarder", "lodger"]
HEAD_FLAGS = ["one", "several", "couple", "everyone", "none", "unset"]
# Ages around 16, 18 and State Pension age, and repeated values, so ties and
# young adults are common.
adult_age = st.one_of(
    st.sampled_from([16, 17, 18, 19, 20, 40, 66, 67, 80]), st.integers(16, 100)
)
money = st.floats(0, 40_000, allow_nan=False, allow_infinity=False)
OUTPUTS = [
    "household_net_income",
    "hbai_household_net_income_ahc",
    "maintenance_loan",
    "is_resolved_household_head",
    "benunit_contains_household_head",
    "is_claimant_or_partner",
    "share_of_household_rent",
    "personal_rent",
    "benunit_is_rent_liable",
    "is_non_dependant_of_household_head",
    "uc_non_dep_deductions",
    "uc_non_dependants_counted",
    "housing_benefit_non_dep_deductions",
    "LHA_allowed_bedrooms",
    "housing_benefit_LHA_allowed_bedrooms",
    "lha_renter_has_non_dependant",
    "council_tax_reduction_claimant_benunit",
    "council_tax_reduction_individual_non_dep_deduction_eligible",
    "pays_rent_to_householder",
    "maintenance_loan_living_arrangement",
    "maintenance_loan_household_income",
]


@st.composite
def family(draw):
    # Sometimes a family of one child under 16 and no adult, so that the
    # head's family can have no claimant and no one is liable for the rent.
    children_only = draw(st.sampled_from([False, False, False, True]))
    return dict(
        ages=[] if children_only else draw(st.lists(adult_age, min_size=1, max_size=2)),
        child_age=draw(
            st.integers(0, 15)
            if children_only
            else st.one_of(st.none(), st.integers(0, 17))
        ),
        earnings=draw(st.lists(money, min_size=2, max_size=2)),
        role=draw(st.sampled_from(ROLES)),
        payment=draw(st.floats(1, 12_000, allow_nan=False)),
        student=draw(st.booleans()),
    )


def size(fam):
    return len(fam["ages"]) + (fam["child_age"] is not None)


@st.composite
def households(draw):
    families = draw(st.lists(family(), min_size=1, max_size=4))
    members = sum(size(fam) for fam in families)
    return dict(
        families=families,
        scheme=draw(st.sampled_from(SCHEMES)),
        tenure=draw(st.sampled_from(TENURES)),
        rent=draw(money),
        council_tax=draw(st.floats(0, 4_000, allow_nan=False)),
        head_flags=draw(st.sampled_from(HEAD_FLAGS)),
        # Which member is flagged ("one"), or which are ("several").
        head_choice=draw(st.lists(st.integers(0, members - 1), min_size=1)),
    )


population = st.lists(households(), min_size=1, max_size=5)


def _family(ages, child_age=None, role="non_dependant", student=False, earnings=0.0):
    return dict(
        ages=ages,
        child_age=child_age,
        earnings=[earnings, 0.0],
        role=role,
        payment=1.0,
        student=student,
    )


def _household(
    families, head_flags, head_choice, rent=9_000.0, tenure="RENT_PRIVATELY"
):
    return dict(
        families=families,
        scheme=("ENGLAND", "MAIDSTONE"),
        tenure=tenure,
        rent=rent,
        council_tax=1_500.0,
        head_flags=head_flags,
        head_choice=head_choice,
    )


# Households where no one is liable for the rent, so share_of_household_rent
# falls back to the head's family, and the raw flags disagree with the head.
# Random generation rarely builds them.
NO_ONE_LIABLE = [
    # A flagged household beside one of two children with no member flagged:
    # the elder child's family has the rent.
    _household([_family([40])], "one", [0], rent=6_000.0),
    _household([_family([], 12), _family([], 9)], "none", [0]),
    # Two flagged children: the elder, alone in its family, is the head, and
    # the younger's parent is neither liable nor a sharer.
    _household([_family([], 12), _family([40], 8)], "several", [0, 2]),
]
# A student in higher education flagged as head beside their parent, in an
# owner-occupied home: the only case where the maintenance loan's
# living-arrangement and household-income proxies turn on the head. The parent
# earns, so the sponsor's income counts. Random generation rarely builds it.
STUDENT_FLAGGED_BESIDE_PARENT = [
    _household(
        [_family([52], earnings=30_000.0), _family([20], student=True)],
        "several",
        [0, 1],
        rent=0.0,
        tenure="OWNED_OUTRIGHT",
    ),
]


def flagged_members(house):
    """Indices of the members the input flags, in household order."""
    families = house["families"]
    members = sum(size(fam) for fam in families)
    mode = house["head_flags"]
    if mode == "one":
        return {house["head_choice"][0]}
    if mode == "several":
        return set(house["head_choice"])
    if mode == "everyone":
        return set(range(members))
    if mode == "couple":
        start = 0
        for fam in families:
            if len(fam["ages"]) == 2:
                return {start, start + 1}
            start += size(fam)
        return set(house["head_choice"])
    return set()


def build(population, head_input=None):
    """One situation for the whole population, plus per-person facts.

    head_input, if given, is the is_household_head input for every person,
    in order; otherwise each household's head_flags decides it.
    """
    people, benunits, homes = {}, {}, {}
    facts = dict(flagged=[], age=[], household=[], benunit=[], sharer=[])
    benunit_index = 0
    for h, house in enumerate(population):
        country, local_authority = house["scheme"]
        flagged_set = flagged_members(house)
        members, member_index = [], 0
        for f, fam in enumerate(house["families"]):
            role = fam["role"] if f > 0 else "head_candidate"
            ids = []
            ages = list(fam["ages"])
            if fam["child_age"] is not None:
                ages.append(fam["child_age"])
            for i, age in enumerate(ages):
                pid = f"h{h}_f{f}_m{i}"
                adult = i < len(fam["ages"])
                person = {"age": age}
                if adult:
                    person["employment_income"] = fam["earnings"][i]
                    if fam["student"] and i == 0 and 18 <= age < 25:
                        person["current_education"] = "TERTIARY"
                    if i == 0 and role in ("boarder", "lodger"):
                        person[f"rent_paid_as_{role}"] = fam["payment"]
                flagged = member_index in flagged_set
                if head_input is not None:
                    person["is_household_head"] = bool(head_input[len(facts["age"])])
                elif house["head_flags"] != "unset":
                    person["is_household_head"] = flagged
                people[pid] = person
                ids.append(pid)
                facts["flagged"].append(flagged)
                facts["age"].append(age)
                facts["household"].append(h)
                facts["benunit"].append(benunit_index)
                member_index += 1
            facts["sharer"].append(role == "sharer")
            benunits[f"h{h}_f{f}"] = {
                "members": ids,
                "liable_for_share_of_household_rent": role == "sharer",
                "claims_all_entitled_benefits": True,
                "would_claim_uc": True,
            }
            members.extend(ids)
            benunit_index += 1
        homes[f"h{h}"] = {
            "members": members,
            "country": country,
            "local_authority": local_authority,
            "council_tax": house["council_tax"],
            "rent": house["rent"],
            "tenure_type": house["tenure"],
        }
    situation = {
        group: {
            name: {
                key: value if key == "members" else {YEAR: value}
                for key, value in entity.items()
            }
            for name, entity in entities.items()
        }
        for group, entities in (
            ("people", people),
            ("benunits", benunits),
            ("households", homes),
        )
    }
    return situation, {k: np.array(v) for k, v in facts.items()}


def reference_head(facts):
    """The household head, implemented independently of the model."""
    head = np.zeros(facts["age"].size, dtype=bool)
    for h in np.unique(facts["household"]):
        members = np.flatnonzero(facts["household"] == h)  # in order
        flagged = members[facts["flagged"][members]]
        candidates = flagged if flagged.size else members
        # argmax takes the first of tied maxima: the member listed first.
        head[candidates[np.argmax(facts["age"][candidates])]] = True
    return head


def calc(simulation, variable):
    return np.asarray(simulation.calculate(variable, YEAR))


def any_in_benunit(values, facts):
    result = np.zeros(facts["sharer"].size, dtype=bool)
    np.logical_or.at(result, facts["benunit"], values)
    return result


def sum_in_household(values, household):
    return np.bincount(household, weights=values.astype(float))


@PROPERTY_SETTINGS
@given(population)
@example(NO_ONE_LIABLE)
@example(STUDENT_FLAGGED_BESIDE_PARENT)
def test_every_programme_reads_one_head(population):
    situation, facts = build(population)
    sim = Simulation(situation=situation)
    benunit_of = facts["benunit"]
    age = facts["age"]

    # 1. One head, as the independent implementation finds it.
    head = calc(sim, "is_resolved_household_head")
    expected = reference_head(facts)
    assert np.array_equal(head, expected)
    assert np.all(sum_in_household(head, facts["household"]) == 1)

    # 2. One family.
    head_family = calc(sim, "benunit_contains_household_head")
    assert np.array_equal(head_family, any_in_benunit(head, facts))
    person_head_family = head_family[benunit_of]

    # 3. Agreement. Rent:
    sharer = facts["sharer"]
    share = calc(sim, "share_of_household_rent")
    assert np.all(share[~head_family & ~sharer] == 0)
    rent = np.array([house["rent"] for house in population])
    personal_rent = calc(sim, "personal_rent")
    paid_to_householder = calc(sim, "rent_paid_as_boarder") + calc(
        sim, "rent_paid_as_lodger"
    )
    share_of_rent = personal_rent - paid_to_householder
    is_benunit_head = calc(sim, "is_benunit_head")
    carries_share = head | (sharer[benunit_of] & ~person_head_family & is_benunit_head)
    assert np.all(np.abs(share_of_rent[~carries_share]) < 0.01)
    rent_charged = sum_in_household(share_of_rent, facts["household"])
    assert np.allclose(rent_charged, rent, atol=0.01)
    # Non-dependants (pin).
    non_dependant = calc(sim, "is_non_dependant_of_household_head")
    rent_liable = calc(sim, "benunit_is_rent_liable")
    assert np.array_equal(non_dependant, ~person_head_family & ~rent_liable[benunit_of])
    # Universal Credit non-dependant deductions fall on the one claim that
    # counts the household's non-dependants: the head's family's wherever it
    # is liable for the rent and claims.
    counted = calc(sim, "uc_non_dependants_counted")
    assert np.all(counted[calc(sim, "uc_non_dep_deductions") > 0])
    household_of_benunit = np.zeros(head_family.size, dtype=int)
    household_of_benunit[benunit_of] = facts["household"]
    assert np.all(sum_in_household(counted, household_of_benunit) <= 1)
    head_family_claims = (
        head_family
        & any_in_benunit(calc(sim, "is_liable_for_household_rent"), facts)
        & calc(sim, "is_uc_eligible")
        & calc(sim, "would_claim_uc")
    )
    head_claims_uc = sum_in_household(head_family_claims, household_of_benunit) > 0
    in_household = head_claims_uc[household_of_benunit]
    assert np.array_equal(counted[in_household], head_family[in_household])
    # Housing Benefit non-dependant deductions.
    assert np.all(calc(sim, "housing_benefit_non_dep_deductions")[share == 0] == 0)
    # Council Tax Reduction.
    claimant = calc(sim, "council_tax_reduction_claimant_benunit")
    assert not np.any(claimant & ~head_family & ~sharer)
    adult_head_family = any_in_benunit(head & (age >= 18), facts)
    assert np.all(claimant[adult_head_family])
    ctr_non_dependant = calc(
        sim, "council_tax_reduction_individual_non_dep_deduction_eligible"
    )
    assert not np.any(ctr_non_dependant & adult_head_family[benunit_of])
    # Boarders and lodgers; the maintenance loan.
    assert not np.any(calc(sim, "pays_rent_to_householder") & person_head_family)
    arrangement = calc(sim, "maintenance_loan_living_arrangement")
    assert not np.any(arrangement[head] == "LIVING_WITH_PARENTS")


def computed_values(simulation):
    """Every (variable, period) array the simulation holds."""
    values = {}
    for name in simulation.tax_benefit_system.variables:
        holder = simulation.get_holder(name)
        for period in holder.get_known_periods():
            values[(name, str(period))] = holder.get_array(period)
    return values


def identical(a, b):
    a, b = np.asarray(a), np.asarray(b)
    if a.dtype.kind == "f":
        return np.array_equal(a, b, equal_nan=True)
    return np.array_equal(a, b)


@PROPERTY_SETTINGS
@given(population)
@example(NO_ONE_LIABLE)
@example(STUDENT_FLAGGED_BESIDE_PARENT)
def test_flags_matter_only_through_the_head(population):
    situation, facts = build(population)
    well_formed, _ = build(population, head_input=reference_head(facts))
    simulations = Simulation(situation=situation), Simulation(situation=well_formed)
    for simulation in simulations:
        for variable in OUTPUTS:
            simulation.calculate(variable, YEAR)
    # 4. Metamorphic: everything but the input itself is identical.
    flagged, settled = (computed_values(simulation) for simulation in simulations)
    flagged = {k: v for k, v in flagged.items() if k[0] != "is_household_head"}
    settled = {k: v for k, v in settled.items() if k[0] != "is_household_head"}
    assert flagged.keys() == settled.keys()
    different = [key for key in flagged if not identical(flagged[key], settled[key])]
    assert different == []


def test_only_the_resolved_head_reads_the_flag():
    # 5. Structural: is_household_head is read in one place.
    package = Path(policyengine_uk.__file__).parent
    reader = re.compile(r"""["']is_household_head["']""")
    allowed = {
        Path("variables/household/demographic/is_resolved_household_head.py"),
    }
    readers = {
        path.relative_to(package)
        for path in package.rglob("*.py")
        if "tests" not in path.relative_to(package).parts
        and reader.search(path.read_text())
    }
    assert readers == allowed
