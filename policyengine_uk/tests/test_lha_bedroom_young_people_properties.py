"""Property-based tests for the LHA size criteria (UC Regs 2013 Sch 4 paras
9-12; HB Regs 2006 and HB (SPC) Regs 2006 reg 13D and reg 21(3)): the
bedrooms of benefit-unit members aged 16 or over who are not the claimant or
partner, the children of other families in the household, foster and
adoption placements, the additional bedrooms for foster parents and
overnight care, and the housing cost contributions of in-unit
non-dependants.

Invariants, for any generated population of households:

1. Monotonicity: adding a person aged 16 to 19 to any family never lowers
   any family's Universal Credit or Housing Benefit bedrooms, whether the
   claimant and partner are supplied or inferred.
2. Exact effect of a person aged 16 to 19 who is not the claimant or
   partner:
   - their family gains one Universal Credit bedroom unless they are a
     qualifying young person no one is responsible for (para 9(2)(g)), the
     family's foster child (under 18, para 9(2)(c)), or the household head
     and not a qualifying young person (the formula treats the head as
     liable for the rent: paras 1(2), 9(1)(a) and 9(2)(d));
   - their family gains one Housing Benefit bedroom unless they are placed
     with it as a foster child (HB reg 21(3));
   - a family they are placed with as a foster child gains the foster
     parent's (UC, para 12) or qualifying parent or carer's (HB,
     13D(3A)(b)) bedroom if it did not already have it;
   - if they join a non-dependant's family, the claim that counts the
     household's non-dependants (uc_non_dependants_counted) gains one
     Universal Credit bedroom unless no one is responsible for them;
   - if they are an in-unit non-dependant (invariant 6) of a family that
     makes no Universal Credit claim of its own and does not count the
     household's non-dependants, the claim that does gains one Universal
     Credit bedroom, as it bears their contribution (para 9(2)(f));
   - if they are the foster child, not a qualifying young person, of
     the head's, a sharer's, a boarder's or a lodger's family, the
     claim that counts the household's non-dependants gains one
     Universal Credit bedroom unless it is that family's or they head
     the household: para 9(2)(c) takes them out of their foster
     parent's extended benefit unit only;
   - if they join a non-dependant's, boarder's or lodger's family, every
     family liable for the rent gains one Housing Benefit bedroom, even if
     they are placed with that family: reg 21(3) takes out only a child or
     young person placed with the claimant or partner, so they occupy the
     claimant's dwelling (reg 13D(12));
   - no other family's bedrooms change.
3. Children: adding a child under 16 who is neither fostered nor placed for
   adoption to any family never lowers any family's bedrooms under either
   scheme and raises each by at most one.
4. Placed children: adding a child under 16 placed with a family as a
   foster child or for adoption gives that family one more bedroom under
   each scheme if it did not already meet the foster parent condition (UC)
   or have a qualifying parent or carer (HB), and none otherwise. If the
   family is a non-dependant's, boarder's or lodger's, each family liable
   for the rent gains 0 or 1 Housing Benefit bedrooms: the child occupies
   its dwelling (reg 21(3) names only a placement with the claimant or
   partner; reg 13D(12)) and shares a room with the other children if it
   can. A foster child changes no other family's Universal Credit bedrooms:
   no one is responsible for them (reg 4(6)(a); para 9(2)(g)). A child
   placed for adoption counts as a child under Universal Credit (reg
   4A(1)(c)): the adopter's family and the claim counting a non-dependant
   adopter's household each gain 0 or 1 more. No joint tenant's bedrooms
   change, and no other family's.
5. Reference: every family's bedrooms, and its additional bedrooms, equal a
   count of the size criteria made by the test itself. The added person's
   status comes from the test's own predicates on the inputs (UC reg 5
   qualifying young person, the Child Benefit qualifying young person for
   HB reg 19, looked after and under 18 for a foster child), not from the
   model; which claim counts the non-dependants, which families make a
   claim of their own, and which families are liable for the rent, are read
   from the model and tested elsewhere. Children's rooms come from a
   brute-force pairing. The count applies the same legal readings as the
   model, so it checks the implementation of those readings, not the
   readings themselves:
   - one for the claimant or couple;
   - one for each other member aged 16 or over (UC: except a qualifying
     young person no one is responsible for, a foster child under 18 and a
     household head who is not a qualifying young person; HB: except one
     placed with the family as a foster child);
   - for the claim counting the non-dependants (UC), one for each person
     aged 16 or over in a non-dependant's family, except one no one is
     responsible for, one for each in-unit non-dependant of a family
     that makes no claim of its own, and one for each foster child of
     another family who is not a qualifying young person and does not
     head the household; for a family liable for the rent
     (HB), one for the couple or single adult of each non-dependant's,
     boarder's or lodger's family and one for each other member aged 16 or
     over, including one placed with that family;
   - the fewest rooms that hold the counted children under 16 two to a
     room, where only children of the same sex or two children under 10 may
     share, found by brute force. UC counts the family's own children other
     than foster children and, for the counting claim, the non-dependants'
     children other than foster children. HB counts the family's children
     other than foster children and children placed for adoption and, for
     a family liable for the rent, every child of each non-dependant's,
     boarder's or lodger's family, placed or not;
   - one additional bedroom if anyone so counted, or a child placed with
     the family, has overnight care, and one if the family fosters, has a
     child placed for adoption, or has an approved foster parent between
     placements.
6. In-unit non-dependants: every member of a benefit unit aged 16 or over
   who is neither the claimant nor partner nor a Universal Credit
   qualifying young person nor the household head (the householder in
   whose name the accommodation is rented, whom the formula reads as liable
   for the rent, so that para 9(2)(d) excludes them) nor the family's
   foster child (para 9(2)(c)) is a non-dependant (para 9(2)) with a
   bedroom (para 10(1)(c)). So their family has one more Universal Credit
   bedroom with them than without them, and making them qualifying young
   persons the renter is responsible for (para 10(1)(b)) leaves every
   family's Universal Credit bedrooms unchanged, except that the claim
   counting the household's non-dependants loses the bedroom of one whose
   own family makes no claim and is not that claim (para 9(2)(g)). The
   model's is_benefit_unit_non_dependant_for_universal_credit, which the
   formula reads, marks exactly these members.
7. Close-relative adopters: marking every child's adopter as a foster
   parent or close relative of the child (UC reg 89(3)(a)) takes away the
   foster parent condition exactly where an adoption placement was the
   family's only route to it (para 12(4)(b)); it lowers that family's
   Universal Credit bedrooms by one and changes nothing else: Universal
   Credit responsibility (reg 4A(1)(c)), the Housing Benefit placement test
   (reg 21(3)), the qualifying parent or carer and every family's Housing
   Benefit bedrooms stay the same.
8. Rooms and contributions: nobody owes a housing cost contribution without
   being a non-dependant (para 13). Adding an adult aged 16 to 64, not in
   education, to any family: if they are an in-unit non-dependant, they owe
   a contribution unless aged under 21 or receiving Attendance Allowance
   (para 16(2)); the claim that bears it (their own family's if it makes a
   claim, otherwise the one that counts the household's non-dependants)
   gains exactly that contribution, unless its renter is exempt (para 15),
   and one bedroom; no other family's contributions change.
9. Coding: moving such an adult aged 20 or over, not claiming, between a
   family and a benefit unit of their own leaves every claiming family's
   Universal Credit bedrooms, contributions and award unchanged, with one
   exception. Where the adult's family makes its own claim and does not
   count the household's non-dependants, that claim bears them while the
   family includes them (invariant 8), and the claim that counts the
   household's non-dependants bears them in a benefit unit of their own.
   Their bedroom then moves between those two claims, and no other claim
   changes. Someone younger can be a qualifying young person, and their
   family's Child Benefit and child element then depend on them.
"""

