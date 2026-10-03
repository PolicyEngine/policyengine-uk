"""Programme definitions, benefit-unit structure and frozen age-18 shims.

Invariants:

1. For every age 0--25, education enum and combination of head, parent,
   approved training, own-benefit receipt and looked-after status, the four
   programmes' child predicates mean under 16. Their young-person predicates
   agree with the statutory age/education/entry conditions the model encodes.
   Legacy children are Child Benefit children/QYPs other than claimants,
   partners and children placed by a local authority; the HBAI fallback and
   the claimant-or-partner presumption follow their documented assumptions.
   An unflagged member at least 16 years younger than a claimant flagged as
   a parent is never their partner, at any age, unless a member under 20 and
   at least 16 years younger explains the flag; flagging the claimant as a
   parent never adds a partner. On benefit units shaped like the FRS's (one
   or two adults, all flagged as parents when there are dependants) the
   any-age 20-year gap changes only childless couples whose claimant is 20 or
   more years older than the other adult (intended), and supplied
   claimant/partner roles are always kept.
2. HBAI types partition everyone. Any benefit unit with one head has at most
   two claimants/partners, all of them HBAI adults, and at least one if it
   has an HBAI adult; valid families (one or two adults aged 20+ and
   dependants) have exactly their adults, except an unflagged couple whose
   head is 20+ years older than the other adult (the any-age presumption,
   intended), and always when the roles are supplied. Couple/single and
   couple/lone-parent/single-person partition benefit units. Heads aged 16+
   are claimants or partners, including when explicitly younger than others,
   unless two other members are flagged parents and the head is not.
3. All 23 deprecated shims retain their original age-18 formulas, including
   empty-group sentinels and historical eldest-child tie behaviour. Explicit
   age_under_18 has the same membership as the shims for school-attendance
   inputs and household adult age/capital-gains ranks (modelling conventions,
   not statutory adult definitions).
4. Adding an under-16 dependant leaves existing claimant/partner membership
   unchanged, even when the added child carries a parent marker (an
   identified parent must be aged 16 or over; the minimised counterexample
   that found this is kept as a regression test).
   Before/after families share one Simulation to avoid repeated
   model construction, but occupy distinct households and benefit units.

Scope: these are tests of the ENCODED statutory limbs, not full entitlement.
Education status proxies full-time non-advanced study: hours, employment
contracts, approved providers and interruptions are unobserved. CB/CTC leaver
extensions are omitted, as is UC/PC's unconditional age-16-to-next-September
route. UC's terminal date is an input; PC's September terminal date is absent.
Own-benefit receipt collapses different programme-specific benefit lists.
UC/CTC/PC blanket looked-after exclusions omit statutory exceptions. HBAI's
fallback assumes dependence at 16--17 regardless of study, requires an
identified parent at 18--19 and infers partnership from head/parent status.
WTC childcare uses annual ages <16/<17 instead of the September/week cutoff;
disability inputs omit some statutory awards/history. Student support uses
benefit-unit membership as a proxy for financial dependence. These existing
limitations are preserved here, not treated as new model defects.

Statutory texts and HBAI glossary were fetched on 2026-09-28; URLs accompany
the independent scalar references below. No network or survey data is used.
"""

from itertools import product
from unittest.mock import patch

import numpy as np
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation
from policyengine_uk.tax_benefit_system import system
from policyengine_uk.variables.household.demographic.highest_education import (
    EducationType,
)

YEAR = 2026
# Keep later mutations of the public module-level system out of these tests.
_PROPERTY_SYSTEM = system.clone()
EDUCATIONS = tuple(item.name for item in EducationType)
PROGRAMMES = (
    "child_benefit",
    "universal_credit",
    "child_tax_credit",
    "pension_credit",
)
FLAGS = (
    "is_benunit_head",
    "is_parent",
    "is_in_approved_training",
    "receives_benefits_in_own_right",
    "is_looked_after_by_local_authority",
)
PROPERTY_SETTINGS = settings(
    max_examples=25,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)


def person(age, **inputs):
    return {
        "age": age,
        "current_education": "NOT_IN_EDUCATION",
        "is_benunit_head": False,
        "is_parent": False,
        "is_in_approved_training": False,
        "receives_benefits_in_own_right": False,
        "is_looked_after_by_local_authority": False,
        "is_apprentice": False,
        "age_started_or_accepted_current_education_or_training": 17,
        "is_before_universal_credit_qualifying_young_person_terminal_date": False,
        "is_disabled_for_benefits": False,
        "is_enhanced_disabled_for_benefits": False,
        "is_severely_disabled_for_benefits": False,
        "is_blind": False,
        "is_SP_age": False,
        "capital_gains_before_response": 0,
        **inputs,
    }


