"""Programme definitions, benefit-unit structure and frozen age-18 shims.

Invariants:

1. For every age 0--25, education enum and combination of head, parent,
   approved training, own-benefit receipt and looked-after status, the four
   programmes' child predicates mean under 16. Their young-person predicates
   agree with the statutory age/education/entry conditions the model encodes.
   Legacy children are Child Benefit children/QYPs other than claimants and
   partners; the HBAI fallback follows its documented structural assumptions.
2. HBAI types partition everyone. Valid families (one or two adults aged 20+
   and dependants) have one or two claimants/partners; couple/single and
   couple/lone-parent/single-person partition benefit units. Heads aged 16+
   are claimants or partners, including when explicitly younger than others.
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
extensions are omitted, as are UC's unconditional age-16-to-next-September
route and PC's (an input that defaults to false). UC's and PC's September
terminal dates are one input.
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
import pytest
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
    if programme in ("universal_credit", "pension_credit") and p["age"] >= 19:
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
        and any(member["is_parent"] for member in family)
        and (non_advanced_education(p) or p["is_in_approved_training"])
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
    assert_values(sim, "is_claimant_or_partner", [not child for child in hbai], year)
    # SSCBA s137 and IS reg14 / HB reg19, projected to the encoded family:
    # https://www.legislation.gov.uk/ukpga/1992/4/section/137
    # https://www.legislation.gov.uk/uksi/1987/1967/regulation/14
    # https://www.legislation.gov.uk/uksi/2006/213/regulation/19
    assert_values(
        sim,
        "is_child_or_young_person_for_legacy_benefits",
        [
            child and child_or_young_person(p, "child_benefit")
            for p, child in zip(people, hbai)
        ],
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
    assert_values(sim, "is_dependent_child_for_student_support", hbai, year)
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
        expected = [not hbai_dependent_child(p, family) for p in family]
        actual = claimants[offset : offset + len(family)]
        np.testing.assert_array_equal(actual, expected)
        assert couple[i] == (sum(expected) >= 2)
        responsible = any(
            not claimant and child_or_young_person(p, "child_benefit")
            for p, claimant in zip(family, expected)
        )
        assert lone[i] == (sum(expected) < 2 and responsible)
        for p, claimant in zip(family, actual):
            if p["is_benunit_head"] and p["age"] >= 16:
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
        assert sum(old) == sum(p["age"] >= 20 for p in family)
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
    sim = simulate([family, family + [person(0, is_parent=True)]])
    actual = sim.calculate("is_claimant_or_partner", YEAR)
    np.testing.assert_array_equal(actual[:2], actual[2:4])
