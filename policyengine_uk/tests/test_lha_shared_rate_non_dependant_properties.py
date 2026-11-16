"""Property-based tests for the shared accommodation rate's non-dependant
condition, which each scheme applies with its own definitions:

- Universal Credit: UC Regs 2013 Sch 4 para 28(3)-(4), with para 9 and regs
  4-5 (universal_credit_renter_has_non_dependant).
- Housing Benefit: HB Regs 2006 reg 13D(2)(a)(i), with regs 2(1), 3 and 19
  (housing_benefit_has_non_dependant).

Invariants, for any generated population of households:

1. UC: a member of the renter's benefit unit aged 16 or over, other than the
   claimant or partner, who is not looked after by a local authority stops the
   renter being a specified renter. They are either a qualifying young person
   the renter is responsible for (para 28(3)) or a non-dependant (para
   28(4)), so the shared rate never depends on which. The household head and
   a member who pays the household head as a boarder or lodger are left out:
   each is liable for their own occupation, so is not a non-dependant (para
   9(2)(d)); one who is not a qualifying young person leaves the renter's
   shared rate alone.
2. HB: such a member who is not placed with the family stops the claimant
   being a young individual with no non-dependant: they are either a young
   person in the claimant's family, making the claimant a lone parent rather
   than a single claimant (reg 2(1)), or a non-dependant (reg 3). The same
   two are left out (reg 3(2)(d)-(e) and (4)).
3. Deductions imply a non-dependant: a family charged a UC or HB
   non-dependant deduction has a non-dependant under that scheme's test.
   One exception, for HB: a joint occupier charged part of the deduction for
   a non-dependant within another joint occupier's own benefit unit, such
   as that occupier's adult son. housing_benefit_non_dep_deductions treats
   him as every joint occupier's and apportions his deduction (reg 74(5)),
   while housing_benefit_has_non_dependant counts him for his own family
   only (see outside_joint_occupiers). HB regs 3(1) and (4) give one
   residence test for both, so the split is an open question;
   test_the_examples_decide_each_invariant pins it.
4. Agreement below 19: for a member under 19 who is not the claimant or
   partner, the UC and HB person-level non-dependant definitions agree,
   except for a person a local authority looks after. They differ from 19,
   when UC's qualifying young person ends at the 1 September after the 19th
   birthday (reg 5(1)(b)) and Child Benefit's does not (Child Benefit
   (General) Regs 2006 reg 3(4)). A looked-after 16- or 17-year-old outside
   the young person tests is the renter's foster child under UC, so not a
   non-dependant (Sch 4 para 9(2)(c); is_lha_foster_child), but an HB
   non-dependant, since HB reg 3(2)(c) with reg 21(3) covers only a child or
   young person.

The generator concentrates members' ages around 16 to 20, where the schemes'
definitions differ, draws whether a 16-year-old is before the 1 September
after their 16th birthday (UC reg 5(1)(a); Child Benefit (General) Regs 2006
reg 4) and whether a lodger's member aged 16 or over pays the householder
too, and explicit examples pin the cases that decide each invariant,
including a member who is the household head, which the generator never
draws.
"""

import numpy as np
from hypothesis import HealthCheck, example, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation

# Situation inputs without a period key are set for 2025.
YEAR = 2025
PROPERTY_SETTINGS = settings(
    max_examples=15,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)
EDUCATION = ["NOT_IN_EDUCATION", "UPPER_SECONDARY", "POST_SECONDARY", "TERTIARY"]
EARNINGS = [0.0, 15_000.0, 30_000.0]


@st.composite
def member(draw):
    age = draw(st.one_of(st.integers(15, 20), st.integers(0, 40)))
    return dict(
        age=age,
        education=draw(st.sampled_from(EDUCATION)),
        looked_after=age < 18 and draw(st.booleans()),
        placed_for_adoption=age < 18 and draw(st.booleans()),
        # UC reg 5(1)(a) and Child Benefit reg 4: a 16-year-old may be in or
        # past the route to the 1 September after their 16th birthday.
        before_first_september=age == 16 and draw(st.booleans()),
        # UC reg 5(1)(b): a 19-year-old may be before or past the 1 September
        # after their 19th birthday.
        before_uc_terminal_date=age != 19 or draw(st.booleans()),
        started_education_at=draw(st.integers(14, 19)),
        earnings=draw(st.sampled_from(EARNINGS)),
        # In a lodger's family, a member aged 16 or over may pay the
        # householder for their own room (pays_rent_to_householder).
        pays_householder=age >= 16 and draw(st.booleans()),
    )


