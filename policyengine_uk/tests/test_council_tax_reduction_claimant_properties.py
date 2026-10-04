"""Property-based tests for who claims Council Tax Reduction in a household
of several families.

Only a person liable to pay the council tax is in a class entitled to a
reduction (SI 2012/2885 Sch 1 paras 2-3; SI 2013/3029 regs 22-25; SSI
2021/249 reg 13; SSI 2012/319 reg 14). The model takes the household head
(the household reference person, a householder) as the liable resident, and
families liable for a share of the rent as jointly liable with the head's.

Where the rent is shared, a full-time student is excluded from entitlement
(Default Scheme Sch para 75(1)); the model takes a person in higher education
as one, so a family there claims only through a liable non-student.

Invariants, for any generated population of households, including ties in
age, no head flagged, several heads flagged, sharer families with no member
aged 18 or over, and adults in higher education. Invariants marked "pin"
restate the formula, so they guard against regressions rather than check it
independently.

1. One head: exactly one family in each household contains the household
   head. With one or more members flagged, it holds a flagged member; with
   none, it holds a member of the greatest age.
2. Claimants: a household whose rent is not shared has at most one claimant
   family, the head's, and the head's family claims whenever the head is
   18 or over and, where the rent is shared, not a student (including a
   grandparent head whose family's claimant and partner are 17-year-old
   parents). A family with no member aged 18 or over never claims (no one
   under 18 can be liable, LGFA 1992 s.6(5)), and where the rent is shared
   no family claims through students alone. Every person treated as liable
   is 18 or over and in the head's family or a sharer family. Pin: a family
   claims if and only if it has a member treated as liable who, where the
   rent is shared, is not a student.
3. Simulated reductions: no family outside the claimants gets one, and a
   household's total never exceeds its council tax. (Reported reductions,
   used where a scheme is not modelled, are outside this test.)
4. Non-dependants: no claimant or partner of a claimant family is a
   non-dependant (the applicant's family, SI 2012/2885 reg 9(2)(a)). Pin: no
   member of a sharer family is one, and every adult outside the claimant
   families, the sharer families and boarders' and lodgers' families is one.
5. Differential: where the input flags at most one head, the family holding
   the head is the one holding the person-level household head that Housing
   Benefit and Universal Credit use.
6. Not age: with one head flagged, raising every other member's age above
   the head's does not change who claims.
7. No-op: where the flagged head is strictly the eldest member and the rent
   is not shared, the claimant family is the eldest adult's family, the
   previous rule.
8. Shares: in every household, the claimant families' shares of the council
   tax sum to at most one, so jointly liable claims never cover more than
   the whole council tax.
"""

import numpy as np
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation

YEAR = 2026
PROPERTY_SETTINGS = settings(
    max_examples=20,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)
SCHEMES = [
    ("ENGLAND", "MAIDSTONE"),
    ("ENGLAND", "MERTON"),
    ("ENGLAND", "KINGSTON_UPON_THAMES"),
    ("ENGLAND", "NEWHAM"),
    ("ENGLAND", "WESTMINSTER"),
    ("ENGLAND", "OXFORD"),
    ("SCOTLAND", "CITY_OF_EDINBURGH"),
    ("WALES", "CARDIFF"),
]
HEAD_FLAGS = ["one", "unset", "none", "several"]
# Ages around State Pension age and repeated values, so ties are common.
adult_age = st.one_of(
    st.sampled_from([18, 25, 40, 66, 67, 80, 85]), st.integers(18, 100)
)
money = st.floats(0, 40_000, allow_nan=False, allow_infinity=False)


@st.composite
def family(draw):
    return dict(
        ages=draw(st.lists(adult_age, min_size=1, max_size=2)),
        child_age=draw(st.one_of(st.none(), st.integers(0, 15))),
        earnings=draw(st.lists(money, min_size=2, max_size=2)),
        # Each adult is sometimes in higher education.
        students=draw(
            st.lists(st.sampled_from([False, False, True]), min_size=2, max_size=2)
        ),
        sharer=draw(st.booleans()),
        # Outside the first family: sometimes a single person aged 15-17.
        minor_age=draw(st.one_of(st.none(), st.none(), st.integers(15, 17))),
        # In the first family: sometimes a couple of parents aged 16-17 with
        # a baby, living in the head's family (#1896's parent-couple rule).
        minor_parents=draw(st.one_of(st.none(), st.none(), st.integers(16, 17))),
    )


def adult_ages(fam, f):
    """The family's adults (none for a minor-only family after the first)."""
    return [] if f > 0 and fam["minor_age"] is not None else fam["ages"]


