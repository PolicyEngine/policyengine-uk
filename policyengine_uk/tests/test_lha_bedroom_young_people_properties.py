"""Property-based tests for the LHA size criteria (UC Regs 2013 Sch 4 paras
9-12; HB Regs 2006 and HB (SPC) Regs 2006 reg 13D and reg 21(3)): the
bedrooms of benefit-unit members aged 16 or over who are not the claimant or
partner, the children of other families in the household, foster and
adoption placements, the additional bedrooms for foster parents and
overnight care, and the bedrooms for children and couples who cannot share
a bedroom because of disability.

Invariants, for any generated population of households:

1. Monotonicity: adding a person aged 16 to 19 to any family never lowers
   any family's Universal Credit or Housing Benefit bedrooms, whether the
   claimant and partner are supplied or inferred.
2. Exact effect of a person aged 16 to 19: when the added person is not the
   claimant or partner, their family gains one Housing Benefit bedroom
   unless the person is placed with it as a foster child (HB reg 21(3)), and
   one Universal Credit bedroom unless they are a qualifying young person no
   one is responsible for (para 9(2)(g)) or the family's foster child (under
   18, para 9(2)(c)); a family they are placed with as a foster child gains
   the foster parent's (UC, para 12) or qualifying parent or carer's (HB,
   13D(3A)(b)) bedroom if it did not already have it. The household head's
   family also gains one bedroom under both schemes if the person joins a
   non-dependant's family (UC: unless no one is responsible for them; HB:
   unless placed with it), and one Housing Benefit bedroom if they join a
   boarder's or lodger's family (unless placed with it). No other family's
   bedrooms change.
3. Children: adding a child under 16 who is neither fostered nor placed for
   adoption to any family never lowers any family's bedrooms under either
   scheme and raises each by at most one.
4. Foster children: adding a foster child to a family gives that family one
   more bedroom under each scheme if it did not already meet the foster
   parent condition (UC) or have a qualifying parent or carer (HB), and none
   otherwise. No other family's bedrooms change under either scheme: a
   child placed with another family is not in the household head's
   extended benefit unit (UC para 9(2)(g)) and, following DWP, not an
   occupier (HB; LHA Guidance Manual para 2.033).
5. Reference: every family's bedrooms, and its additional bedrooms, equal a
   count of the size criteria made by the test itself. The added person's
   status comes from the test's own predicates on the inputs (UC reg 5
   qualifying young person, the Child Benefit qualifying young person for
   HB reg 19, looked after and under 18 for a foster child), not from the
   model, and children's rooms come from a brute-force pairing. The count
   applies the same legal readings as the model, including its judgment
   calls (see the PR), so it checks the implementation of those readings,
   not the readings themselves:
   - one for the claimant or couple;
   - one for each other member aged 16 or over (UC: except a qualifying
     young person no one is responsible for and a foster child under 18;
     HB: except one placed with the family as a foster child);
   - for the household head's family, one for each person aged 16 or over
     in a non-dependant's family (and, for HB, in a boarder's or lodger's
     family), except one no one is responsible for (UC) or placed with that
     family as a foster child (HB);
   - the fewest rooms that hold the counted children under 16 two to a
     room, where only children of the same sex or two children under 10 may
     share, found by brute force. UC counts the family's own children and,
     for the household head's family, the non-dependants' children, but no
     foster child. HB counts the children of the family and, for the
     household head's family, of a non-dependant's, boarder's or lodger's
     family, other than foster children and children placed for adoption;
   - one additional bedroom if anyone so counted, or a foster child of the
     family, has overnight care, and one if the family fosters, has a child
     placed for adoption, or has an approved foster parent between
     placements;
   - children who cannot share a bedroom because of disability: the brute
     force forbids them any room-mate, and the difference from the
     unrestricted pairing is additional (UC para 12(6), (8); HB reg
     13D(3)(ba));
   - couples one of whom cannot share: one more bedroom for the family's own
     couple (UC para 12(6A), (9)(d); HB 13D(3)(za)-(zb)) and, under HB, for
     each occupier couple of a non-dependant's, boarder's or lodger's family
     counted by the household head's family;
   - under HB, the bedrooms for people who cannot share count only so far
     as the dwelling's reported bedrooms exceed the count if everyone could
     share (reg 13D(3), closing words); unreported (0) means no limit.
6. A child who cannot share: flagging one more child under 16 as unable to
   share (with a qualifying benefit) raises any family's bedrooms by nothing
   or one under each scheme, and changes only the families whose size
   criteria count that child.
7. The dwelling's bedrooms: with them reported, every family's Housing
   Benefit bedrooms lie between the count if everyone could share and the
   count with them unreported, and exceed the dwelling's bedrooms only
   where the count if everyone could share already does.
"""