import numpy as np
from hypothesis import HealthCheck, assume, example, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation

YEAR = 2025  # Situation inputs without a period are set for 2025.
PROPERTY_SETTINGS = settings(
    max_examples=25,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)
ROLES = ["sharer", "boarder", "lodger", "non_dependant"]
OCCUPIER_ROLES = ("non_dependant", "boarder", "lodger")
EDUCATION = ["NOT_IN_EDUCATION", "UPPER_SECONDARY", "UPPER_SECONDARY", "TERTIARY"]
KINDS = ["own", "own", "own", "foster", "adopted"]
OVERNIGHT = st.sampled_from([False, False, False, True])

# (age, is_male, kind, has overnight care)
child = st.tuples(st.integers(0, 15), st.booleans(), st.sampled_from(KINDS), OVERNIGHT)


@st.composite
def family(draw, role):
    return dict(
        role=role,
        adults=draw(
            st.lists(st.tuples(st.integers(20, 85), OVERNIGHT), min_size=1, max_size=2)
        ),
        children=draw(st.lists(child, min_size=0, max_size=4)),
        between_placements=draw(st.sampled_from([False, False, False, True])),
    )


@st.composite
def household(draw):
    others = draw(
        st.lists(st.sampled_from(ROLES).flatmap(family), min_size=0, max_size=2)
    )
    return [draw(family("head"))] + others


@st.composite
def young_person(draw):
    person = dict(
        age=draw(st.integers(16, 19)),
        is_male=draw(st.booleans()),
        current_education=draw(st.sampled_from(EDUCATION)),
        age_started_or_accepted_current_education_or_training=draw(st.integers(14, 19)),
        is_before_universal_credit_qualifying_young_person_terminal_date=draw(
            st.booleans()
        ),
        is_looked_after_by_local_authority=draw(st.sampled_from([False, True, True])),
        receives_benefits_in_own_right=draw(st.sampled_from([False, False, True])),
    )
    if draw(OVERNIGHT):
        person["dla_sc_middle_plus"] = True
        person["has_non_resident_overnight_carer"] = True
    return person


def without_overnight_care(person):
    return {
        k: v
        for k, v in person.items()
        if k not in ("dla_sc_middle_plus", "has_non_resident_overnight_carer")
    }


@st.composite
def scenario(draw):
    population = draw(st.lists(household(), min_size=1, max_size=4))
    h = draw(st.integers(0, len(population) - 1))
    f = draw(st.integers(0, len(population[h]) - 1))
    person = draw(young_person())
    # On some draws the person added to the head's family heads the household
    # in place of its first adult, whose claimant role does not change.
    if f == 0:
        person["is_household_head"] = draw(st.booleans())
    return population, (h, f), person


@st.composite
def child_scenario(draw, kinds):
    population = draw(st.lists(household(), min_size=1, max_size=4))
    h = draw(st.integers(0, len(population) - 1))
    f = draw(st.integers(0, len(population[h]) - 1))
    added = (
        draw(st.integers(0, 15)),
        draw(st.booleans()),
        draw(st.sampled_from(kinds)),
        False,
    )
    return population, (h, f), added


