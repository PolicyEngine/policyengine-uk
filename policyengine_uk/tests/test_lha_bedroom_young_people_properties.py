"""Property-based tests for the bedrooms of benefit-unit members aged 16 or
over who are not the claimant or partner (UC Regs 2013 Sch 4 paras 9-10; HB
Regs 2006 and HB (SPC) Regs 2006 reg 13D(3)).

Invariants, for any generated population of households:

1. Monotonicity: adding a person aged 16 to 19 to any family never lowers
   any family's Universal Credit or Housing Benefit bedrooms, whether the
   claimant and partner are supplied or inferred.
2. Exact effect: when the added person is not the claimant or partner, their
   family gains one Housing Benefit bedroom, and one Universal Credit bedroom
   unless they are a qualifying young person no one is responsible for (para
   9(2)(g)) or they head the household and are not a qualifying young person
   (the formula treats the household head as liable for the rent, so such
   a member is neither a renter nor a non-dependant: paras 1(2), 9(1)(a) and
   9(2)(d)). If they join a non-dependant's family, the claim that counts the
   household's non-dependants (uc_non_dependants_counted) gains one Universal
   Credit bedroom unless they are a qualifying young person no one is
   responsible for (para 9(2)(g) applies to the whole extended benefit unit),
   and every family liable for the rent gains one Housing Benefit bedroom,
   since they are an occupier of each such claim (reg 13D(12)). If they join
   a boarder's or lodger's family, every family liable for the rent gains one
   Housing Benefit bedroom. If they are an in-unit non-dependant (invariant
   4) of a family that makes no Universal Credit claim of its own, the claim
   that counts the household's non-dependants gains one Universal Credit
   bedroom too, as it bears their contribution. No other family's bedrooms
   change.
3. Reference: every family's bedrooms equal an independent count of the size
   criteria. Universal Credit: one for the renter or couple; one for each
   other member aged 16 or over, except a qualifying young person no one is
   responsible for and a household head who is not a qualifying young
   person; for the counting claim, one for each person aged 16 or
   over in a non-dependant's family, with the same exception, and one for
   each in-unit non-dependant of a family that makes no claim; and the
   fewest rooms that hold the family's own children. Housing Benefit, for a
   family liable for the rent: one for the claimant or couple; one for each
   other member aged 16 or over; for each non-dependant's, boarder's or
   lodger's family, one for its couple or single adult (reg 13D(3)(a), (b))
   and one for each other member aged 16 or over; and the fewest rooms that
   hold the children of all those occupiers together. Any other family's
   Housing Benefit claim counts only its own members. The fewest rooms hold
   children under 16 two to a room, where only children of the same sex or
   two children under 10 may share, found by brute force. Which claim counts
   the non-dependants, and which families are liable for the rent, are read
   from the model; they are tested elsewhere. Universal Credit does not yet
   count other families' children (a separate change).
4. In-unit non-dependants: every member of a benefit unit aged 16 or over
   who is neither the claimant nor partner nor a Universal Credit qualifying
   young person nor the household head (the householder in whose name the
   accommodation is rented, whom the formula reads as liable for the rent,
   so that para 9(2)(d) excludes them) is a non-dependant (para 9(2)) with
   a bedroom (para 10(1)(c)). So their family has one more Universal Credit
   bedroom with them than without them, and making them qualifying young
   persons the renter is responsible for (para 10(1)(b)) leaves every family's
   Universal Credit bedrooms unchanged, except that the claim counting the
   household's non-dependants loses the bedroom of one whose own family
   makes no claim and is not that claim (para 9(2)(g)). The model's
   is_benefit_unit_non_dependant_for_universal_credit, which the formula
   reads, marks exactly these members.
5. Rooms and contributions: nobody owes a housing cost contribution without
   being a non-dependant (para 13). Adding an adult aged 16 to 64, not in
   education, to any family: if they are an in-unit non-dependant, they owe
   a contribution unless aged under 21 or receiving Attendance Allowance
   (para 16(2)); the claim that bears it (their own family's if it makes a
   claim, otherwise the one that counts the household's non-dependants)
   gains exactly that contribution, unless its renter is exempt (para 15),
   and one bedroom; no other family's contributions change.
6. Coding: moving such an adult, not claiming, between a family and a
   benefit unit of their own leaves every claiming family's Universal Credit
   bedrooms, contributions and award unchanged.
"""

from itertools import combinations

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
EDUCATION = ["NOT_IN_EDUCATION", "UPPER_SECONDARY", "TERTIARY"]

child = st.tuples(st.integers(0, 15), st.booleans())  # (age, is_male)


@st.composite
def family(draw, role):
    return dict(
        role=role,
        adults=draw(st.lists(st.integers(20, 85), min_size=1, max_size=2)),
        children=draw(st.lists(child, min_size=0, max_size=4)),
    )


