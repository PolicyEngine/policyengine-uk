"""Property-based tests for the LHA size criteria (UC Regs 2013 Sch 4 paras
9-12; HB Regs 2006 and HB (SPC) Regs 2006 reg 13D and reg 21(3)): the
bedrooms of benefit-unit members aged 16 or over who are not the claimant or
partner, the children of other families in the household, foster and
adoption placements, and the additional bedrooms for foster parents and
overnight care.

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
   model; which claim counts the non-dependants, and which families are
   liable for the rent, are read from the model and tested elsewhere.
   Children's rooms come from a brute-force pairing. The count applies the
   same legal readings as the model, so it checks the implementation of
   those readings, not the readings themselves:
   - one for the claimant or couple;
   - one for each other member aged 16 or over (UC: except a qualifying
     young person no one is responsible for, a foster child under 18 and a
     household head who is not a qualifying young person; HB: except one
     placed with the family as a foster child);
   - for the claim counting the non-dependants (UC), one for each person
     aged 16 or over in a non-dependant's family, except one no one is
     responsible for; for a family liable for the rent (HB), one for the
     couple or single adult of each non-dependant's, boarder's or lodger's
     family and one for each other member aged 16 or over, including one
     placed with that family;
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
   qualifying young person nor the household head nor the family's foster
   child is a non-dependant (para 9(2)) with a bedroom (para 10(1)(c)). So
   their family has one more Universal Credit bedroom with them than
   without them, and making them qualifying young persons the renter is
   responsible for (para 10(1)(b)) leaves every family's Universal Credit
   bedrooms unchanged.
7. Close-relative adopters: marking every child's adopter as a foster
   parent or close relative of the child (UC reg 89(3)(a)) takes away the
   foster parent condition exactly where an adoption placement was the
   family's only route to it (para 12(4)(b)); it lowers that family's
   Universal Credit bedrooms by one and changes nothing else: Universal
   Credit responsibility (reg 4A(1)(c)), the Housing Benefit placement test
   (reg 21(3)), the qualifying parent or carer and every family's Housing
   Benefit bedrooms stay the same.
"""

import numpy as np
from hypothesis import HealthCheck, example, given, settings
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
    # 2. Exact effect.
    expected_uc = np.zeros(len(keys))
    expected_hb = np.zeros(len(keys))
    t = keys.index(target)
    expected_uc[t] += int(added["own_uc_room"])
    expected_uc[t] += int(added["fostered"] and not fosters(fam))
    expected_hb[t] += 0 if added["placed"] else 1
    expected_hb[t] += int(added["placed"] and not fosters(fam))
    same_household = np.array([h == target[0] for h, _ in keys])
    if fam["role"] == "non_dependant" and not added["unclaimed"]:
        expected_uc[same_household & counted] += 1
    if fam["role"] in OCCUPIER_ROLES:
        expected_hb[same_household & liable] += 1
    assert np.array_equal(uc_after - uc_before, expected_uc)
    assert np.array_equal(hb_after - hb_before, expected_hb)


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
    child (para 9(2)(c))."""
    age = np.asarray(sim.calculate("age", YEAR))
    claimant_or_partner = np.asarray(sim.calculate("is_claimant_or_partner", YEAR))
    qualifying = np.asarray(
        sim.calculate("is_qualifying_young_person_for_universal_credit", YEAR)
    )
    household_head = np.asarray(sim.calculate("is_resolved_household_head", YEAR))
    foster_child = np.asarray(sim.calculate("is_lha_foster_child", YEAR))
    return (
        (age >= 16)
        & ~claimant_or_partner
        & ~qualifying
        & ~household_head
        & ~foster_child
    )


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
    # non-dependants if they are in a non-dependant's family. Only the added
    # person can be marked: the generated adults are claimants or partners
    # and the generated children are under 16.
    if marked[names.index(f"h{target[0]}_f{target[1]}_added")]:
        without, _ = build(population)
        _, uc_without, _ = bedrooms(without)
        expected = np.zeros(len(keys))
        expected[keys.index(target)] = 1
        if population[target[0]][target[1]]["role"] == "non_dependant":
            counted, _ = claim_roles(sim)
            same_household = np.array([h == target[0] for h, _ in keys])
            expected[same_household & counted] += 1
        assert np.array_equal(uc - uc_without, expected)
    # Making every marked member a qualifying young person the renter is
    # responsible for leaves every family's bedrooms unchanged.
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
    assert np.array_equal(uc, uc_as_dependants)


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