def child_inputs(age, male, kind, overnight):
    inputs = {"age": age, "is_male": male, "is_household_head": False}
    if kind == "foster":
        inputs["is_looked_after_by_local_authority"] = True
    if kind == "adopted":
        inputs["is_placed_for_adoption"] = True
    if overnight:
        inputs["dla_sc_middle_plus"] = True
        inputs["has_non_resident_overnight_carer"] = True
    return inputs


def build(population, added=None, supply_roles=True, added_child=None):
    """One situation for the population, optionally with a person aged 16 to
    19 added to family ``added[0]`` = (household, family) with attributes
    ``added[1]``, or a child ``added_child[1]`` = (age, is_male, kind,
    overnight) added to family ``added_child[0]``.

    Returns the situation and, per benefit unit, its (household, family).
    An added person with ``is_household_head`` heads the household in place
    of the head family's first adult."""
    people, benunits, homes, keys = {}, {}, {}, []
    for h, families in enumerate(population):
        members = []
        for f, fam in enumerate(families):
            name = f"h{h}_f{f}"
            ids = []
            for i, (age, overnight) in enumerate(fam["adults"]):
                pid = f"{name}_adult_{i}"
                people[pid] = {"age": age, "is_household_head": False}
                if overnight:
                    people[pid]["dla_sc_middle_plus"] = True
                    people[pid]["has_non_resident_overnight_carer"] = True
                if supply_roles:
                    people[pid]["is_claimant_or_partner"] = True
                elif fam["children"]:
                    people[pid]["is_parent"] = True
                ids.append(pid)
            if fam["between_placements"]:
                people[ids[0]]["is_approved_foster_parent_without_placement"] = True
            children = list(fam["children"])
            if added_child is not None and added_child[0] == (h, f):
                children.append(added_child[1])
            for i, spec in enumerate(children):
                pid = f"{name}_child_{i}"
                people[pid] = child_inputs(*spec)
                if supply_roles:
                    people[pid]["is_claimant_or_partner"] = False
                ids.append(pid)
            added_head = False
            if added is not None and added[0] == (h, f):
                pid = f"{name}_added"
                added_head = added[1].get("is_household_head", False)
                people[pid] = {**added[1], "is_household_head": added_head}
                if supply_roles:
                    people[pid]["is_claimant_or_partner"] = False
                ids.append(pid)
            extra = {}
            if fam["role"] == "sharer":
                extra["liable_for_share_of_household_rent"] = True
            if fam["role"] in ("boarder", "lodger"):
                people[ids[0]][f"rent_paid_as_{fam['role']}"] = 5_000
            if fam["role"] == "head" and not added_head:
                people[ids[0]]["is_household_head"] = True
            benunits[name] = {"members": ids, **extra}
            members.extend(ids)
            keys.append((h, f))
        homes[f"h{h}"] = {
            "members": members,
            "rent": 12_000,
            "tenure_type": "RENT_PRIVATELY",
            "brma": "MAIDSTONE",
        }
    situation = {"people": people, "benunits": benunits, "households": homes}
    return situation, keys


def bedrooms(situation):
    sim = Simulation(situation=situation)
    uc = np.asarray(sim.calculate("LHA_allowed_bedrooms", YEAR))
    hb = np.asarray(sim.calculate("housing_benefit_LHA_allowed_bedrooms", YEAR))
    return sim, uc, hb


def claim_roles(sim):
    """Per benefit unit: whether it counts the household's non-dependants
    for Universal Credit, and whether it is liable for the household's
    rent."""
    counted = np.asarray(sim.calculate("uc_non_dependants_counted", YEAR))
    liable = (
        np.asarray(
            sim.calculate("is_liable_for_household_rent", YEAR, map_to="benunit")
        )
        > 0
    )
    return counted.astype(bool), liable


def own_claims(sim):
    """Per benefit unit: whether it makes its own Universal Credit claim as a
    renter, the test uc_non_dep_deductions applies to an in-unit
    non-dependant's family."""
    return (
        np.asarray(sim.calculate("benunit_is_rent_liable", YEAR))
        & np.asarray(sim.calculate("is_uc_eligible", YEAR))
        & np.asarray(sim.calculate("claims_universal_credit", YEAR))
    )


def fewest_rooms_for_children(children):
    """Brute force: the fewest rooms holding the children two to a room,
    where a pair must be of the same sex or both under 10."""

    def can_share(a, b):
        return a[1] == b[1] or (a[0] < 10 and b[0] < 10)

    def best(remaining):
        if not remaining:
            return 0
        first, rest = remaining[0], remaining[1:]
        rooms = 1 + best(rest)
        for j, other in enumerate(rest):
            if can_share(first, other):
                rooms = min(rooms, 1 + best(rest[:j] + rest[j + 1 :]))
        return rooms

    return best(list(children))


def fosters(fam):
    """Whether the family meets the foster parent condition (UC) or has a
    qualifying parent or carer (HB) through its children or adults."""
    return fam["between_placements"] or any(
        kind in ("foster", "adopted") for _, _, kind, _ in fam["children"]
    )


def in_qualifying_education(p, age_limit_for_entry=19):
    """Full-time non-advanced education (any education short of tertiary),
    entered before 19."""
    return p["current_education"] not in ("NOT_IN_EDUCATION", "TERTIARY") and (
        p["age"] < age_limit_for_entry
        or p["age_started_or_accepted_current_education_or_training"]
        < age_limit_for_entry
    )