from itertools import combinations

import numpy as np
from hypothesis import HealthCheck, given, settings
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
EDUCATION = ["NOT_IN_EDUCATION", "UPPER_SECONDARY", "UPPER_SECONDARY", "TERTIARY"]
KINDS = ["own", "own", "own", "foster", "adopted"]
OVERNIGHT = st.sampled_from([False, False, False, True])
CANNOT_SHARE = st.sampled_from([False, False, False, True])

# (age, is_male, kind, has overnight care, cannot share a bedroom)
child = st.tuples(
    st.integers(0, 15),
    st.booleans(),
    st.sampled_from(KINDS),
    OVERNIGHT,
    CANNOT_SHARE,
)


@st.composite
def family(draw, role):
    return dict(
        role=role,
        adults=draw(
            st.lists(st.tuples(st.integers(20, 85), OVERNIGHT), min_size=1, max_size=2)
        ),
        children=draw(st.lists(child, min_size=0, max_size=4)),
        between_placements=draw(st.sampled_from([False, False, False, True])),
        # How many adults, from the first, cannot share a bedroom with a
        # partner because of disability (this matters only for two adults).
        couple_cannot_share=draw(st.sampled_from([0, 0, 0, 1, 2])),
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
    return population, (h, f), draw(young_person())


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
        False,
    )
    return population, (h, f), added


def child_inputs(age, male, kind, overnight, cannot_share):
    inputs = {"age": age, "is_male": male, "is_household_head": False}
    if cannot_share:
        inputs["dla_sc_middle_plus"] = True
        inputs["cannot_reasonably_share_bedroom_due_to_disability"] = True
    if kind == "foster":
        inputs["is_looked_after_by_local_authority"] = True
    if kind == "adopted":
        inputs["is_placed_for_adoption"] = True
    if overnight:
        inputs["dla_sc_middle_plus"] = True
        inputs["has_non_resident_overnight_carer"] = True
    return inputs


def build(
    population,
    added=None,
    supply_roles=True,
    added_child=None,
    num_bedrooms=None,
    flagged_child=None,
):
    """One situation for the population, optionally with a person aged 16 to
    19 added to family ``added[0]`` = (household, family) with attributes
    ``added[1]``, or a child ``added_child[1]`` = (age, is_male, kind,
    overnight, cannot share) added to family ``added_child[0]``.
    ``num_bedrooms`` lists each household's bedrooms (unreported if None).
    ``flagged_child`` = (household, family, index) marks that child as unable
    to share a bedroom.

    Returns the situation and, per benefit unit, its (household, family)."""
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
            for pid in ids[: fam["couple_cannot_share"]]:
                people[pid]["pip_dl"] = 5_000
                people[pid]["cannot_reasonably_share_bedroom_due_to_disability"] = True
            children = list(fam["children"])
            if flagged_child is not None and flagged_child[:2] == (h, f):
                i = flagged_child[2]
                children[i] = children[i][:4] + (True,)
            if added_child is not None and added_child[0] == (h, f):
                children.append(added_child[1])
            for i, spec in enumerate(children):
                pid = f"{name}_child_{i}"
                people[pid] = child_inputs(*spec)
                if supply_roles:
                    people[pid]["is_claimant_or_partner"] = False
                ids.append(pid)
            if added is not None and added[0] == (h, f):
                pid = f"{name}_added"
                people[pid] = {**added[1], "is_household_head": False}
                if supply_roles:
                    people[pid]["is_claimant_or_partner"] = False
                ids.append(pid)
            extra = {}
            if fam["role"] == "sharer":
                extra["liable_for_share_of_household_rent"] = True
            if fam["role"] in ("boarder", "lodger"):
                people[ids[0]][f"rent_paid_as_{fam['role']}"] = 5_000
            if fam["role"] == "head":
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
        if num_bedrooms is not None:
            homes[f"h{h}"]["num_bedrooms"] = num_bedrooms[h]
    situation = {"people": people, "benunits": benunits, "households": homes}
    return situation, keys