@st.composite
def household(draw):
    return dict(
        # The renter's family holds the household's oldest member, so it is
        # the household head's family.
        renter_age=draw(st.one_of(st.integers(18, 34), st.integers(41, 60))),
        partner=draw(st.sampled_from([False, False, True])),
        members=draw(st.lists(member(), min_size=0, max_size=2)),
        # Another family: none, a non-dependant family, a joint tenant (liable
        # for a share of the rent) or a lodger.
        other=draw(st.sampled_from([None, "non_dependant", "sharer", "lodger"])),
        other_age=draw(st.integers(18, 39)),
        other_earnings=draw(st.sampled_from(EARNINGS)),
        other_members=draw(st.lists(member(), min_size=0, max_size=1)),
    )


population = st.lists(household(), min_size=1, max_size=6)


def _member(
    age,
    education="NOT_IN_EDUCATION",
    started=14,
    earnings=0.0,
    before_uc_terminal_date=True,
    pays_householder=False,
):
    return dict(
        age=age,
        education=education,
        looked_after=False,
        placed_for_adoption=False,
        before_first_september=False,
        before_uc_terminal_date=before_uc_terminal_date,
        started_education_at=started,
        earnings=earnings,
        pays_householder=pays_householder,
    )


def _house(
    renter_age,
    members,
    other=None,
    other_age=30,
    other_members=(),
    member_is_head=False,
):
    return dict(
        renter_age=renter_age,
        partner=False,
        members=members,
        other=other,
        other_age=other_age,
        other_earnings=30_000.0,
        other_members=list(other_members),
        # The inputs flag the renter's first member, not the renter, as the
        # household head.
        member_is_head=member_is_head,
    )


# A young single renter with a 16-year-old who has left education: a
# non-dependant under both schemes (invariants 1 and 2).
SCHOOL_LEAVER = [_house(30, [_member(16)])]
# A young single renter with a 19-year-old in non-advanced education begun at
# 18, past the UC terminal date: a UC non-dependant, an HB young person
# (invariants 1, 2 and 4).
NINETEEN_IN_EDUCATION = [
    _house(30, [_member(19, "POST_SECONDARY", 18, before_uc_terminal_date=False)])
]
# A non-dependant family with earnings, a joint tenant sharing the rent, and
# an earning adult son in the head's own family (invariant 3).
SHARED_HOUSE = [
    _house(45, [], other="non_dependant", other_age=30),
    _house(50, [_member(25, earnings=30_000.0)], other="sharer", other_age=28),
]
# A young single householder with a lodger whose adult son pays the
# householder for his own room, so is no one's non-dependant (invariants 1
# and 2 leave him out).
PAYER = [
    _house(
        30,
        [],
        other="lodger",
        other_age=25,
        other_members=[_member(22, earnings=20_000.0, pays_householder=True)],
    )
]
# A young single renter whose benefit unit holds the household head, a
# 40-year-old who is not the claimant or partner (invariants 1 and 2 leave
# them out).
MEMBER_HEAD = [_house(25, [_member(40, earnings=20_000.0)], member_is_head=True)]


def build(population):
    people, benunits, homes = {}, {}, {}
    rows = []
    for h, house in enumerate(population):
        names = []
        renter_age = house["renter_age"]
        member_is_head = house.get("member_is_head", False)
        families = [
            dict(
                name=f"h{h}_renter",
                adults=[renter_age] + ([renter_age] if house["partner"] else []),
                earnings=0.0,
                members=house["members"],
                head=True,
                role=None,
            )
        ]
        if house["other"] is not None:
            # Younger than the renter, so not the household head.
            families.append(
                dict(
                    name=f"h{h}_other",
                    adults=[min(house["other_age"], renter_age - 1)],
                    earnings=house["other_earnings"],
                    members=house["other_members"],
                    head=False,
                    role=house["other"],
                )
            )
        for fam in families:
            ids = []
            for i, age in enumerate(fam["adults"]):
                pid = f"{fam['name']}_adult_{i}"
                people[pid] = {
                    "age": age,
                    "is_claimant_or_partner": True,
                    "is_household_head": fam["head"] and i == 0 and not member_is_head,
                    "current_education": "NOT_IN_EDUCATION",
                    "employment_income": fam["earnings"] if i == 0 else 0.0,
                    "is_before_first_september_following_16th_birthday": False,
                    "is_before_universal_credit_qualifying_young_person_terminal_date": True,
                }
                if fam["role"] == "lodger":
                    people[pid]["rent_paid_as_lodger"] = 4_000.0 if i == 0 else 0.0
                ids.append(pid)
            for i, m in enumerate(fam["members"]):
                pid = f"{fam['name']}_member_{i}"
                people[pid] = {
                    "age": m["age"],
                    "is_claimant_or_partner": False,
                    "is_household_head": fam["head"] and i == 0 and member_is_head,
                    "current_education": m["education"],
                    "is_looked_after_by_local_authority": m["looked_after"],
                    "is_placed_for_adoption": m["placed_for_adoption"]
                    and not m["looked_after"],
                    "age_started_or_accepted_current_education_or_training": m[
                        "started_education_at"
                    ],
                    "employment_income": m["earnings"],
                    "is_before_first_september_following_16th_birthday": m[
                        "before_first_september"
                    ],
                    "is_before_universal_credit_qualifying_young_person_terminal_date": m[
                        "before_uc_terminal_date"
                    ],
                }
                if fam["role"] == "lodger" and m["pays_householder"]:
                    people[pid]["rent_paid_as_lodger"] = 2_000.0
                ids.append(pid)
            benunits[fam["name"]] = {"members": ids}
            if fam["role"] == "sharer":
                benunits[fam["name"]]["liable_for_share_of_household_rent"] = True
            rows.append(dict(name=fam["name"], head=fam["head"], ids=ids))
            names += ids
        homes[f"h{h}"] = {
            "members": names,
            "rent": 9_000.0,
            "tenure_type": "RENT_PRIVATELY",
        }
    situation = {"people": people, "benunits": benunits, "households": homes}
    return Simulation(situation=situation), people, rows