def uc_qualifying_young_person(p):
    """UC Regs 2013 reg 5: aged 16 to 19, in non-advanced education entered
    before 19, before the terminal date if 19, and not receiving benefits in
    their own right."""
    return (
        16 <= p["age"] < 20
        and in_qualifying_education(p)
        and (
            p["age"] < 19
            or p["is_before_universal_credit_qualifying_young_person_terminal_date"]
        )
        and not p["receives_benefits_in_own_right"]
    )


def child_benefit_qualifying_young_person(p):
    """SSCBA 1992 s.142 and the Child Benefit (General) Regulations 2006, as
    HB reg 19's "young person": aged 16 to 19 in non-advanced education
    entered before 19, and not receiving benefits in their own right."""
    return (
        16 <= p["age"] < 20
        and in_qualifying_education(p)
        and not p["receives_benefits_in_own_right"]
    )


def flags(p):
    """The added person's status, from the inputs alone."""
    # Only a person under 18 can be looked after (Children Act 1989 s.105).
    looked_after = p.get("is_looked_after_by_local_authority", False) and p["age"] < 18
    qualifying = uc_qualifying_young_person(p)
    head = p.get("is_household_head", False)
    return dict(
        # A qualifying young person no one is responsible for (UC para
        # 9(2)(g); reg 4(6)(a)).
        unclaimed=looked_after and qualifying,
        # The family's foster child: looked after and under 18 (UC reg 2,
        # "foster parent"; para 9(3)).
        fostered=looked_after,
        # A UC bedroom of their own: a qualifying young person the renter is
        # responsible for (para 10(1)(b)), or a non-dependant (para
        # 10(1)(c)) who neither heads the household (para 9(2)(d)) nor is a
        # foster child (para 9(2)(c)).
        own_uc_room=not looked_after and (qualifying or not head),
        # Placed with the family by a local authority (HB reg 21(3)).
        placed=looked_after and child_benefit_qualifying_young_person(p),
        overnight=p.get("has_non_resident_overnight_carer", False),
    )


@PROPERTY_SETTINGS
@given(scenario(), st.booleans())
def test_adding_a_person_aged_16_to_19_never_lowers_bedrooms(case, supply_roles):
    population, target, person = case
    before, keys = build(population, supply_roles=supply_roles)
    after, keys_after = build(population, (target, person), supply_roles)
    assert keys == keys_after
    _, uc_before, hb_before = bedrooms(before)
    _, uc_after, hb_after = bedrooms(after)
    # 1. Monotonicity.
    assert np.all(uc_after >= uc_before)
    assert np.all(hb_after >= hb_before)


LOOKED_AFTER_QYP = dict(
    age=17,
    is_male=True,
    current_education="UPPER_SECONDARY",
    age_started_or_accepted_current_education_or_training=16,
    is_before_universal_credit_qualifying_young_person_terminal_date=True,
    is_looked_after_by_local_authority=True,
    receives_benefits_in_own_right=False,
)


def lone(role, age):
    return dict(role=role, adults=[(age, False)], children=[], between_placements=False)


@PROPERTY_SETTINGS
@given(scenario())
# A qualifying young person a local authority looks after, added to the
# head's family: no Universal Credit bedroom (para 9(2)(g)).
@example(([[lone("head", 40)]], (0, 0), LOOKED_AFTER_QYP))
# The same young person in a non-dependant's family: no Universal Credit
# bedroom in the renter's claim either (para 9(2)(g)).
@example(([[lone("head", 40), lone("non_dependant", 45)]], (0, 1), LOOKED_AFTER_QYP))
# A sharer's looked-after 17-year-old not in education: the head's claim,
# which counts the household's non-dependants, gains their bedroom and so
# has a non-dependant (para 28(4)).
@example(
    (
        [[lone("head", 30), lone("sharer", 40)]],
        (0, 1),
        dict(LOOKED_AFTER_QYP, current_education="NOT_IN_EDUCATION"),
    )
)
# A 19-year-old not in education in the family of a sharer over State
# Pension age, which makes no Universal Credit claim: the head's claim
# gains their bedroom and so has a non-dependant.
@example(
    (
        [[lone("head", 30), lone("sharer", 70)]],
        (0, 1),
        dict(
            LOOKED_AFTER_QYP,
            age=19,
            current_education="NOT_IN_EDUCATION",
            is_before_universal_credit_qualifying_young_person_terminal_date=False,
            is_looked_after_by_local_authority=False,
        ),
    )
)
def test_exact_effect_of_adding_a_person_aged_16_to_19(case):
    population, target, person = case
    person = without_overnight_care(person)
    before, keys = build(population)
    after, _ = build(population, (target, person))
    sim_before, uc_before, hb_before = bedrooms(before)
    sim, uc_after, hb_after = bedrooms(after)
    counted, liable = claim_roles(sim)
    # Adding a dependant changes neither who counts the non-dependants nor
    # who is liable for the rent.
    counted_before, liable_before = claim_roles(sim_before)
    assert np.array_equal(counted, counted_before)
    assert np.array_equal(liable, liable_before)
    added = flags(person)
    fam = population[target[0]][target[1]]
    names = list(after["people"])
    marked = in_unit_non_dependants(sim)[
        names.index(f"h{target[0]}_f{target[1]}_added")
    ]
    # 2. Exact effect.
    expected_uc = np.zeros(len(keys))
    expected_hb = np.zeros(len(keys))
    t = keys.index(target)
    expected_uc[t] += int(added["own_uc_room"])
    expected_uc[t] += int(added["fostered"] and not fosters(fam))
    expected_hb[t] += 0 if added["placed"] else 1
    expected_hb[t] += int(added["placed"] and not fosters(fam))
    same_household = np.array([h == target[0] for h, _ in keys])
    passed_on = (
        fam["role"] != "non_dependant"
        and marked
        and not own_claims(sim)[t]
        and not counted[t]
    )
    # A foster child who is not a qualifying young person is out of their
    # foster parent's extended benefit unit only (para 9(2)(c)).
    fostered_on = (
        fam["role"] != "non_dependant"
        and added["fostered"]
        and not added["unclaimed"]
        and not person.get("is_household_head", False)
        and not counted[t]
    )
    if (
        (fam["role"] == "non_dependant" and not added["unclaimed"])
        or passed_on
        or fostered_on
    ):
        expected_uc[same_household & counted] += 1
    if fam["role"] in OCCUPIER_ROLES:
        expected_hb[same_household & liable] += 1
    assert np.array_equal(uc_after - uc_before, expected_uc)
    assert np.array_equal(hb_after - hb_before, expected_hb)
    # 3. A bedroom another family's person gives the counting claim is a
    # non-dependant's, so that claim's renter is no specified renter (UC
    # Sch 4 para 28(4)).
    has_non_dependant = np.asarray(
        sim.calculate("lha_renter_has_non_dependant", YEAR)
    ).astype(bool)
    gained = (uc_after > uc_before) & same_household & counted
    gained[t] = False
    assert has_non_dependant[gained].all()