def simulate(families, year=YEAR, household_ids=None):
    """One model construction for many independent benefit units."""
    situation = {"people": {}, "benunits": {}, "households": {}}
    people = []
    for i, family in enumerate(families):
        members = []
        for j, inputs in enumerate(family):
            name = f"p{i}_{j}"
            situation["people"][name] = {}
            people.append(inputs)
            members.append(name)
        situation["benunits"][f"b{i}"] = {"members": members}
        household = f"h{household_ids[i] if household_ids is not None else i}"
        situation["households"].setdefault(household, {"members": []})[
            "members"
        ].extend(members)
    # Clone the real system, including independent parameters and variables.
    # Reimporting every variable for each example creates thousands of new
    # modules which Hypothesis then repeatedly scans for source constants.
    with patch(
        "policyengine_uk.simulation.CountryTaxBenefitSystem",
        side_effect=_PROPERTY_SYSTEM.clone,
    ):
        sim = Simulation(situation=situation)
    # Scalar situation parsing searches the person ID list for every input.
    # Set whole columns once to keep the exhaustive Cartesian grid tractable.
    variables = people[0].keys()
    assert all(p.keys() == variables for p in people)
    for variable in variables:
        sim.set_input(variable, year, [p[variable] for p in people])
    # Constructor reforms calculate some family flags before these inputs
    # exist. Clear those results, retaining only the supplied columns. This
    # helper tests definitions, not reform amounts or baseline comparisons.
    sim.input_variables = list(variables)
    sim.reset_calculations()
    return sim


def non_advanced_education(p):
    # Encoded proxy for >12 hours' non-advanced education; the enum does not
    # observe hours. https://www.legislation.gov.uk/uksi/2013/376/regulation/5
    return (
        p["current_education"]
        not in {
            "NOT_IN_EDUCATION",
            "TERTIARY",
        }
        and not p["is_apprentice"]
    )


def statutory_child(age):
    # SSCBA s142(1), WRA s40, TCA s8(3), SPC Regulations Sch IIA para 2:
    # https://www.legislation.gov.uk/ukpga/1992/4/section/142
    # https://www.legislation.gov.uk/ukpga/2012/5/section/40
    # https://www.legislation.gov.uk/ukpga/2002/21/section/8
    # https://www.legislation.gov.uk/uksi/2002/1792/schedule/IIA
    return age < 16


def qualifying_young_person(p, programme):
    # Education/training routes only (see omissions in module docstring):
    # CB: https://www.legislation.gov.uk/uksi/2006/223/regulation/3
    # CB own-benefit restriction: https://www.legislation.gov.uk/uksi/2006/223/regulation/8
    # UC: https://www.legislation.gov.uk/uksi/2013/376/regulation/5
    # CTC: https://www.legislation.gov.uk/uksi/2002/2007/regulation/5
    # PC: https://www.legislation.gov.uk/uksi/2002/1792/regulation/4A
    if not 16 <= p["age"] < 20 or p["receives_benefits_in_own_right"]:
        return False
    if not (non_advanced_education(p) or p["is_in_approved_training"]):
        return False
    if (
        p["age"] >= 19
        and p["age_started_or_accepted_current_education_or_training"] >= 19
    ):
        return False
    if programme == "universal_credit" and p["age"] >= 19:
        return p["is_before_universal_credit_qualifying_young_person_terminal_date"]
    return True


def child_or_young_person(p, programme):
    # Encoded responsibility filters, without their statutory exceptions:
    # https://www.legislation.gov.uk/uksi/2013/376/regulation/4
    # https://www.legislation.gov.uk/uksi/2002/2007/regulation/3
    # https://www.legislation.gov.uk/uksi/2002/1792/schedule/IIA
    eligible = statutory_child(p["age"]) or qualifying_young_person(p, programme)
    if programme != "child_benefit" and p["is_looked_after_by_local_authority"]:
        return False
    return eligible


def hbai_dependent_child(p, family):
    # Calculator fallback documented in is_hbai_dependent_child, with the
    # deliberately limited household/education observations described above.
    # https://www.gov.uk/government/statistics/households-below-average-income-for-financial-years-ending-1995-to-2025/households-below-average-income-background-information-and-methodology-report-fye-2025#child
    if p["age"] < 16:
        return True
    if p["is_benunit_head"] or p["is_parent"]:
        return False
    if p["age"] < 18:
        return True
    return (
        p["age"] < 20
        and any(member["is_parent"] and member["age"] >= 16 for member in family)
        and (non_advanced_education(p) or p["is_in_approved_training"])
    )