def bedrooms(situation):
    sim = Simulation(situation=situation)
    uc = np.asarray(sim.calculate("LHA_allowed_bedrooms", YEAR))
    hb = np.asarray(sim.calculate("housing_benefit_LHA_allowed_bedrooms", YEAR))
    return sim, uc, hb


def fewest_rooms_for_children(children):
    """Brute force: the fewest rooms holding the children two to a room,
    where a pair must be of the same sex or both under 10, and a child who
    cannot share because of disability (a third element that is true) shares
    with no one."""

    def can_share(a, b):
        if (len(a) > 2 and a[2]) or (len(b) > 2 and b[2]):
            return False
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
        c[2] in ("foster", "adopted") for c in fam["children"]
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
    return dict(
        # A qualifying young person no one is responsible for (UC para
        # 9(2)(g); reg 4(6)(a)).
        unclaimed=looked_after and uc_qualifying_young_person(p),
        # The family's foster child: looked after and under 18 (UC reg 2,
        # "foster parent"; para 9(3)).
        fostered=looked_after,
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


@PROPERTY_SETTINGS
@given(scenario())
def test_exact_effect_of_adding_a_person_aged_16_to_19(case):
    population, target, person = case
    person = without_overnight_care(person)
    before, keys = build(population)
    after, _ = build(population, (target, person))
    _, uc_before, hb_before = bedrooms(before)
    _, uc_after, hb_after = bedrooms(after)
    added = flags(person)
    fam = population[target[0]][target[1]]
    # 2. Exact effect.
    expected_uc = np.zeros(len(keys))
    expected_hb = np.zeros(len(keys))
    t = keys.index(target)
    expected_uc[t] += 0 if added["unclaimed"] or added["fostered"] else 1
    expected_uc[t] += int(added["fostered"] and not fosters(fam))
    expected_hb[t] += 0 if added["placed"] else 1
    expected_hb[t] += int(added["placed"] and not fosters(fam))
    head = keys.index((target[0], 0))
    if fam["role"] == "non_dependant":
        expected_uc[head] += 0 if added["unclaimed"] else 1
    if fam["role"] in ("non_dependant", "boarder", "lodger"):
        expected_hb[head] += 0 if added["placed"] else 1
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
@given(child_scenario(["foster"]))
def test_a_foster_child_adds_only_the_foster_parents_bedroom(case):
    population, target, added_child = case
    before, keys = build(population)
    after, _ = build(population, added_child=(target, added_child))
    _, uc_before, hb_before = bedrooms(before)
    _, uc_after, hb_after = bedrooms(after)
    # 4. Foster children.
    fam = population[target[0]][target[1]]
    t = keys.index(target)
    new_carer = int(not fosters(fam))
    expected_uc = np.zeros(len(keys))
    expected_uc[t] = new_carer
    assert np.array_equal(uc_after - uc_before, expected_uc)
    assert np.array_equal(hb_after - hb_before, expected_uc)


@st.composite
def reference_scenario(draw):
    population, target, person = draw(scenario())
    # Each household's bedrooms: unreported (0) or 1 to 6, as in the FRS.
    num_bedrooms = draw(
        st.lists(
            st.sampled_from([0, 0, 1, 2, 3, 4, 5, 6]),
            min_size=len(population),
            max_size=len(population),
        )
    )
    return population, target, person, num_bedrooms


def pairable(children):
    """(age, is_male) of each child, for the pairing without the condition."""
    return [c[:2] for c in children]


def with_flags(children):
    """(age, is_male, cannot share) of each child."""
    return [(c[0], c[1], c[4]) for c in children]


def couple_cannot_share(fam):
    """The family is a couple one of whom cannot share a bedroom with the
    other (UC Sch 4 para 12(6A); HB reg 2(1))."""
    return len(fam["adults"]) == 2 and fam["couple_cannot_share"] > 0


@PROPERTY_SETTINGS
@given(reference_scenario())
def test_bedrooms_match_a_reference_count_of_the_size_criteria(case):
    population, target, person, num_bedrooms = case
    situation, keys = build(population, (target, person), num_bedrooms=num_bedrooms)
    sim, uc, hb = bedrooms(situation)
    uc_additional = np.asarray(sim.calculate("LHA_additional_bedrooms", YEAR))
    hb_additional = np.asarray(
        sim.calculate("housing_benefit_LHA_additional_bedrooms", YEAR)
    )
    hb_cannot_share = np.asarray(
        sim.calculate("housing_benefit_LHA_cannot_share_bedrooms", YEAR)
    )
    added = flags(person)
    # 5. Reference count.
    for b, (h, f) in enumerate(keys):
        families = population[h]
        fam = families[f]
        is_target = (h, f) == target
        # Own members aged 16 or over who are not the claimant or partner.
        uc_rooms = 1 + int(is_target and not (added["unclaimed"] or added["fostered"]))
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
        # Couples who cannot share: UC only the renter's (para 12(6A)); HB
        # every occupier couple (reg 13D(3)(za)-(zb)).
        uc_couples = hb_couples = int(couple_cannot_share(fam))
        if fam["role"] == "head":
            for g, other in enumerate(families[1:], start=1):
                joins = target == (h, g)
                if other["role"] == "non_dependant":
                    uc_rooms += len(other["adults"]) + int(
                        joins and not added["unclaimed"]
                    )
                    uc_children += [c for c in other["children"] if c[2] != "foster"]
                    uc_overnight |= any(o for _, o in other["adults"]) or any(
                        c[3] for c in other["children"] if c[2] != "foster"
                    )
                    uc_overnight |= (
                        joins and added["overnight"] and not added["unclaimed"]
                    )
                if other["role"] in ("non_dependant", "boarder", "lodger"):
                    # HB reg 13D(3)(a): the family's claimant or couple
                    # has one bedroom.
                    hb_rooms += 1 + int(joins and not added["placed"])
                    hb_children += [c for c in other["children"] if c[2] == "own"]
                    hb_overnight |= any(o for _, o in other["adults"]) or any(
                        c[3] for c in other["children"] if c[2] == "own"
                    )
                    hb_overnight |= joins and added["overnight"] and not added["placed"]
                    hb_couples += int(couple_cannot_share(other))
        # Children who cannot share: the fewest rooms in which none of them
        # shares, beyond the rooms the children would otherwise need (UC
        # para 12(6) and (8); HB reg 13D(3)(ba)).
        uc_child_rooms = fewest_rooms_for_children(pairable(uc_children))
        uc_disabled_child_rooms = (
            fewest_rooms_for_children(with_flags(uc_children)) - uc_child_rooms
        )
        hb_child_rooms = fewest_rooms_for_children(pairable(hb_children))
        hb_disabled_child_rooms = (
            fewest_rooms_for_children(with_flags(hb_children)) - hb_child_rooms
        )
        expected_uc_additional = (
            int(uc_overnight) + int(uc_foster) + uc_disabled_child_rooms + uc_couples
        )
        expected_hb_additional = int(hb_overnight) + int(hb_carer)
        assert uc_additional[b] == expected_uc_additional
        assert hb_additional[b] == expected_hb_additional
        assert uc[b] == uc_rooms + uc_child_rooms + expected_uc_additional
        # HB: the bedrooms if everyone could share, plus those for people who
        # cannot share, so far as the dwelling has bedrooms beyond the first
        # (reg 13D(3), closing words).
        able_to_share = hb_rooms + hb_child_rooms + expected_hb_additional
        extra = hb_disabled_child_rooms + hb_couples
        if num_bedrooms[h] > 0:
            extra = min(extra, max(num_bedrooms[h] - able_to_share, 0))
        assert hb_cannot_share[b] == extra
        assert hb[b] == able_to_share + extra


@st.composite
def flagged_child_scenario(draw):
    """A population and one of its children under 16 to flag as unable to
    share a bedroom (with a qualifying benefit)."""
    population = draw(st.lists(household(), min_size=1, max_size=4))
    children = [
        (h, f, i)
        for h, families in enumerate(population)
        for f, fam in enumerate(families)
        for i in range(len(fam["children"]))
    ]
    if not children:
        population[0][0]["children"].append((5, True, "own", False, False))
        children = [(0, 0, len(population[0][0]["children"]) - 1)]
    return population, draw(st.sampled_from(children))


@PROPERTY_SETTINGS
@given(flagged_child_scenario())
def test_a_child_who_cannot_share_adds_at_most_one_bedroom(case):
    population, flagged = case
    before, keys = build(population)
    after, _ = build(population, flagged_child=flagged)
    _, uc_before, hb_before = bedrooms(before)
    _, uc_after, hb_after = bedrooms(after)
    # 6. One more child who cannot share raises any family's bedrooms by
    # nothing or one under each scheme, with the dwelling's bedrooms
    # unreported: each such child takes a room, but the others then need at
    # most one fewer.
    for change in (uc_after - uc_before, hb_after - hb_before):
        assert np.all((change == 0) | (change == 1))
    # Only families whose size criteria count the child change: the child's
    # own family and, for a child of a non-dependant (UC) or of any occupier
    # family (HB), the household head's family.
    h, f, i = flagged
    kind = population[h][f]["children"][i][2]
    role = population[h][f]["role"]
    for b, key in enumerate(keys):
        uc_counts = (key == (h, f) and kind != "foster") or (
            key == (h, 0) and role == "non_dependant" and kind != "foster"
        )
        hb_counts = (key == (h, f) and kind == "own") or (
            key == (h, 0)
            and role in ("non_dependant", "boarder", "lodger")
            and kind == "own"
        )
        if not uc_counts:
            assert uc_after[b] == uc_before[b]
        if not hb_counts:
            assert hb_after[b] == hb_before[b]


@PROPERTY_SETTINGS
@given(reference_scenario())
def test_housing_benefit_rooms_never_exceed_the_dwelling_beyond_the_base(case):
    population, target, person, num_bedrooms = case
    unreported, keys = build(population, (target, person))
    reported, _ = build(population, (target, person), num_bedrooms=num_bedrooms)
    sim, _, hb_free = bedrooms(unreported)
    able = hb_free - np.asarray(
        sim.calculate("housing_benefit_LHA_cannot_share_bedrooms", YEAR)
    )
    _, _, hb = bedrooms(reported)
    # 7. The dwelling's bedrooms only ever withhold the bedrooms for people
    # who cannot share: the HB count lies between the count if everyone
    # could share and the count with the dwelling unreported, and exceeds
    # the dwelling's bedrooms only where the count if everyone could share
    # already does.
    beds = np.array([num_bedrooms[h] for h, _ in keys])
    assert np.all(able <= hb) and np.all(hb <= hb_free)
    reported_beds = beds > 0
    assert np.all(hb[reported_beds] <= np.maximum(able, beds)[reported_beds])