@PROPERTY_SETTINGS
@given(child_scenario(["own"]))
def test_adding_a_child_raises_each_family_by_at_most_one_bedroom(case):
    population, target, added_child = case
    before, keys = build(population)
    after, _ = build(population, added_child=(target, added_child))
    _, uc_before, hb_before = bedrooms(before)
    _, uc_after, hb_after = bedrooms(after)
    # 3. Children.
    for change in (uc_after - uc_before, hb_after - hb_before):
        assert np.all((change == 0) | (change == 1))


@PROPERTY_SETTINGS
@given(child_scenario(["foster", "adopted"]))
def test_a_placed_child_adds_the_carers_bedroom(case):
    population, target, added_child = case
    before, keys = build(population)
    after, _ = build(population, added_child=(target, added_child))
    sim, uc_before, hb_before = bedrooms(before)
    _, uc_after, hb_after = bedrooms(after)
    counted, liable = claim_roles(sim)
    # 4. Placed children.
    fam = population[target[0]][target[1]]
    t = keys.index(target)
    new_carer = int(not fosters(fam))
    expected = np.zeros(len(keys))
    expected[t] = new_carer
    same_household = np.array([h == target[0] for h, _ in keys])
    # Under Housing Benefit the child occupies the dwelling of each family
    # liable for the rent if placed with a non-dependant, boarder or lodger.
    hb_child_room = np.zeros(len(keys), dtype=bool)
    if fam["role"] in OCCUPIER_ROLES:
        hb_child_room = same_household & liable
    hb_extra = hb_after - hb_before - expected
    assert np.all((hb_extra == 0) | ((hb_extra == 1) & hb_child_room))
    uc_change = uc_after - uc_before
    if added_child[2] == "foster":
        assert np.array_equal(uc_change, expected)
    else:
        # The adopter's child counts as a child (reg 4A(1)(c)), in the
        # adopter's family and, for a non-dependant adopter, in the claim
        # counting the household's non-dependants.
        child_room = np.zeros(len(keys), dtype=bool)
        child_room[t] = True
        if fam["role"] == "non_dependant":
            child_room |= same_household & counted
        extra = uc_change - expected
        assert np.all((extra == 0) | ((extra == 1) & child_room))