def claimants_or_partners(family, any_age_gap=20):
    # is_claimant_or_partner's documented rule. The claimant is the head if an
    # HBAI adult, else the eldest HBAI adult. The partner is the eldest other
    # flagged parent, else the eldest other adult not presumed the claimant's
    # child: at least 16 years younger and either under 20 or below a claimant
    # flagged as a parent whose flag no such under-20 member explains, or at
    # least 20 years younger at any age. If the claimant is not a flagged
    # parent but two or more others are, the two eldest of those are the
    # couple instead. Age ties go to the earlier member. any_age_gap=None is
    # the rule without the any-age gap, kept for the differential test.
    n = len(family)
    adult = [not hbai_dependent_child(p, family) for p in family]
    ages = [p["age"] for p in family]
    heads = [i for i in range(n) if family[i]["is_benunit_head"] and adult[i]]
    adults = [i for i in range(n) if adult[i]]
    if not adults:
        return [False] * n
    pool = heads or adults
    claimant = max(pool, key=lambda i: (ages[i], -i))
    parent = [adult[i] and family[i]["is_parent"] for i in range(n)]
    other_parents = [i for i in range(n) if parent[i] and i != claimant]
    if len(other_parents) >= 2 and not parent[claimant]:
        couple = sorted(other_parents, key=lambda i: (-ages[i], i))[:2]
        return [i in couple for i in range(n)]
    young_child = any(ages[j] < 20 and ages[claimant] - ages[j] >= 16 for j in range(n))
    flag_unexplained = parent[claimant] and not young_child

    def presumed_child(i):
        gap = ages[claimant] - ages[i]
        if any_age_gap is not None and gap >= any_age_gap:
            return True
        return (ages[i] < 20 or flag_unexplained) and gap >= 16

    pool = other_parents or [
        i for i in adults if i != claimant and not presumed_child(i)
    ]
    partner = max(pool, key=lambda i: (ages[i], -i)) if pool else None
    return [i == claimant or i == partner for i in range(n)]


def legacy_child_or_young_person(p, claimant):
    # SSCBA s137 and IS reg14 / HB reg19, minus the claimant and partner and
    # anyone placed by a local authority (IS reg16(4), HB reg21(3)):
    # https://www.legislation.gov.uk/uksi/1987/1967/regulation/16
    # https://www.legislation.gov.uk/uksi/2006/213/regulation/21
    return (
        not claimant
        and not p["is_looked_after_by_local_authority"]
        and child_or_young_person(p, "child_benefit")
    )


def wtc_childcare_child(p, family):
    # Annual proxy for reg14(3)-(4), not the precise September/week cutoff:
    # https://www.legislation.gov.uk/uksi/2002/2005/regulation/14
    # https://www.legislation.gov.uk/uksi/2002/2007/regulation/3
    limit = 17 if p["is_disabled_for_benefits"] or p["is_blind"] else 16
    return (
        hbai_dependent_child(p, family)
        and not p["is_looked_after_by_local_authority"]
        and p["age"] < limit
    )


def assert_values(sim, variable, expected, year=YEAR):
    actual = sim.calculate(variable, year)
    if hasattr(actual, "decode_to_str"):
        actual = actual.decode_to_str()
    np.testing.assert_array_equal(actual, expected, err_msg=variable)


def assert_definitions(families, year=YEAR):
    sim = simulate(families, year)
    people = [p for family in families for p in family]
    children = [statutory_child(p["age"]) for p in people]
    # This is the membership input to private-school imputation. A calculator
    # simulation's attends_private_school result is always zero and would
    # therefore be a vacuous test of the imputation's age predicate.
    under_18 = [p["age"] < 18 for p in people]
    assert_values(sim, "age_under_18", under_18, year)
    assert_values(sim, "is_child", under_18, year)
    assert_values(sim, "is_adult", [not child for child in under_18], year)
    assert_values(
        sim,
        "is_in_non_advanced_education",
        [non_advanced_education(p) for p in people],
        year,
    )
    for programme in PROGRAMMES:
        assert_values(sim, f"is_child_for_{programme}", children, year)
        assert_values(
            sim,
            f"is_qualifying_young_person_for_{programme}",
            [qualifying_young_person(p, programme) for p in people],
            year,
        )
        assert_values(
            sim,
            f"is_child_or_qualifying_young_person_for_{programme}",
            [child_or_young_person(p, programme) for p in people],
            year,
        )
    hbai = [hbai_dependent_child(p, family) for family in families for p in family]
    assert_values(sim, "is_hbai_dependent_child", hbai, year)
    assert_values(sim, "is_hbai_adult", [not child for child in hbai], year)
    claimants = [c for family in families for c in claimants_or_partners(family)]
    assert_values(sim, "is_claimant_or_partner", claimants, year)
    # SSCBA s137 and IS reg14 / HB reg19, projected to the encoded family:
    # https://www.legislation.gov.uk/ukpga/1992/4/section/137
    # https://www.legislation.gov.uk/uksi/1987/1967/regulation/14
    # https://www.legislation.gov.uk/uksi/2006/213/regulation/19
    assert_values(
        sim,
        "is_child_or_young_person_for_legacy_benefits",
        [legacy_child_or_young_person(p, c) for p, c in zip(people, claimants)],
        year,
    )
    assert_values(
        sim,
        "is_child_for_working_tax_credit_childcare_element",
        [wtc_childcare_child(p, family) for family in families for p in family],
        year,
    )
    # Financial dependence is unobserved: test the documented membership proxy.
    # https://www.legislation.gov.uk/uksi/2011/1986/regulation/42
    assert_values(
        sim,
        "is_dependent_child_for_student_support",
        [not claimant for claimant in claimants],
        year,
    )
    assert_hbai_partition(sim, people, hbai, year)
    assert_structure(sim, families, year)