@st.composite
def household(draw):
    others = draw(
        st.lists(st.sampled_from(ROLES).flatmap(family), min_size=0, max_size=2)
    )
    return [draw(family("head"))] + others


@st.composite
def young_person(draw):
    return dict(
        age=draw(st.integers(16, 19)),
        is_male=draw(st.booleans()),
        current_education=draw(st.sampled_from(EDUCATION)),
        age_started_or_accepted_current_education_or_training=draw(st.integers(14, 19)),
        is_before_universal_credit_qualifying_young_person_terminal_date=draw(
            st.booleans()
        ),
        is_looked_after_by_local_authority=draw(st.booleans()),
        receives_benefits_in_own_right=draw(st.booleans()),
    )


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


def build(population, added=None, supply_roles=True):
    """One situation for the population, optionally with a person added to
    family ``added[0]`` = (household, family) with attributes ``added[1]``.

    Returns the situation and, per benefit unit, its (household, family).
    An added person with ``is_household_head`` heads the household in place
    of the head family's first adult."""
    people, benunits, homes, keys = {}, {}, {}, []
    for h, families in enumerate(population):
        members = []
        for f, fam in enumerate(families):
            name = f"h{h}_f{f}"
            ids = []
            for i, age in enumerate(fam["adults"]):
                pid = f"{name}_adult_{i}"
                people[pid] = {"age": age, "is_household_head": False}
                if supply_roles:
                    people[pid]["is_claimant_or_partner"] = True
                elif fam["children"]:
                    people[pid]["is_parent"] = True
                ids.append(pid)
            for i, (age, male) in enumerate(fam["children"]):
                pid = f"{name}_child_{i}"
                people[pid] = {"age": age, "is_male": male, "is_household_head": False}
                if supply_roles:
                    people[pid]["is_claimant_or_partner"] = False
                ids.append(pid)
            if added is not None and added[0] == (h, f):
                pid = f"{name}_added"
                people[pid] = {
                    **added[1],
                    "is_household_head": added[1].get("is_household_head", False),
                }
                if supply_roles:
                    people[pid]["is_claimant_or_partner"] = False
                ids.append(pid)
            extra = {}
            if fam["role"] == "sharer":
                extra["liable_for_share_of_household_rent"] = True
            if fam["role"] in ("boarder", "lodger"):
                people[ids[0]][f"rent_paid_as_{fam['role']}"] = 5_000
            added_head = (
                added is not None
                and added[0] == (h, f)
                and added[1].get("is_household_head", False)
            )
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


def has_own_uc_bedroom(sim, situation):
    """Each person aged 16 or over who is not the claimant or partner: whether
    they have a Universal Credit bedroom of their own. A qualifying young
    person the renter is responsible for has one (para 10(1)(b)); one no one
    is responsible for has none (para 9(2)(g)). Anyone else has one as a
    non-dependant (para 10(1)(c)), unless they head the household, whom the
    formula treats as liable for the rent (para 9(2)(d))."""
    qualifying = np.asarray(
        sim.calculate("is_qualifying_young_person_for_universal_credit", YEAR)
    )
    responsible = np.asarray(
        sim.calculate("is_child_or_qualifying_young_person_for_universal_credit", YEAR)
    )
    head = np.asarray(sim.calculate("is_resolved_household_head", YEAR))
    return dict(zip(situation["people"], responsible | (~qualifying & ~head)))


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
# A qualifying young person a local authority looks after, added to the
# head's family: no Universal Credit bedroom (para 9(2)(g)).
@example(
    (
        [[dict(role="head", adults=[40], children=[])]],
        (0, 0),
        dict(
            age=17,
            is_male=True,
            current_education="UPPER_SECONDARY",
            age_started_or_accepted_current_education_or_training=16,
            is_before_universal_credit_qualifying_young_person_terminal_date=True,
            is_looked_after_by_local_authority=True,
            receives_benefits_in_own_right=False,
        ),
    )
)
# The same young person in a non-dependant's family: no Universal Credit
# bedroom in the renter's claim either (para 9(2)(g)).
@example(
    (
        [
            [
                dict(role="head", adults=[40], children=[]),
                dict(role="non_dependant", adults=[45], children=[]),
            ]
        ],
        (0, 1),
        dict(
            age=17,
            is_male=True,
            current_education="UPPER_SECONDARY",
            age_started_or_accepted_current_education_or_training=16,
            is_before_universal_credit_qualifying_young_person_terminal_date=True,
            is_looked_after_by_local_authority=True,
            receives_benefits_in_own_right=False,
        ),
    )
)
def test_exact_effect_of_adding_a_person_aged_16_to_19(case):
    population, target, person = case
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
    gains = has_own_uc_bedroom(sim, after)[f"h{target[0]}_f{target[1]}_added"]
    names = list(after["people"])
    marked = in_unit_non_dependants(sim)[
        names.index(f"h{target[0]}_f{target[1]}_added")
    ]
    # 2. Exact effect.
    expected_uc = np.zeros(len(keys))
    expected_hb = np.zeros(len(keys))
    t = keys.index(target)
    expected_uc[t] += 1 if gains else 0
    expected_hb[t] += 1
    role = population[target[0]][target[1]]["role"]
    same_household = np.array([h == target[0] for h, _ in keys])
    passed_on = (
        role != "non_dependant" and marked and not own_claims(sim)[t] and not counted[t]
    )
    if (role == "non_dependant" and gains) or passed_on:
        expected_uc[same_household & counted] += 1
    if role in ("non_dependant", "boarder", "lodger"):
        expected_hb[same_household & liable] += 1
    assert np.array_equal(uc_after - uc_before, expected_uc)
    assert np.array_equal(hb_after - hb_before, expected_hb)