@st.composite
def households(draw):
    families = draw(st.lists(family(), min_size=1, max_size=4))
    adults = sum(len(adult_ages(fam, f)) for f, fam in enumerate(families))
    return dict(
        families=families,
        scheme=draw(st.sampled_from(SCHEMES)),
        council_tax=draw(st.floats(0, 4_000, allow_nan=False)),
        rent=draw(money),
        savings=draw(st.floats(0, 20_000, allow_nan=False)),
        head_flags=draw(st.sampled_from(HEAD_FLAGS)),
        # Which adult is flagged ("one"), or which are ("several").
        head_choice=draw(st.lists(st.integers(0, adults - 1), min_size=1)),
    )


population = st.lists(households(), min_size=1, max_size=8)


def build(population, age_override=None):
    """One situation for the whole population, plus per-person facts.

    age_override(house, adult_index, age, flagged) -> new age, if given.
    """
    people, benunits, homes = {}, {}, {}
    facts = dict(flagged=[], age=[], household=[], benunit=[], sharer=[])
    benunit_index = 0
    for h, house in enumerate(population):
        country, local_authority = house["scheme"]
        if house["head_flags"] == "one":
            flagged_adults = {house["head_choice"][0]}
        elif house["head_flags"] == "several":
            flagged_adults = set(house["head_choice"])
        else:
            flagged_adults = set()
        members, adult_index = [], 0
        for f, fam in enumerate(house["families"]):
            ids = []
            for i, age in enumerate(adult_ages(fam, f)):
                pid = f"h{h}_f{f}_adult_{i}"
                flagged = adult_index in flagged_adults
                if age_override is not None:
                    age = age_override(house, adult_index, age, flagged)
                person = {
                    "age": age,
                    "employment_income": fam["earnings"][i],
                    "in_HE": fam["students"][i],
                }
                if house["head_flags"] != "unset":
                    person["is_household_head"] = flagged
                people[pid] = person
                ids.append(pid)
                facts["flagged"].append(flagged)
                facts["age"].append(age)
                adult_index += 1
            if f == 0 and fam["minor_parents"] is not None:
                for i in range(3):
                    pid = f"h{h}_f{f}_young_{i}"
                    age = fam["minor_parents"] if i < 2 else 0
                    people[pid] = {"age": age, "is_parent": i < 2}
                    if house["head_flags"] != "unset":
                        people[pid]["is_household_head"] = False
                    ids.append(pid)
                    facts["flagged"].append(False)
                    facts["age"].append(age)
            child_age = fam["child_age"]
            if f > 0 and fam["minor_age"] is not None:
                child_age = fam["minor_age"]
            if child_age is not None:
                pid = f"h{h}_f{f}_child"
                people[pid] = {"age": child_age}
                if house["head_flags"] != "unset":
                    people[pid]["is_household_head"] = False
                ids.append(pid)
                facts["flagged"].append(False)
                facts["age"].append(child_age)
            facts["household"].extend([h] * len(ids))
            facts["benunit"].extend([benunit_index] * len(ids))
            # The first family is only a sharer if it does not hold the head.
            facts["sharer"].append(fam["sharer"] and f > 0)
            benunits[f"h{h}_f{f}"] = {
                "members": ids,
                "liable_for_share_of_household_rent": fam["sharer"] and f > 0,
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
            "tenure_type": "RENT_PRIVATELY",
            "savings": house["savings"],
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


def calc(simulation, variable, map_to=None):
    return np.asarray(simulation.calculate(variable, YEAR, map_to=map_to))


def household_of_benunit(facts):
    """The household index of each benefit unit."""
    households = np.zeros(facts["sharer"].size, dtype=int)
    households[facts["benunit"]] = facts["household"]
    return households


def per_household(values, facts):
    """Sum benefit-unit values within each household."""
    return np.bincount(household_of_benunit(facts), weights=values.astype(float))


@PROPERTY_SETTINGS
@given(population)
def test_claimant_invariants(population):
    situation, facts = build(population)
    sim = Simulation(situation=situation)
    head = calc(sim, "benunit_contains_household_head")
    claimant = calc(sim, "council_tax_reduction_claimant_benunit")
    sharer = facts["sharer"]
    shared = per_household(sharer, facts) > 0
    n_households = shared.size
    person_household = facts["household"]
    person_head_family = head[facts["benunit"]]

    # 1. One head, holding a flagged member if any, else the eldest.
    assert np.all(per_household(head, facts) == 1)
    for h in range(n_households):
        in_h = person_household == h
        flagged = facts["flagged"][in_h]
        if population[h]["head_flags"] in ("one", "several"):
            assert np.any(flagged & person_head_family[in_h])
        elif population[h]["head_flags"] == "none" or not all(
            house["head_flags"] == "unset" for house in population
        ):
            ages = facts["age"][in_h]
            assert np.any((ages == ages.max()) & person_head_family[in_h])

    # 2. Claimants.
    claimants = per_household(claimant, facts)
    assert np.all(claimants[~shared] == 1)  # every head here is 18 or over
    age = calc(sim, "age")
    claimant_or_partner = calc(sim, "is_claimant_or_partner")
    has_adult = np.zeros(claimant.size, dtype=bool)
    np.logical_or.at(has_adult, facts["benunit"], age >= 18)
    assert not np.any(claimant & ~has_adult)
    liable = calc(sim, "council_tax_reduction_liable_person")
    head_person = calc(sim, "council_tax_reduction_household_head")
    in_head_or_sharer = (head | sharer)[facts["benunit"]]
    assert np.all(age[liable] >= 18)
    assert np.all(in_head_or_sharer[liable])
    student = calc(sim, "in_HE")
    person_shared = shared[person_household]
    excluded_student = person_shared & student
    head_adult = np.zeros(claimant.size, dtype=bool)
    np.logical_or.at(
        head_adult,
        facts["benunit"],
        head_person & (age >= 18) & ~excluded_student,
    )
    assert np.all(claimant[head_adult])
    claimants_not_shared = per_household(claimant, facts)[~shared]
    assert np.all(claimants_not_shared <= 1)
    has_adult_non_student = np.zeros(claimant.size, dtype=bool)
    np.logical_or.at(has_adult_non_student, facts["benunit"], (age >= 18) & ~student)
    benunit_shared = shared[household_of_benunit(facts)]
    assert not np.any(claimant & benunit_shared & ~has_adult_non_student)
    has_liable = np.zeros(claimant.size, dtype=bool)
    np.logical_or.at(has_liable, facts["benunit"], liable & ~excluded_student)
    assert np.array_equal(claimant, has_liable)

    # 3. Simulated reductions: none outside claimant families; never above
    # the council tax.
    reduction = calc(sim, "simulated_council_tax_reduction_benunit")
    assert np.all(reduction[~claimant] == 0)
    council_tax = calc(sim, "council_tax")
    assert np.all(per_household(reduction, facts) <= council_tax + 0.01)

    # 8. Shares of the council tax sum to at most one.
    share = calc(sim, "council_tax_reduction_joint_liability_share")
    assert np.all(per_household(share * claimant, facts) <= 1 + 1e-6)

    # 4. Non-dependants.
    non_dep = calc(sim, "council_tax_reduction_individual_non_dep_deduction_eligible")
    person_claimant = claimant[facts["benunit"]]
    person_sharer = sharer[facts["benunit"]]
    lodger = calc(sim, "pays_rent_to_householder")
    adult = age >= 18
    assert not np.any(non_dep & person_claimant & claimant_or_partner)
    assert not np.any(non_dep & person_sharer)
    assert np.all(non_dep[adult & ~person_claimant & ~person_sharer & ~lodger])

    # 5. Differential with the person-level household head. Once anyone in
    # the simulation has the input, everyone else's defaults to false, so an
    # "unset" household is well formed only if every household is.
    all_unset = all(house["head_flags"] == "unset" for house in population)
    well_formed = np.array(
        [
            population[h]["head_flags"] == "one"
            or (population[h]["head_flags"] == "unset" and all_unset)
            for h in person_household
        ]
    )
    person_level_head = calc(sim, "is_household_head")
    assert np.array_equal(
        person_head_family[well_formed],
        sim.map_result(
            sim.map_result(person_level_head, "person", "benunit") > 0,
            "benunit",
            "person",
        ).astype(bool)[well_formed],
    )


@PROPERTY_SETTINGS
@given(population)
def test_claimant_does_not_follow_age(population):
    for house in population:
        house["head_flags"] = "one"
    situation, facts = build(population)

    def older_than_head(house, adult_index, age, flagged):
        return age if flagged else 101 + adult_index

    raised, _ = build(population, age_override=older_than_head)
    # 6. Not age.
    before = calc(
        Simulation(situation=situation), "council_tax_reduction_claimant_benunit"
    )
    after = calc(Simulation(situation=raised), "council_tax_reduction_claimant_benunit")
    assert np.array_equal(before, after)


@PROPERTY_SETTINGS
@given(population)
def test_no_op_where_head_is_eldest(population):
    for house in population:
        house["head_flags"] = "one"
        for fam in house["families"]:
            fam["sharer"] = False

    def head_eldest(house, adult_index, age, flagged):
        return 110 if flagged else min(age, 100)

    situation, facts = build(population, age_override=head_eldest)
    sim = Simulation(situation=situation)
    claimant = calc(sim, "council_tax_reduction_claimant_benunit")
    # 7. The previous rule: the family of the household's eldest adult.
    age = calc(sim, "age")
    benunit_max_age = sim.map_result(
        sim.map_result(age, "person", "benunit", how="max"), "benunit", "person"
    )
    household_max_age = sim.map_result(
        sim.map_result(age, "person", "household", how="max"), "household", "person"
    )
    previous = sim.map_result(
        (benunit_max_age == household_max_age).astype(float), "person", "benunit"
    )
    assert np.array_equal(claimant, previous > 0)