def assert_hbai_partition(sim, people, hbai, year=YEAR):
    working = [not child and not p["is_SP_age"] for p, child in zip(people, hbai)]
    pensioners = [not child and p["is_SP_age"] for p, child in zip(people, hbai)]
    assert_values(sim, "is_hbai_working_age_adult", working, year)
    assert_values(sim, "is_hbai_pensioner", pensioners, year)
    assert_values(
        sim,
        "hbai_person_type",
        [
            "CHILD" if child else "PENSIONER" if retired else "WORKING_AGE_ADULT"
            for child, retired in zip(hbai, pensioners)
        ],
        year,
    )
    np.testing.assert_array_equal(
        np.array(hbai, dtype=int) + np.array(working) + np.array(pensioners), 1
    )
    for variable, younger in (
        ("is_hbai_child_under_14", True),
        ("is_hbai_child_aged_14_or_over", False),
    ):
        assert_values(
            sim,
            variable,
            [child and ((p["age"] < 14) == younger) for p, child in zip(people, hbai)],
            year,
        )


def assert_structure(sim, families, year=YEAR):
    claimants = sim.calculate("is_claimant_or_partner", year)
    couple = sim.calculate("is_couple", year)
    single = sim.calculate("is_single", year)
    lone = sim.calculate("is_lone_parent", year)
    single_person = sim.calculate("is_single_person", year)
    np.testing.assert_array_equal(couple ^ single, True)
    np.testing.assert_array_equal(
        couple.astype(int) + lone.astype(int) + single_person.astype(int), 1
    )
    offset = 0
    for i, family in enumerate(families):
        expected = claimants_or_partners(family)
        actual = claimants[offset : offset + len(family)]
        np.testing.assert_array_equal(actual, expected)
        adults = [not hbai_dependent_child(p, family) for p in family]
        assert sum(actual) <= 2
        assert (sum(actual) >= 1) == any(adults)
        assert all(adult for adult, claimant in zip(adults, actual) if claimant)
        assert couple[i] == (sum(expected) >= 2)
        responsible = any(
            legacy_child_or_young_person(p, claimant)
            for p, claimant in zip(family, expected)
        )
        assert lone[i] == (sum(expected) < 2 and responsible)
        # An adult head is the claimant unless two other flagged parents form
        # the couple.
        parents = [
            a and p["is_parent"] and not p["is_benunit_head"]
            for p, a in zip(family, adults)
        ]
        for p, adult, claimant in zip(family, adults, actual):
            if p["is_benunit_head"] and p["age"] >= 16:
                assert adult
                if sum(parents) < 2 or p["is_parent"]:
                    assert claimant
        offset += len(family)


def test_every_age_education_and_structural_flag_combination():
    # 26 ages * 8 education values * 2**5 flags = 6,656 independent families.
    # The matrix includes deliberately unusual inputs: an under-16 head or a
    # student parent must not change the pure statutory under-16 definition.
    families = []
    for age, education, flags in product(
        range(26), EDUCATIONS, product((False, True), repeat=5)
    ):
        subject = person(age, current_education=education, **dict(zip(FLAGS, flags)))
        parent = person(
            40, is_parent=True, is_benunit_head=not subject["is_benunit_head"]
        )
        families.append([parent, subject])
    assert_definitions(families)


def test_entry_terminal_and_wtc_disability_boundaries():
    # Guarantee the age-19 entry/terminal boundaries and the distinct disabled
    # and blind routes at WTC ages 15/16/17, independently of generated draws.
    families = []
    for age, education, entry_age, flags in product(
        range(15, 21),
        ("POST_SECONDARY", "TERTIARY", "NOT_IN_EDUCATION"),
        (18.5, 19, 1000),
        product((False, True), repeat=5),
    ):
        apprentice, terminal, training, disabled, blind = flags
        subject = person(
            age,
            current_education=education,
            age_started_or_accepted_current_education_or_training=entry_age,
            is_apprentice=apprentice,
            is_before_universal_credit_qualifying_young_person_terminal_date=terminal,
            is_in_approved_training=training,
            is_disabled_for_benefits=disabled,
            is_blind=blind,
        )
        families.append([person(40, is_parent=True, is_benunit_head=True), subject])
    assert_definitions(families)