@PROPERTY_SETTINGS
@given(scenario())
# A non-dependant's foster child who requires overnight care: the renter's
# Housing Benefit overnight room (reg 13D(3A)(a)(iii); reg 21(3)).
@example(
    (
        [
            [
                lone("head", 60),
                dict(
                    role="non_dependant",
                    adults=[(32, False)],
                    children=[(6, False, "foster", True)],
                    between_placements=False,
                ),
            ]
        ],
        (0, 0),
        dict(LOOKED_AFTER_QYP, is_looked_after_by_local_authority=False),
    )
)
def test_bedrooms_match_a_reference_count_of_the_size_criteria(case):
    population, target, person = case
    situation, keys = build(population, (target, person))
    sim, uc, hb = bedrooms(situation)
    counted, liable = claim_roles(sim)
    uc_additional = np.asarray(sim.calculate("LHA_additional_bedrooms", YEAR))
    hb_additional = np.asarray(
        sim.calculate("housing_benefit_LHA_additional_bedrooms", YEAR)
    )
    added = flags(person)
    own_claim = own_claims(sim)
    names = list(situation["people"])
    marked = in_unit_non_dependants(sim)
    # 5. Reference count.
    for b, (h, f) in enumerate(keys):
        families = population[h]
        fam = families[f]
        is_target = (h, f) == target
        # Own members aged 16 or over who are not the claimant or partner.
        uc_rooms = 1 + int(is_target and added["own_uc_room"])
        hb_rooms = 1 + int(is_target and not added["placed"])
        # Children: UC counts the children the family is responsible for
        # (not foster children); HB counts occupiers (not children placed
        # with the family as foster children or for adoption).
        uc_children = [c for c in fam["children"] if c[2] != "foster"]
        hb_children = [c for c in fam["children"] if c[2] == "own"]
        # Overnight care: the family's own members, including a foster
        # child (UC para 12(A1)(c); HB 13D(3A)(a)(iv)).
        uc_overnight = hb_overnight = any(o for _, o in fam["adults"]) or any(
            c[3] for c in fam["children"]
        )
        if is_target and added["overnight"]:
            uc_overnight |= added["fostered"] or not added["unclaimed"]
            hb_overnight = True
        uc_foster = fosters(fam) or (is_target and added["fostered"])
        hb_carer = fosters(fam) or (is_target and added["placed"])
        for g, other in enumerate(families):
            if g == f:
                continue
            joins = target == (h, g)
            if counted[b] and other["role"] == "non_dependant":
                uc_rooms += len(other["adults"]) + int(joins and not added["unclaimed"])
                uc_children += [c for c in other["children"] if c[2] != "foster"]
                uc_overnight |= any(o for _, o in other["adults"]) or any(
                    c[3] for c in other["children"] if c[2] != "foster"
                )
                uc_overnight |= joins and added["overnight"] and not added["unclaimed"]
            elif counted[b] and joins:
                # UC: an in-unit non-dependant of a family that makes no
                # claim of its own (para 9(2)(f)), and another family's
                # foster child who is not a qualifying young person (para
                # 9(2)(c)), count in this claim.
                passed_on = (
                    marked[names.index(f"h{h}_f{g}_added")]
                    and not own_claim[keys.index((h, g))]
                ) or (
                    added["fostered"]
                    and not added["unclaimed"]
                    and not person.get("is_household_head", False)
                )
                uc_rooms += int(passed_on)
                uc_overnight |= bool(passed_on and added["overnight"])
            if liable[b] and other["role"] in OCCUPIER_ROLES:
                # HB reg 13D(3)(a), (b): the occupier family's couple or
                # single adult has one bedroom, and the added person one.
                # Reg 21(3) takes out only a child placed with the claimant
                # or partner, so every child of the family counts.
                hb_rooms += 1 + int(joins)
                hb_children += other["children"]
                hb_overnight |= any(o for _, o in other["adults"]) or any(
                    c[3] for c in other["children"]
                )
                hb_overnight |= joins and added["overnight"]
        expected_uc_additional = int(uc_overnight) + int(uc_foster)
        expected_hb_additional = int(hb_overnight) + int(hb_carer)
        assert uc_additional[b] == expected_uc_additional
        assert hb_additional[b] == expected_hb_additional
        assert uc[b] == (
            uc_rooms
            + fewest_rooms_for_children([c[:2] for c in uc_children])
            + expected_uc_additional
        )
        assert hb[b] == (
            hb_rooms
            + fewest_rooms_for_children([c[:2] for c in hb_children])
            + expected_hb_additional
        )


def in_unit_non_dependants(sim):
    """Each person: aged 16 or over, neither the claimant nor partner, not a
    Universal Credit qualifying young person, not the household head (UC
    Regs 2013 Sch 4 para 9(2), with (d) for the head, the householder in
    whose name the accommodation is rented) and not the family's foster
    child (para 9(2)(c)). Checks that the model's
    is_benefit_unit_non_dependant_for_universal_credit marks the same
    people."""
    age = np.asarray(sim.calculate("age", YEAR))
    claimant_or_partner = np.asarray(sim.calculate("is_claimant_or_partner", YEAR))
    qualifying = np.asarray(
        sim.calculate("is_qualifying_young_person_for_universal_credit", YEAR)
    )
    household_head = np.asarray(sim.calculate("is_resolved_household_head", YEAR))
    foster_child = np.asarray(sim.calculate("is_lha_foster_child", YEAR))
    marked = (
        (age >= 16)
        & ~claimant_or_partner
        & ~qualifying
        & ~household_head
        & ~foster_child
    )
    model = np.asarray(
        sim.calculate("is_benefit_unit_non_dependant_for_universal_credit", YEAR)
    )
    assert np.array_equal(marked, model)
    return marked


@PROPERTY_SETTINGS
@given(scenario())
def test_every_in_unit_non_dependant_has_a_bedroom(case):
    population, target, person = case
    person = without_overnight_care(person)
    situation, keys = build(population, (target, person))
    sim, uc, _ = bedrooms(situation)
    marked = in_unit_non_dependants(sim)
    names = list(situation["people"])
    # 6. A marked member has a bedroom of their own: without them, their
    # family has one fewer, and so does the claim counting the household's
    # non-dependants if they are in a non-dependant's family, or in a family
    # that neither makes its own claim nor is that claim. Only the added
    # person can be marked: the generated adults are claimants or partners
    # and the generated children are under 16.
    if marked[names.index(f"h{target[0]}_f{target[1]}_added")]:
        without, _ = build(population)
        _, uc_without, _ = bedrooms(without)
        expected = np.zeros(len(keys))
        expected[keys.index(target)] = 1
        role = population[target[0]][target[1]]["role"]
        counted, _ = claim_roles(sim)
        t = keys.index(target)
        if role == "non_dependant" or not (own_claims(sim)[t] or counted[t]):
            same_household = np.array([h == target[0] for h, _ in keys])
            expected[same_household & counted] += 1
        assert np.array_equal(uc - uc_without, expected)
    # Making every marked member a qualifying young person the renter is
    # responsible for leaves every family's bedrooms unchanged, except that
    # the claim counting the household's non-dependants loses the bedroom of
    # one whose own family makes no claim and is not that claim: another
    # family's qualifying young person is not that renter's non-dependant
    # (para 9(2)(g)).
    expected_change = np.zeros(len(keys))
    if marked[names.index(f"h{target[0]}_f{target[1]}_added")]:
        counted, _ = claim_roles(sim)
        t = keys.index(target)
        role = population[target[0]][target[1]]["role"]
        if role != "non_dependant" and not (own_claims(sim)[t] or counted[t]):
            same_household = np.array([h == target[0] for h, _ in keys])
            expected_change[same_household & counted] = -1
    as_dependants = {
        **situation,
        "people": {
            name: (
                {
                    **attributes,
                    "is_qualifying_young_person_for_universal_credit": True,
                    "is_looked_after_by_local_authority": False,
                }
                if marked[i]
                else attributes
            )
            for i, (name, attributes) in enumerate(situation["people"].items())
        },
    }
    sim_as_dependants, uc_as_dependants, _ = bedrooms(as_dependants)
    assert not in_unit_non_dependants(sim_as_dependants).any()
    assert np.array_equal(uc_as_dependants - uc, expected_change)


