"""Property-based tests for the shared accommodation rate's non-dependant
condition, which each scheme applies with its own definitions:

- Universal Credit: UC Regs 2013 Sch 4 para 28(3)-(4), with para 9 and regs
  4-5 (universal_credit_renter_has_non_dependant).
- Housing Benefit: HB Regs 2006 reg 13D(2)(a)(i), with regs 2(1), 3 and 19
  (housing_benefit_claimant_has_non_dependant).

Invariants, for any generated population of households:

1. UC: a member of the renter's benefit unit aged 16 or over, other than the
   claimant or partner, who is not looked after by a local authority stops the
   renter being a specified renter. They are either a qualifying young person
   the renter is responsible for (para 28(3)) or a non-dependant (para
   28(4)), so the shared rate never depends on which.
2. HB: such a member who is not placed with the family stops the claimant
   being a young individual with no non-dependant: they are either a young
   person in the claimant's family, making the claimant a lone parent rather
   than a single claimant (reg 2(1)), or a non-dependant (reg 3).
3. Deductions imply a non-dependant: a family charged a UC or HB
   non-dependant deduction has a non-dependant under that scheme's test.
4. Agreement below 19: for a member under 19 who is not the claimant or
   partner, the UC and HB person-level non-dependant definitions agree. They
   differ only from 19, when UC's qualifying young person ends at the 1
   September after the 19th birthday (reg 5(1)(b)) and Child Benefit's does
   not (Child Benefit (General) Regs 2006 reg 3(4)).
"""

import numpy as np
from hypothesis import HealthCheck, given, settings
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


@st.composite
def member(draw):
    age = draw(st.integers(0, 40))
    return dict(
        age=age,
        education=draw(st.sampled_from(EDUCATION)),
        looked_after=age < 18 and draw(st.booleans()),
        placed_for_adoption=age < 18 and draw(st.booleans()),
        started_education_at=draw(st.integers(14, 19)),
    )


@st.composite
def household(draw):
    return dict(
        # The renter's family holds the household's oldest member, so it is
        # the household head's family.
        renter_age=draw(st.integers(41, 60)) if draw(st.booleans()) else 40,
        young_renter_age=draw(st.integers(18, 34)),
        young=draw(st.booleans()),
        partner=draw(st.booleans()),
        members=draw(st.lists(member(), min_size=0, max_size=3)),
        # Another family: none, a non-dependant family, a joint tenant (liable
        # for a share of the rent) or a lodger.
        other=draw(st.sampled_from([None, "non_dependant", "sharer", "lodger"])),
        other_age=draw(st.integers(18, 39)),
        other_members=draw(st.lists(member(), min_size=0, max_size=2)),
    )


population = st.lists(household(), min_size=1, max_size=6)


def build(population):
    people, benunits, homes = {}, {}, {}
    rows = []
    for h, house in enumerate(population):
        names = []
        renter_age = (
            house["young_renter_age"] if house["young"] else house["renter_age"]
        )
        families = [
            dict(
                name=f"h{h}_renter",
                adults=[renter_age] + ([renter_age] if house["partner"] else []),
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
                    "is_household_head": fam["head"] and i == 0,
                    "current_education": "NOT_IN_EDUCATION",
                }
                if fam["role"] == "lodger":
                    people[pid]["rent_paid_as_lodger"] = 4_000.0 if i == 0 else 0.0
                ids.append(pid)
            for i, m in enumerate(fam["members"]):
                pid = f"{fam['name']}_member_{i}"
                people[pid] = {
                    "age": m["age"],
                    "is_claimant_or_partner": False,
                    "is_household_head": False,
                    "current_education": m["education"],
                    "is_looked_after_by_local_authority": m["looked_after"],
                    "is_placed_for_adoption": m["placed_for_adoption"]
                    and not m["looked_after"],
                    "age_started_or_accepted_current_education_or_training": m[
                        "started_education_at"
                    ],
                }
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


@PROPERTY_SETTINGS
@given(population)
def test_shared_rate_never_depends_on_how_a_member_aged_16_or_over_is_classed(pop):
    sim, people, rows = build(pop)
    specified = calc(sim, "is_lha_shared_accommodation_rate_specified_renter")
    hb_young_individual = calc(sim, "is_housing_benefit_young_individual")
    hb_has_non_dependant = calc(sim, "housing_benefit_claimant_has_non_dependant")
    placed = dict(zip(people, calc(sim, "is_child_or_young_person_placed_with_family")))
    for i, row in enumerate(rows):
        others = [
            p
            for p in row["ids"]
            if not people[p]["is_claimant_or_partner"] and people[p]["age"] >= 16
        ]
        # Invariant 1.
        if any(not people[p]["is_looked_after_by_local_authority"] for p in others):
            assert not specified[i], row["name"]
        # Invariant 2.
        if any(not placed[p] for p in others):
            assert not (hb_young_individual[i] and not hb_has_non_dependant[i]), row[
                "name"
            ]


@PROPERTY_SETTINGS
@given(population)
def test_a_non_dependant_deduction_implies_a_non_dependant(pop):
    sim, _, rows = build(pop)
    # Invariant 3.
    uc = calc(sim, "uc_non_dep_deductions")
    uc_has = calc(sim, "universal_credit_renter_has_non_dependant")
    hb = calc(sim, "housing_benefit_non_dep_deductions")
    hb_has = calc(sim, "housing_benefit_claimant_has_non_dependant")
    for i, row in enumerate(rows):
        assert uc[i] <= 0 or uc_has[i], row["name"]
        assert hb[i] <= 0 or hb_has[i], row["name"]


@PROPERTY_SETTINGS
@given(population)
def test_uc_and_hb_non_dependant_definitions_agree_below_19(pop):
    sim, people, _ = build(pop)
    # Invariant 4.
    uc = calc(sim, "is_benefit_unit_non_dependant_for_universal_credit")
    hb = calc(sim, "is_benefit_unit_non_dependant_for_legacy_benefits")
    for j, (pid, p) in enumerate(people.items()):
        if not p["is_claimant_or_partner"] and p["age"] < 19:
            assert uc[j] == hb[j], pid