@PROPERTY_SETTINGS
@given(
    st.fixed_dictionaries({flag: st.booleans() for flag in FLAGS}),
    st.booleans(),
    st.booleans(),
    st.booleans(),
    st.booleans(),
    st.booleans(),
    st.sampled_from([0, 16, 17, 18, 18.5, 19, 20, 25, 1000]),
    st.integers(20, 90),
    st.sampled_from([2024, 2026]),
)
def test_programme_definitions_with_generated_entry_and_household_context(
    flags,
    apprentice,
    terminal,
    disabled,
    blind,
    identified_parent,
    entry_age,
    parent_age,
    year,
):
    families = []
    for age, education in product(range(26), EDUCATIONS):
        subject = person(
            age,
            current_education=education,
            **flags,
            is_apprentice=apprentice,
            is_before_universal_credit_qualifying_young_person_terminal_date=terminal,
            is_disabled_for_benefits=disabled,
            is_blind=blind,
            age_started_or_accepted_current_education_or_training=entry_age,
        )
        parent = person(
            parent_age,
            is_parent=identified_parent,
            is_benunit_head=not flags["is_benunit_head"],
            is_SP_age=parent_age >= 66,
        )
        families.append([parent, subject])
    assert_definitions(families, year)


@st.composite
def valid_families(draw):
    families = []
    for _ in range(draw(st.integers(1, 8))):
        adults = draw(st.lists(st.integers(20, 90), min_size=1, max_size=2))
        ages = draw(st.lists(st.integers(0, 19), max_size=5))
        family = [
            person(
                age, is_parent=bool(ages), is_benunit_head=i == 0, is_SP_age=age >= 66
            )
            for i, age in enumerate(adults)
        ]
        for age in ages:
            # The generator creates dependants, not additional claimants:
            # 18--19-year-olds require education/training and a known parent.
            education = draw(st.sampled_from(EDUCATIONS))
            training = draw(st.booleans())
            if age >= 18 and education in {"NOT_IN_EDUCATION", "TERTIARY"}:
                training = True
            family.append(
                person(
                    age, current_education=education, is_in_approved_training=training
                )
            )
        families.append(family)
    return families


@PROPERTY_SETTINGS
@given(valid_families(), st.integers(0, 15))
def test_valid_family_partition_and_adding_a_child_preserves_claimants(
    families, added_age
):
    # Keep every existing input fixed; even an unidentified parent stays so.
    augmented = [family + [person(added_age)] for family in families]
    combined = families + augmented
    sim = simulate(combined)
    assert_structure(sim, combined)
    people = [p for family in combined for p in family]
    hbai = [hbai_dependent_child(p, family) for family in combined for p in family]
    assert_hbai_partition(sim, people, hbai)
    claimants = sim.calculate("is_claimant_or_partner", YEAR)
    old_offset = 0
    new_offset = sum(map(len, families))
    for family in families:
        old = claimants[old_offset : old_offset + len(family)]
        new = claimants[new_offset : new_offset + len(family)]
        np.testing.assert_array_equal(old, claimants_or_partners(family))
        # Every adult is selected, except in an unflagged couple whose head
        # (the claimant) is 20+ years older: the any-age presumption (intended).
        adults = [p for p in family if p["age"] >= 20]
        wide_gap = (
            len(adults) == 2
            and not adults[0]["is_parent"]
            and adults[0]["age"] - adults[1]["age"] >= 20
        )
        assert sum(old) == len(adults) - wide_gap
        assert sum(old) in (1, 2)
        np.testing.assert_array_equal(new, old)
        assert not claimants[new_offset + len(family)]
        old_offset += len(family)
        new_offset += len(family) + 1


def test_calculated_heads_are_claimants_at_16_or_over():
    families = [[person(age)] for age in range(26)]
    families += [[person(16), person(16)], [person(20), person(25)]]
    # The default head is eldest, with ties resolved by member order.
    for family in families:
        for p in family:
            del p["is_benunit_head"]
    sim = simulate(families)
    heads = sim.calculate("is_benunit_head", YEAR)
    claimants = sim.calculate("is_claimant_or_partner", YEAR)
    offset = 0
    for family in families:
        expected_head = max(range(len(family)), key=lambda i: family[i]["age"])
        np.testing.assert_array_equal(
            heads[offset : offset + len(family)],
            [i == expected_head for i in range(len(family))],
        )
        if family[expected_head]["age"] >= 16:
            assert claimants[offset + expected_head]
        offset += len(family)


@st.composite
def arbitrary_benefit_units(draw):
    # Any ages, education, parent flags and head position: not only the
    # shapes the FRS produces.
    families = []
    for _ in range(draw(st.integers(1, 8))):
        size = draw(st.integers(1, 6))
        head = draw(st.integers(0, size - 1))
        families.append(
            [
                person(
                    draw(st.integers(0, 90)),
                    current_education=draw(st.sampled_from(EDUCATIONS)),
                    is_in_approved_training=draw(st.booleans()),
                    is_parent=draw(st.booleans()),
                    is_benunit_head=i == head,
                )
                for i in range(size)
            ]
        )
    return families


@PROPERTY_SETTINGS
@given(arbitrary_benefit_units())
def test_any_benefit_unit_has_at_most_two_claimants_or_partners(families):
    assert_structure(simulate(families), families)