def as_close_relative_adopters(situation):
    return {
        **situation,
        "people": {
            name: {**attributes, "adopter_is_foster_parent_or_close_relative": True}
            for name, attributes in situation["people"].items()
        },
    }


@PROPERTY_SETTINGS
@given(scenario())
def test_a_close_relative_adopter_loses_only_the_foster_room(case):
    population, target, person = case
    situation, keys = build(population, (target, person))
    added = flags(person)
    outputs = []
    for variant in (situation, as_close_relative_adopters(situation)):
        sim, uc, hb = bedrooms(variant)
        outputs.append(
            dict(
                uc=uc,
                hb=hb,
                foster=np.asarray(
                    sim.calculate("lha_renter_meets_foster_parent_condition", YEAR)
                ),
                **{
                    name: np.asarray(sim.calculate(name, YEAR))
                    for name in (
                        "is_child_or_qualifying_young_person_for_universal_credit",
                        "is_child_or_young_person_placed_with_family",
                        "is_housing_benefit_qualifying_parent_or_carer",
                        "housing_benefit_LHA_additional_bedrooms",
                    )
                },
            )
        )
    before, after = outputs
    # 7. The foster parent condition without the adoption route: a foster
    # child, an approved foster parent between placements, or the added
    # person placed as a foster child.
    expected_foster = np.array(
        [
            population[h][f]["between_placements"]
            or any(c[2] == "foster" for c in population[h][f]["children"])
            or ((h, f) == target and added["fostered"])
            for h, f in keys
        ]
    )
    assert np.array_equal(after["foster"], expected_foster)
    lost = before["foster"] & ~after["foster"]
    assert np.array_equal(before["uc"] - after["uc"], lost.astype(float))
    assert np.array_equal(before["hb"], after["hb"])
    for name in before:
        if name not in ("uc", "hb", "foster"):
            assert np.array_equal(before[name], after[name])


@st.composite
def adult_member(draw):
    """A member aged 16 or over who is not in education, with or without
    Attendance Allowance (an exemption under UC Regs 2013 Sch 4 para 16(2)).
    Outside education, UC reg 5(1)(a) makes them a qualifying young person
    only before the 1 September after their 16th birthday."""
    return dict(
        age=draw(st.integers(16, 64)),
        is_male=draw(st.booleans()),
        current_education="NOT_IN_EDUCATION",
        is_looked_after_by_local_authority=False,
        attendance_allowance=draw(st.sampled_from([0, 5_000])),
    )


@st.composite
def adult_scenario(draw):
    population = draw(st.lists(household(), min_size=1, max_size=3))
    h = draw(st.integers(0, len(population) - 1))
    f = draw(st.integers(0, len(population[h]) - 1))
    # Whether each family would claim Universal Credit, so that the claim
    # bearing a non-dependant is sometimes not their own family's.
    would_claim = [[draw(st.booleans()) for _ in families] for families in population]
    return population, (h, f), draw(adult_member()), would_claim


def with_claim_flags(situation, would_claim):
    for name, unit in situation["benunits"].items():
        if name.startswith("h") and "_f" in name:
            h, f = name[1:].split("_f")
            unit["would_claim_uc"] = would_claim[int(h)][int(f)]
    return situation


def in_own_benefit_unit(population, target, person, would_claim):
    """The population with ``person`` in a benefit unit of their own, in the
    household of family ``target``, not claiming Universal Credit. Invariant 9
    covers people aged 20 or over."""
    assume(person["age"] >= 20)
    situation, keys = build(population)
    situation = with_claim_flags(situation, would_claim)
    h = target[0]
    situation["people"]["moved"] = {
        **person,
        "is_household_head": False,
        "is_claimant_or_partner": True,
    }
    situation["benunits"]["moved"] = {"members": ["moved"], "would_claim_uc": False}
    situation["households"][f"h{h}"]["members"].append("moved")
    return situation, keys


def claim_and_contributions(situation):
    sim = Simulation(situation=situation)

    def calc(variable):
        return np.asarray(sim.calculate(variable, YEAR))

    own_claim = (
        calc("benunit_is_rent_liable")
        & calc("is_uc_eligible")
        & calc("claims_universal_credit")
    )
    return sim, calc, own_claim


