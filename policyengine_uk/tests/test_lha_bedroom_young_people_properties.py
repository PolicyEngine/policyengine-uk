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
   9(2)(g)). The household head's family also gains one bedroom under both
   schemes if the person joins a non-dependant's family, and one Housing
   Benefit bedroom if they join a boarder's or lodger's family. No other
   family's bedrooms change.
3. Reference: every family's bedrooms equal an independent count of the size
   criteria: one for the claimant or couple; one for each other member aged
   16 or over (for Universal Credit, except a qualifying young person no one
   is responsible for); for the household head's family, one for each person
   aged 16 or over in a non-dependant's family (and, for Housing Benefit, in
   a boarder's or lodger's family); and the fewest rooms that hold the
   family's children under 16 two to a room, where only children of the same
   sex or two children under 10 may share, found by brute force. Children of
   other families are not counted for the household head, matching the model
   (a separate, existing gap).
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
    return population, (h, f), draw(young_person())


def build(population, added=None, supply_roles=True):
    """One situation for the population, optionally with a person added to
    family ``added[0]`` = (household, family) with attributes ``added[1]``.

    Returns the situation and, per benefit unit, its (household, family)."""
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
    situation = {"people": people, "benunits": benunits, "households": homes}
    return situation, keys


def bedrooms(situation):
    sim = Simulation(situation=situation)
    uc = np.asarray(sim.calculate("LHA_allowed_bedrooms", YEAR))
    hb = np.asarray(sim.calculate("housing_benefit_LHA_allowed_bedrooms", YEAR))
    return sim, uc, hb


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
def test_exact_effect_of_adding_a_person_aged_16_to_19(case):
    population, target, person = case
    before, keys = build(population)
    after, _ = build(population, (target, person))
    _, uc_before, hb_before = bedrooms(before)
    sim, uc_after, hb_after = bedrooms(after)
    # Whether the added person is a qualifying young person no one is
    # responsible for. (The qualifying young person tests themselves are
    # covered elsewhere.)
    pid = f"h{target[0]}_f{target[1]}_added"
    index = list(after["people"]).index(pid)
    qualifying = sim.calculate("is_qualifying_young_person_for_universal_credit", YEAR)
    responsible = sim.calculate(
        "is_child_or_qualifying_young_person_for_universal_credit", YEAR
    )
    unclaimed = bool(qualifying[index]) and not bool(responsible[index])
    # 2. Exact effect.
    expected_uc = np.zeros(len(keys))
    expected_hb = np.zeros(len(keys))
    t = keys.index(target)
    expected_uc[t] += 0 if unclaimed else 1
    expected_hb[t] += 1
    role = population[target[0]][target[1]]["role"]
    head = keys.index((target[0], 0))
    if role == "non_dependant":
        expected_uc[head] += 1
        expected_hb[head] += 1
    elif role in ("boarder", "lodger"):
        expected_hb[head] += 1
    assert np.array_equal(uc_after - uc_before, expected_uc)
    assert np.array_equal(hb_after - hb_before, expected_hb)


@PROPERTY_SETTINGS
@given(scenario())
def test_bedrooms_match_an_independent_count_of_the_size_criteria(case):
    population, target, person = case
    situation, keys = build(population, (target, person))
    sim, uc, hb = bedrooms(situation)
    qualifying = sim.calculate("is_qualifying_young_person_for_universal_credit", YEAR)
    responsible = sim.calculate(
        "is_child_or_qualifying_young_person_for_universal_credit", YEAR
    )
    unclaimed = dict(
        zip(situation["people"], np.asarray(qualifying) & ~np.asarray(responsible))
    )
    # 3. Reference count.
    for b, (h, f) in enumerate(keys):
        families = population[h]
        fam = families[f]
        added = (h, f) == target
        own_children = fewest_rooms_for_children(fam["children"])
        own_uc = int(added and not unclaimed[f"h{h}_f{f}_added"])
        own_hb = int(added)
        outside_uc = outside_hb = 0
        if fam["role"] == "head":
            for g, other in enumerate(families[1:], start=1):
                aged_16_or_over = len(other["adults"]) + int(target == (h, g))
                if other["role"] == "non_dependant":
                    outside_uc += aged_16_or_over
                if other["role"] in ("non_dependant", "boarder", "lodger"):
                    outside_hb += aged_16_or_over
        assert uc[b] == 1 + own_uc + outside_uc + own_children
        assert hb[b] == 1 + own_hb + outside_hb + own_children