@st.composite
def shim_populations(draw):
    members = st.fixed_dictionaries(
        {
            "age": st.integers(0, 90),
            "current_education": st.sampled_from(EDUCATIONS),
            "is_disabled_for_benefits": st.booleans(),
            "is_enhanced_disabled_for_benefits": st.booleans(),
            "is_severely_disabled_for_benefits": st.booleans(),
            "is_SP_age": st.booleans(),
            "person_id": st.integers(0, 20),
            "capital_gains_before_response": st.integers(0, 100_000),
        }
    )
    raw = draw(
        st.lists(st.lists(members, min_size=1, max_size=7), min_size=1, max_size=8)
    )
    return [[person(**p) for p in family] for family in raw]


def frozen_rank(people, value, eligible, excluded):
    """Stable descending rank, using Python sorting independently of core."""
    ordered = sorted(
        (i for i, p in enumerate(people) if eligible(p)),
        key=lambda i: -people[i][value],
    )
    result = [excluded] * len(people)
    for rank, i in enumerate(ordered, start=1):
        result[i] = rank
    return result


@PROPERTY_SETTINGS
@given(shim_populations())
def test_all_deprecated_shims_and_explicit_age_ranks_keep_frozen_semantics(families):
    # Always exercise both empty subgroups, all 0--25 age boundaries, stable
    # ties, and the frozen distinction between exactly two and three adults.
    families += [
        [person(age, person_id=age + 1) for age in range(26)],
        [person(18, person_id=1)],
        [person(18, person_id=1), person(18, person_id=2)],
        [person(18, person_id=i) for i in range(3)],
        [person(0, person_id=3), person(1, person_id=1), person(1, person_id=2)],
    ]
    # Two benefit units share each household: adult ranks must not restart at
    # a benefit-unit boundary, whereas child ranks and counts must do so.
    household_ids = [i // 2 for i in range(len(families))]
    sim = simulate(families, household_ids=household_ids)
    people = [p for family in families for p in family]
    expected = {
        "is_child": [p["age"] < 18 for p in people],
        "is_adult": [p["age"] >= 18 for p in people],
        "age_under_18": [p["age"] < 18 for p in people],
        "is_WA_adult": [p["age"] >= 18 and not p["is_SP_age"] for p in people],
        "is_young_child": [p["age"] < 14 for p in people],
        "is_older_child": [14 <= p["age"] < 18 for p in people],
    }
    for family in families:
        ages = [p["age"] for p in family]
        children = [age for age in ages if age < 18]
        adults = [age for age in ages if age >= 18]
        group_values = {
            "num_children": len(children),
            "benunit_count_children": len(children),
            "num_adults": len(adults),
            "benunit_count_adults": len(adults),
            "eldest_child_age": max(children, default=-np.inf),
            "youngest_child_age": min(children, default=np.inf),
            "eldest_adult_age": max(adults, default=-np.inf),
            "youngest_adult_age": min(adults, default=np.inf),
            "family_type": (
                "COUPLE_WITH_CHILDREN" if children else "COUPLE_NO_CHILDREN"
            )
            if len(adults) == 2
            else ("LONE_PARENT" if children else "SINGLE"),
        }
        for suffix in ("disabled", "enhanced_disabled", "severely_disabled"):
            for group, child in (("children", True), ("adults", False)):
                group_values[f"num_{suffix}_{group}"] = sum(
                    ((p["age"] < 18) == child) and p[f"is_{suffix}_for_benefits"]
                    for p in family
                )
        for variable, value in group_values.items():
            expected.setdefault(variable, []).append(value)
        ranks = frozen_rank(family, "age", lambda p: p["age"] < 18, -1)
        expected.setdefault("child_index", []).extend(ranks)
        # Frozen oddity: every member of a childless family is "eldest child".
        expected.setdefault("is_eldest_child", []).extend(
            not children or rank == 1 for rank in ranks
        )
        # Frozen oddity: a younger child's larger ID can leave tied eldest
        # children with no selected eldest. Do not silently fix this shim.
        eldest = max(children, default=-np.inf)
        tied = children.count(eldest) > 1
        max_child_id = max(p["person_id"] if p["age"] < 18 else 0 for p in family)
        expected.setdefault("is_benunit_eldest_child", []).extend(
            p["age"] == eldest and (not tied or p["person_id"] == max_child_id)
            for p in family
        )
    households = {}
    for household, family in zip(household_ids, families):
        households.setdefault(household, []).extend(family)
    for variable, value in (
        ("adult_index", "age"),
        ("adult_index_cg", "capital_gains_before_response"),
    ):
        expected[variable] = [
            rank
            for household in households.values()
            for rank in frozen_rank(household, value, lambda p: p["age"] >= 18, 0)
        ]
    for variable, values in expected.items():
        assert_values(sim, variable, values)


@PROPERTY_SETTINGS
@given(st.integers(0, 15), st.sampled_from(EDUCATIONS), st.booleans())
def test_adding_a_child_without_identifying_parents_preserves_existing_members(
    added_age, education, training
):
    families = [
        [
            person(24, is_benunit_head=True),
            person(age, current_education=education, is_in_approved_training=training),
        ]
        for age in range(16, 20)
    ]
    combined = families + [family + [person(added_age)] for family in families]
    sim = simulate(combined)
    actual = sim.calculate("is_claimant_or_partner", YEAR)
    for i in range(len(families)):
        np.testing.assert_array_equal(
            actual[2 * i : 2 * i + 2], actual[8 + 3 * i : 10 + 3 * i]
        )


def test_parent_marked_under_16_entrant_preserves_existing_claimants():
    # Executed and minimised: 20 is the smallest ordinary-adult age in our
    # family generator, 18 the first affected student age, and 0 the smallest
    # entrant age. Before: claimants [True, True]. After: [True, False, False].
    # The entrant is itself an HBAI dependent child despite its parent marker.
    family = [
        person(20, is_benunit_head=True),
        person(18, current_education="POST_SECONDARY"),
    ]
    entrant = family + [person(0, is_parent=True)]
    sim = simulate([family, entrant])
    actual = sim.calculate("is_claimant_or_partner", YEAR)
    np.testing.assert_array_equal(actual[:2], actual[2:4])
    # The reference ignores a parent flag under 16, as the model does.
    expected = claimants_or_partners(family) + claimants_or_partners(entrant)
    np.testing.assert_array_equal(actual, expected)


@st.composite
def flagged_claimant_units(draw):
    # A head flagged as a parent, with unflagged others no older than them, of
    # any education and training. Half the units have no member under 20, so
    # nothing explains the flag.
    families = []
    for _ in range(draw(st.integers(1, 8))):
        claimant_age = draw(st.integers(32, 90))
        youngest = draw(st.sampled_from([0, 20]))
        family = [person(claimant_age, is_parent=True, is_benunit_head=True)]
        for _ in range(draw(st.integers(1, 4))):
            family.append(
                person(
                    draw(st.integers(youngest, claimant_age)),
                    current_education=draw(st.sampled_from(EDUCATIONS)),
                    is_in_approved_training=draw(st.booleans()),
                )
            )
        families.append(family)
    return families


@PROPERTY_SETTINGS
@given(flagged_claimant_units())
def test_member_far_below_a_flagged_claimant_is_never_their_partner(families):
    # Unless a member under 20 and 16+ years younger explains the flag, every
    # member 16+ years below the flagged claimant is their child at any age.
    # With such a member, the under-20 limit stays.
    sim = simulate(families)
    assert_structure(sim, families)
    claimants = sim.calculate("is_claimant_or_partner", YEAR)
    offset = 0
    for family in families:
        claimant_age = family[0]["age"]
        explained = any(
            p["age"] < 20 and claimant_age - p["age"] >= 16 for p in family[1:]
        )
        assert claimants[offset]
        for j, p in enumerate(family[1:], start=1):
            if claimant_age - p["age"] >= 16 and (p["age"] < 20 or not explained):
                assert not claimants[offset + j]
        offset += len(family)


@st.composite
def unflagged_units_with_adult_head(draw):
    families = []
    for _ in range(draw(st.integers(1, 8))):
        family = [person(draw(st.integers(20, 90)), is_benunit_head=True)]
        for _ in range(draw(st.integers(0, 4))):
            family.append(
                person(
                    draw(st.integers(0, 90)),
                    current_education=draw(st.sampled_from(EDUCATIONS)),
                    is_in_approved_training=draw(st.booleans()),
                )
            )
        families.append(family)
    return families


@PROPERTY_SETTINGS
@given(unflagged_units_with_adult_head())
def test_flagging_the_claimant_as_a_parent_never_adds_a_partner(families):
    # Metamorphic: the same units before and after flagging the head (the
    # claimant) as a parent. The flag can only remove members from the partner
    # pool, so the claimant stays and the count of claimants and partners
    # never rises. Any partner left is under 16 years younger, unless a member
    # under 20 and 16+ years younger explains the flag.
    flagged = [[{**family[0], "is_parent": True}] + family[1:] for family in families]
    combined = families + flagged
    sim = simulate(combined)
    assert_structure(sim, combined)
    claimants = sim.calculate("is_claimant_or_partner", YEAR)
    n = sum(map(len, families))
    before_offset, after_offset = 0, n
    for family in families:
        before = claimants[before_offset : before_offset + len(family)]
        after = claimants[after_offset : after_offset + len(family)]
        assert before[0] and after[0]
        assert after.sum() <= before.sum()
        explained = any(
            p["age"] < 20 and family[0]["age"] - p["age"] >= 16 for p in family[1:]
        )
        for p, partner in zip(family[1:], after[1:]):
            if partner and not explained:
                assert family[0]["age"] - p["age"] < 16
        before_offset += len(family)
        after_offset += len(family)


@st.composite
def frs_shaped_units(draw):
    # The FRS's benefit unit: one adult or a couple (any ages and gap, either
    # one the head), plus dependants; every adult is flagged as a parent if and
    # only if there are dependants (policyengine-uk-data's is_parent).
    families = []
    for _ in range(draw(st.integers(1, 8))):
        adults = draw(st.lists(st.integers(16, 90), min_size=1, max_size=2))
        dependants = draw(st.lists(st.integers(0, 19), max_size=4))
        head = draw(st.integers(0, len(adults) - 1))
        family = [
            person(age, is_parent=bool(dependants), is_benunit_head=i == head)
            for i, age in enumerate(adults)
        ]
        for age in dependants:
            family.append(
                person(
                    age,
                    current_education=draw(st.sampled_from(EDUCATIONS)),
                    is_in_approved_training=draw(st.booleans()),
                )
            )
        families.append(family)
    return families


def survey_roles(family):
    # The FRS adult table: everyone in a unit without dependants (nobody is
    # flagged), otherwise the adults flagged as parents.
    flagged = any(p["is_parent"] for p in family)
    return [p["is_parent"] or not flagged for p in family]


def childless_couple_split_by_any_age_gap(family):
    # A childless two-adult unit whose head (the claimant) is 20+ years older.
    if len(family) != 2 or not all(survey_roles(family)):
        return False
    head, other = sorted(family, key=lambda p: not p["is_benunit_head"])
    return head["age"] - other["age"] >= 20


@PROPERTY_SETTINGS
@given(frs_shaped_units())
def test_frs_shaped_units_change_only_for_childless_couples_20_years_apart(families):
    # Differential against the rule without the any-age gap. On FRS-shaped
    # units the two can differ only in childless two-adult units 20 or more
    # years apart, which carry no flags: there, if the claimant (the head) is
    # the elder, the younger adult is presumed their child (intended); a
    # younger head keeps the couple. A dataset that carries
    # is_claimant_or_partner (policyengine-uk-data#524's enhanced FRS) does not
    # depend on this; datasets without the role do.
    sim = simulate(families)
    expected = [c for family in families for c in claimants_or_partners(family)]
    assert_values(sim, "is_claimant_or_partner", expected)
    for family in families:
        if not childless_couple_split_by_any_age_gap(family):
            assert claimants_or_partners(family) == claimants_or_partners(
                family, any_age_gap=None
            )


@PROPERTY_SETTINGS
@given(frs_shaped_units())
def test_supplied_claimant_and_partner_roles_are_kept(families):
    # policyengine-uk-data#524 supplies is_claimant_or_partner from the FRS
    # adult table: the head and any partner, whatever their ages and gap. Supplied
    # roles override the presumption, so the FRS couples it would split stay
    # couples, and every unit keeps one claimant and at most one partner.
    roles = [role for family in families for role in survey_roles(family)]
    sim = simulate(families)
    sim.set_input("is_claimant_or_partner", YEAR, roles)
    assert_values(sim, "is_claimant_or_partner", roles)
    is_couple = sim.calculate("is_couple", YEAR)
    offset = 0
    for i, family in enumerate(families):
        n_roles = sum(roles[offset : offset + len(family)])
        assert is_couple[i] == (n_roles == 2)
        offset += len(family)


def test_unflagged_adult_pairs_follow_the_20_year_gap():
    # Exhaustive over unflagged two-adult units, both 20 to 90, head the
    # elder: the younger is the partner exactly when under 20 years younger.
    pairs = [(a, b) for a in range(20, 91) for b in range(20, a + 1)]
    families = [[person(a, is_benunit_head=True), person(b)] for a, b in pairs]
    sim = simulate(families)
    claimants = sim.calculate("is_claimant_or_partner", YEAR)
    expected = [c for a, b in pairs for c in (True, a - b < 20)]
    np.testing.assert_array_equal(claimants, expected)
    assert expected == [c for f in families for c in claimants_or_partners(f)]


def test_wide_gap_couples_by_head_order_and_with_supplied_roles():
    # An unflagged couple 25 years apart: with the elder as head (the claimant)
    # the younger is presumed their child; with the younger as head the elder
    # is the partner. Supplied roles keep the couple either way.
    elder_head = [person(70, is_benunit_head=True), person(45)]
    younger_head = [person(45, is_benunit_head=True), person(70)]
    families = [elder_head, younger_head]
    sim = simulate(families)
    inferred = sim.calculate("is_claimant_or_partner", YEAR)
    np.testing.assert_array_equal(inferred, [True, False, True, True])
    assert claimants_or_partners(elder_head) == [True, False]
    assert claimants_or_partners(younger_head) == [True, True]
    supplied = simulate(families)
    supplied.set_input("is_claimant_or_partner", YEAR, [True] * 4)
    np.testing.assert_array_equal(supplied.calculate("is_couple", YEAR), [True] * 2)