def calc(sim, variable):
    return np.asarray(sim.calculate(variable, YEAR))


def liable_for_own_occupation(sim, people):
    """For each person, whether they are the household head or pay the head
    as a boarder or lodger: liable for their own occupation, so no one's
    non-dependant (UC Sch 4 para 9(2)(d); HB reg 3(2)(d)-(e), (4))."""
    head = calc(sim, "is_resolved_household_head")
    payer = calc(sim, "pays_rent_to_householder")
    return dict(zip(people, head | payer))


@PROPERTY_SETTINGS
@given(population)
@example(SCHOOL_LEAVER)
@example(NINETEEN_IN_EDUCATION)
@example(PAYER)
@example(MEMBER_HEAD)
def test_shared_rate_never_depends_on_how_a_member_aged_16_or_over_is_classed(pop):
    sim, people, rows = build(pop)
    specified = calc(sim, "is_lha_shared_accommodation_rate_specified_renter")
    hb_young_individual = calc(sim, "is_housing_benefit_young_individual")
    hb_has_non_dependant = calc(sim, "housing_benefit_has_non_dependant")
    placed = dict(zip(people, calc(sim, "is_child_or_young_person_placed_with_family")))
    liable = liable_for_own_occupation(sim, people)
    for i, row in enumerate(rows):
        others = [
            p
            for p in row["ids"]
            if not people[p]["is_claimant_or_partner"]
            and people[p]["age"] >= 16
            and not liable[p]
        ]
        # Invariant 1.
        if any(not people[p]["is_looked_after_by_local_authority"] for p in others):
            assert not specified[i], row["name"]
        # Invariant 2.
        if any(not placed[p] for p in others):
            assert not (hb_young_individual[i] and not hb_has_non_dependant[i]), row[
                "name"
            ]


def shares_another_joint_occupiers_own_non_dependant(sim, people, rows):
    """For each family, whether it is a joint occupier in a household where
    another joint occupier's benefit unit holds an HB non-dependant: the
    exception to invariant 3 for HB."""
    share = calc(sim, "share_of_household_rent")
    in_unit = dict(
        zip(people, calc(sim, "is_benefit_unit_non_dependant_for_legacy_benefits"))
    )
    house = [row["name"].split("_")[0] for row in rows]
    return [
        share[i] > 0
        and any(
            j != i
            and house[j] == house[i]
            and share[j] > 0
            and any(in_unit[p] for p in rows[j]["ids"])
            for j in range(len(rows))
        )
        for i in range(len(rows))
    ]


@PROPERTY_SETTINGS
@given(population)
@example(SHARED_HOUSE)
@example(PAYER)
def test_a_non_dependant_deduction_implies_a_non_dependant(pop):
    sim, people, rows = build(pop)
    # Invariant 3.
    uc = calc(sim, "uc_non_dep_deductions")
    uc_has = calc(sim, "universal_credit_renter_has_non_dependant")
    hb = calc(sim, "housing_benefit_non_dep_deductions")
    hb_has = calc(sim, "housing_benefit_has_non_dependant")
    excepted = shares_another_joint_occupiers_own_non_dependant(sim, people, rows)
    for i, row in enumerate(rows):
        assert uc[i] <= 0 or uc_has[i], row["name"]
        assert hb[i] <= 0 or hb_has[i] or excepted[i], row["name"]