@PROPERTY_SETTINGS
@given(scenario())
def test_bedrooms_match_an_independent_count_of_the_size_criteria(case):
    population, target, person = case
    situation, keys = build(population, (target, person))
    sim, uc, hb = bedrooms(situation)
    counted, liable = claim_roles(sim)
    gains = has_own_uc_bedroom(sim, situation)
    own_claim = own_claims(sim)
    names = list(situation["people"])
    marked = in_unit_non_dependants(sim)
    occupier_roles = ("non_dependant", "boarder", "lodger")
    # 3. Reference count.
    for b, (h, f) in enumerate(keys):
        families = population[h]
        fam = families[f]
        added = (h, f) == target
        own_uc = int(added and gains[f"h{h}_f{f}_added"])
        own_hb = int(added)
        outside_uc = outside_hb = 0
        hb_children = list(fam["children"])
        for g, other in enumerate(families):
            if g == f:
                continue
            joins = target == (h, g)
            if counted[b] and other["role"] == "non_dependant":
                # UC: each non-dependant who is not a child (adults are
                # supplied as claimant or partner).
                outside_uc += len(other["adults"])
                outside_uc += int(joins and gains[f"h{h}_f{g}_added"])
            elif counted[b] and joins and not own_claim[keys.index((h, g))]:
                # UC: an in-unit non-dependant of a family that makes no
                # claim of its own counts in this claim (para 9(2)(f)).
                outside_uc += int(marked[names.index(f"h{h}_f{g}_added")])
            if liable[b] and other["role"] in occupier_roles:
                # HB: the occupier family's couple ((a)) or single adult
                # ((b)), the added person ((b)) and its children.
                outside_hb += 1 + int(joins)
                hb_children += other["children"]
        uc_children = fewest_rooms_for_children(fam["children"])
        assert uc[b] == 1 + own_uc + outside_uc + uc_children
        assert hb[b] == 1 + own_hb + outside_hb + fewest_rooms_for_children(hb_children)


def in_unit_non_dependants(sim):
    """Each person: aged 16 or over, neither the claimant nor partner, not a
    Universal Credit qualifying young person, and not the household head
    (UC Regs 2013 Sch 4 para 9(2), with (d) for the head, the householder
    in whose name the accommodation is rented). Checks that the model's
    is_benefit_unit_non_dependant_for_universal_credit marks the same
    people."""
    age = np.asarray(sim.calculate("age", YEAR))
    claimant_or_partner = np.asarray(sim.calculate("is_claimant_or_partner", YEAR))
    qualifying = np.asarray(
        sim.calculate("is_qualifying_young_person_for_universal_credit", YEAR)
    )
    household_head = np.asarray(sim.calculate("is_resolved_household_head", YEAR))
    marked = (age >= 16) & ~claimant_or_partner & ~qualifying & ~household_head
    model = np.asarray(
        sim.calculate("is_benefit_unit_non_dependant_for_universal_credit", YEAR)
    )
    assert np.array_equal(marked, model)
    return marked


@PROPERTY_SETTINGS
@given(scenario())
def test_every_in_unit_non_dependant_has_a_bedroom(case):
    population, target, person = case
    situation, keys = build(population, (target, person))
    sim, uc, _ = bedrooms(situation)
    marked = in_unit_non_dependants(sim)
    names = list(situation["people"])
    # 4. A marked member has a bedroom of their own: without them, their
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
    household of family ``target``, not claiming Universal Credit."""
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
    # 5. Nobody owes a contribution without being a non-dependant (Sch 4
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
    # 6. Every family making a claim keeps its bedrooms, contribution and
    # award whether the adult is coded in a benefit unit or in their own.
    for variable in (
        "LHA_allowed_bedrooms",
        "uc_non_dep_deductions",
        "universal_credit",
    ):
        a = calc_in(variable)[own_claim_in]
        b = calc_out(variable)[:n][own_claim_in]
        assert np.allclose(a, b), variable