@PROPERTY_SETTINGS
@given(adult_scenario())
def test_every_in_unit_non_dependant_with_a_room_owes_a_contribution(case):
    population, target, person, would_claim = case
    before, keys = build(population)
    after, _ = build(population, (target, person))
    before = with_claim_flags(before, would_claim)
    after = with_claim_flags(after, would_claim)
    sim_before, calc_before, own_claim_before = claim_and_contributions(before)
    sim, calc, own_claim = claim_and_contributions(after)
    counted = calc("uc_non_dependants_counted")
    assert np.array_equal(own_claim, own_claim_before)
    assert np.array_equal(counted, calc_before("uc_non_dependants_counted"))
    # 8. Nobody owes a contribution without being a non-dependant (Sch 4
    # para 9(2) and para 13).
    owes = calc("uc_individual_non_dep_deduction") > 0
    non_dependant = calc("is_benefit_unit_non_dependant_for_universal_credit") | calc(
        "is_non_dependant_of_household_head"
    )
    assert not np.any(owes & ~non_dependant)
    names = list(after["people"])
    i = names.index(f"h{target[0]}_f{target[1]}_added")
    in_unit = calc("is_benefit_unit_non_dependant_for_universal_credit")[i]
    head = calc("is_resolved_household_head")[i]
    # The added member is never a claimant. Outside education, they count as
    # a qualifying young person only before the 1 September after their 16th
    # birthday (UC reg 5(1)(a)), which the formula reads.
    qualifying = calc("is_qualifying_young_person_for_universal_credit")[i]
    assert in_unit == (person["age"] >= 16 and not head and not qualifying)
    if not in_unit:
        return
    # An in-unit non-dependant owes a contribution unless aged under 21 or
    # receiving Attendance Allowance (para 16(2)(a), (2)(c)).
    p = sim.tax_benefit_system.parameters(
        YEAR
    ).gov.dwp.universal_credit.elements.housing.non_dep_deduction
    exempt = person["age"] < p.age_threshold or person["attendance_allowance"] > 0
    assert owes[i] == (not exempt)
    # The claim that bears them: their own family's if it makes one,
    # otherwise the one counting the household's non-dependants.
    b = keys.index(target)
    role = population[target[0]][target[1]]["role"]
    same_household = np.array([h == target[0] for h, _ in keys])
    if own_claim[b] and role != "non_dependant":
        bearer = np.arange(len(keys)) == b
    else:
        bearer = same_household & counted.astype(bool)
    renter_exempt = calc("uc_non_dep_deductions_renter_exempt")
    expected = bearer * (not exempt) * ~renter_exempt * p.amount * 12
    delta = calc("uc_non_dep_deductions") - calc_before("uc_non_dep_deductions")
    assert np.allclose(delta, expected)
    # The claim that bears the contribution also has their bedroom.
    rooms = calc("LHA_allowed_bedrooms") - calc_before("LHA_allowed_bedrooms")
    assert np.all(rooms[bearer] == 1)


@PROPERTY_SETTINGS
@given(adult_scenario())
# A claiming sharer's family bears the adult, whom the head's claim counts
# once they have a benefit unit of their own.
@example(
    (
        [
            [
                dict(
                    role="head",
                    adults=[(59, False), (20, False)],
                    children=[],
                    between_placements=False,
                ),
                dict(
                    role="sharer",
                    adults=[(59, False), (66, False)],
                    children=[],
                    between_placements=False,
                ),
            ]
        ],
        (0, 1),
        dict(
            age=57,
            is_male=False,
            current_education="NOT_IN_EDUCATION",
            is_looked_after_by_local_authority=False,
            attendance_allowance=0,
        ),
        [[True, True]],
    )
)
def test_moving_a_non_claiming_adult_out_of_the_benefit_unit_changes_no_claim(case):
    population, target, person, would_claim = case
    inside, keys = build(population, (target, person))
    inside = with_claim_flags(inside, would_claim)
    outside, _ = in_own_benefit_unit(population, target, person, would_claim)
    _, calc_in, own_claim_in = claim_and_contributions(inside)
    _, calc_out, own_claim_out = claim_and_contributions(outside)
    n = len(keys)
    # The household head's family keeps its claim either way.
    assert np.array_equal(own_claim_in, own_claim_out[:n])
    counted = calc_in("uc_non_dependants_counted").astype(bool)
    assert np.array_equal(counted, calc_out("uc_non_dependants_counted")[:n] > 0)
    # 9. In their family, the family's own claim bears the adult if it makes
    # one (invariant 8); in a benefit unit of their own, the claim that counts
    # the household's non-dependants bears them. Where those claims differ,
    # the adult's bedroom moves from the first to the second.
    t = keys.index(target)
    role = population[target[0]][target[1]]["role"]
    counting = np.array([h == target[0] for h, _ in keys]) & counted
    moves = own_claim_in[t] and role != "non_dependant" and not counted[t]
    changed = np.zeros(n, dtype=bool)
    if moves:
        changed[t] = True
        changed |= counting
        rooms_in = calc_in("LHA_allowed_bedrooms")
        rooms_out = calc_out("LHA_allowed_bedrooms")[:n]
        assert rooms_in[t] == rooms_out[t] + 1
        assert np.all(rooms_out[counting] == rooms_in[counting] + 1)
    # Every other family making a claim keeps its bedrooms, contribution and
    # award whether the adult is coded in a benefit unit or in their own.
    keep = own_claim_in & ~changed
    for variable in (
        "LHA_allowed_bedrooms",
        "uc_non_dep_deductions",
        "universal_credit",
    ):
        a = calc_in(variable)[keep]
        b = calc_out(variable)[:n][keep]
        assert np.allclose(a, b), variable