@PROPERTY_SETTINGS
@given(population)
@example(SCHOOL_LEAVER)
@example(NINETEEN_IN_EDUCATION)
def test_uc_and_hb_non_dependant_definitions_agree_below_19(pop):
    sim, people, _ = build(pop)
    # Invariant 4.
    uc = calc(sim, "is_benefit_unit_non_dependant_for_universal_credit")
    hb = calc(sim, "is_benefit_unit_non_dependant_for_legacy_benefits")
    for j, (pid, p) in enumerate(people.items()):
        if (
            not p["is_claimant_or_partner"]
            and p["age"] < 19
            and not p.get("is_looked_after_by_local_authority", False)
        ):
            assert uc[j] == hb[j], pid


def test_the_examples_decide_each_invariant():
    """The explicit examples exercise what each invariant turns on, so a
    regression in either scheme's definition cannot pass vacuously."""
    sim, people, rows = build(SCHOOL_LEAVER)
    assert calc(sim, "universal_credit_renter_has_non_dependant")[0]
    assert calc(sim, "housing_benefit_has_non_dependant")[0]
    assert calc(sim, "is_housing_benefit_young_individual")[0]

    sim, people, rows = build(NINETEEN_IN_EDUCATION)
    assert calc(sim, "universal_credit_renter_has_non_dependant")[0]
    assert not calc(
        sim, "is_responsible_for_child_or_qualifying_young_person_for_universal_credit"
    )[0]
    assert not calc(sim, "housing_benefit_has_non_dependant")[0]

    sim, people, rows = build(SHARED_HOUSE)
    hb = calc(sim, "housing_benefit_non_dep_deductions")
    uc = calc(sim, "uc_non_dep_deductions")
    # Head of the first household: a non-dependant family with earnings.
    assert hb[0] > 0 and uc[0] > 0
    # Head of the second household: an earning adult son in their own family.
    assert hb[2] > 0 and uc[2] > 0
    # The joint tenant in that household bears part of the son's HB
    # deduction but has no HB non-dependant: the exception to invariant 3,
    # an open question under HB regs 3(1), (4) and 74(5).
    has = calc(sim, "housing_benefit_has_non_dependant")
    excepted = shares_another_joint_occupiers_own_non_dependant(sim, people, rows)
    assert hb[3] > 0 and not has[3] and excepted[3]
    # Only the head's claim counts him under UC (Sch 4 para 9(2)(f)).
    assert uc[3] == 0 and not calc(sim, "universal_credit_renter_has_non_dependant")[3]

    # Invariants 1 and 2 leave out a member liable for their own occupation:
    # with one, the renter keeps the shared rate under both schemes.
    for population, row, member in [
        # The lodger's adult son, who pays the householder himself.
        (PAYER, 1, "h0_other_member_0"),
        # The household head, in the young renter's benefit unit.
        (MEMBER_HEAD, 0, "h0_renter_member_0"),
    ]:
        sim, people, rows = build(population)
        assert member in rows[row]["ids"]
        assert liable_for_own_occupation(sim, people)[member]
        assert calc(sim, "is_lha_shared_accommodation_rate_specified_renter")[row]
        assert calc(sim, "is_housing_benefit_young_individual")[row]
        assert not calc(sim, "housing_benefit_has_non_dependant")[row]
        assert calc(sim, "uc_non_dep_deductions")[row] == 0
        assert calc(sim, "housing_benefit_non_dep_deductions")[row] == 0


def test_a_deduction_implies_a_non_dependant_when_a_family_has_no_claimant():
    """Invariant 3 holds for any input, including another family whose only
    member is not flagged as a claimant or partner: both flags count the same
    people the deduction formulas charge."""
    situation = {
        "people": {
            "head": {
                "age": 45,
                "is_claimant_or_partner": True,
                "is_household_head": True,
            },
            "other": {
                "age": 30,
                "is_claimant_or_partner": False,
                "is_household_head": False,
                "employment_income": 30_000.0,
            },
        },
        "benunits": {
            "head_family": {"members": ["head"]},
            "other": {"members": ["other"]},
        },
        "households": {
            "home": {
                "members": ["head", "other"],
                "rent": 9_000.0,
                "tenure_type": "RENT_PRIVATELY",
            }
        },
    }
    sim = Simulation(situation=situation)
    assert calc(sim, "uc_non_dep_deductions")[0] > 0
    assert calc(sim, "universal_credit_renter_has_non_dependant")[0]
    assert calc(sim, "housing_benefit_non_dep_deductions")[0] > 0
    assert calc(sim, "housing_benefit_has_non_dependant")[0]
