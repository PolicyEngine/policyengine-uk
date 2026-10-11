"""Each Council Tax Reduction scheme's own young person.

Scotland's working-age scheme, from 1 April 2022, defines a young person as a
Universal Credit qualifying young person (Council Tax Reduction (Scotland)
Regulations 2021 reg. 6(1); UC Regs 2013 reg. 5). England, Wales and
Scotland's pension-age scheme use the Child Benefit qualifying young person
(SI 2012/2885 reg. 2; WSI 2013/3029 reg. 2; SSI 2012/319 reg. 4), as Scotland's
working-age scheme did until 31 March 2022 (SSI 2012/303 reg. 4). Every scheme
makes a child a person under 16, and no applicant is responsible for
themselves or their partner (SSI 2021/249 reg. 7(2)-(3)).

Invariants:

1. Scheme selection. The Council Tax Reduction flag is the Universal Credit
   test (a child or qualifying young person who is not looked after and not
   the claimant or partner) exactly where the family is in Scotland, is not a
   pensioner for Council Tax Reduction and the year is 2022-23 or later.
   Everywhere else it is the legacy (Child Benefit) flag. Checked over
   every combination of the inputs the two definitions read, and over
   generated benefit units of any shape.
2. No claimant or partner is their own benefit unit's child or young person,
   under any scheme.
3. A member under 16 who is not looked after is in the family under every
   scheme.
4. Where a member's Universal Credit and Child Benefit statuses agree, the
   flag does not depend on the country, the pensioner test or the year.
5. A lone parent is a single claimant with at least one such member, and the
   working-age applicable amount of a family with no premiums is the personal
   allowance the table gives for a couple, a lone parent or a single person,
   for 52 weeks.
6. The applicant's own earnings count under every scheme (SSI 2021/249 reg.
   36(1)). A household head aged 18 or 19 who applies alone was reached by
   the income mask only as a Child Benefit young person; they stay in the
   means test where Scotland's working-age scheme does not read them as a
   young person. A member who is not the applicant counts only as that
   scheme's young person.

The pensioner test and the claimant and partner are supplied, so these tests
exercise the young person rule alone; the YAML cases use the derived tests.
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

_PROPERTY_SYSTEM = system.clone()
EDUCATIONS = tuple(item.name for item in EducationType)
COUNTRIES = ("ENGLAND", "WALES", "SCOTLAND", "NORTHERN_IRELAND")
# 2021-22 is the last year of SSI 2012/303; SSI 2021/249 applies from 2022-23.
YEARS = (2021, 2022, 2026)
SETTINGS = settings(
    max_examples=25,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)

member = st.fixed_dictionaries(
    {
        "age": st.integers(0, 25),
        "current_education": st.sampled_from(EDUCATIONS),
        "is_in_approved_training": st.booleans(),
        "receives_benefits_in_own_right": st.booleans(),
        "is_looked_after_by_local_authority": st.booleans(),
        "is_before_universal_credit_qualifying_young_person_terminal_date": (
            st.booleans()
        ),
        "age_started_or_accepted_current_education_or_training": st.sampled_from(
            [17, 1000]
        ),
    }
)
claimant = st.fixed_dictionaries(
    {
        "age": st.integers(16, 70),
        "current_education": st.sampled_from(EDUCATIONS),
        "is_in_approved_training": st.booleans(),
        "receives_benefits_in_own_right": st.just(False),
        "is_looked_after_by_local_authority": st.just(False),
        "is_before_universal_credit_qualifying_young_person_terminal_date": (
            st.booleans()
        ),
        "age_started_or_accepted_current_education_or_training": st.sampled_from(
            [17, 1000]
        ),
    }
)


@st.composite
def families(draw):
    claimants = draw(st.lists(claimant, min_size=1, max_size=2))
    others = draw(st.lists(member, max_size=4))
    return {
        "country": draw(st.sampled_from(COUNTRIES)),
        "pensioner": draw(st.booleans()),
        "members": [dict(p, is_claimant_or_partner=True) for p in claimants]
        + [dict(p, is_claimant_or_partner=False) for p in others],
    }


def simulate(units, year):
    situation = {"people": {}, "benunits": {}, "households": {}}
    people = []
    for i, unit in enumerate(units):
        names = []
        for j, inputs in enumerate(unit["members"]):
            name = f"p{i}_{j}"
            situation["people"][name] = {}
            people.append(inputs)
            names.append(name)
        situation["benunits"][f"b{i}"] = {"members": names}
        situation["households"][f"h{i}"] = {"members": names}
    with patch(
        "policyengine_uk.simulation.CountryTaxBenefitSystem",
        side_effect=_PROPERTY_SYSTEM.clone,
    ):
        sim = Simulation(situation=situation)
    for variable in people[0]:
        sim.set_input(variable, year, [p[variable] for p in people])
    sim.set_input("country", year, [unit["country"] for unit in units])
    sim.set_input(
        "council_tax_reduction_pensioner", year, [unit["pensioner"] for unit in units]
    )
    sim.input_variables = list(people[0]) + [
        "country",
        "council_tax_reduction_pensioner",
    ]
    sim.reset_calculations()
    return sim


def per_person(units, key):
    return np.array([unit[key] for unit in units for _ in unit["members"]])


def follows_universal_credit(unit, year):
    return unit["country"] == "SCOTLAND" and not unit["pensioner"] and year >= 2022


def assert_scheme_selection(units, year):
    sim = simulate(units, year)
    people = [p for unit in units for p in unit["members"]]
    claimant_or_partner = np.array([p["is_claimant_or_partner"] for p in people])
    looked_after = np.array([p["is_looked_after_by_local_authority"] for p in people])
    under_16 = np.array([p["age"] < 16 for p in people])
    flag = sim.calculate("is_child_or_young_person_for_council_tax_reduction", year)
    legacy = sim.calculate("is_child_or_young_person_for_legacy_benefits", year)
    universal_credit = (
        (
            under_16
            | sim.calculate("is_qualifying_young_person_for_universal_credit", year)
        )
        & ~looked_after
        & ~claimant_or_partner
    )
    scottish = np.array(
        [
            follows_universal_credit(unit, year)
            for unit in units
            for _ in unit["members"]
        ]
    )
    # Invariant 1.
    np.testing.assert_array_equal(flag, np.where(scottish, universal_credit, legacy))
    # Invariant 2.
    assert not (flag & claimant_or_partner).any()
    # Invariant 3.
    assert flag[under_16 & ~looked_after & ~claimant_or_partner].all()
    return flag, legacy, scottish


@SETTINGS
@given(st.lists(families(), min_size=1, max_size=6), st.sampled_from(YEARS))
def test_each_scheme_reads_its_own_young_person(units, year):
    # Benefit units of any shape, where a claimant or partner can also be a
    # qualifying young person.
    assert_scheme_selection(units, year)


def test_scheme_selection_over_every_combination():
    # Ages 14 to 21, every education value, training, own-right benefits,
    # looked-after status, the Universal Credit terminal date and the entry
    # age, under each country and pensioner test, in each year: 2,048
    # subjects * 8 schemes * 3 years, each with a claimant aged 45, and again
    # as the claimant of a benefit unit of their own.
    adult = {
        "age": 45,
        "current_education": "NOT_IN_EDUCATION",
        "is_in_approved_training": False,
        "receives_benefits_in_own_right": False,
        "is_looked_after_by_local_authority": False,
        "is_before_universal_credit_qualifying_young_person_terminal_date": False,
        "age_started_or_accepted_current_education_or_training": 1000,
        "is_claimant_or_partner": True,
    }
    subjects = [
        {
            "age": age,
            "current_education": education,
            "is_in_approved_training": training,
            "receives_benefits_in_own_right": own_right,
            "is_looked_after_by_local_authority": looked_after,
            "is_before_universal_credit_qualifying_young_person_terminal_date": (
                terminal
            ),
            "age_started_or_accepted_current_education_or_training": entry_age,
            "is_claimant_or_partner": False,
        }
        for age in range(14, 22)
        for education in EDUCATIONS
        for training in (False, True)
        for own_right in (False, True)
        for looked_after in (False, True)
        for terminal in (False, True)
        for entry_age in (17, 1000)
    ]
    units = [
        {"country": country, "pensioner": pensioner, "members": [adult, subject]}
        for subject in subjects
        for country in COUNTRIES
        for pensioner in (False, True)
    ]
    # The same subjects as the claimant of a benefit unit of their own: never
    # their own child or young person, under any scheme (invariant 2).
    alone = [
        {
            "country": country,
            "pensioner": pensioner,
            "members": [dict(subject, is_claimant_or_partner=True)],
        }
        for subject in subjects
        for country in COUNTRIES
        for pensioner in (False, True)
    ]
    for year in YEARS:
        flag, legacy, scottish = assert_scheme_selection(units, year)
        differs = flag != legacy
        # The Universal Credit definition applies nowhere before 2022-23, and
        # only in Scotland's working-age scheme after it.
        assert not differs[~scottish].any()
        # Not vacuous: from 2022-23 the two definitions do part there.
        assert differs.any() == (year >= 2022)
        own_flag, _, _ = assert_scheme_selection(alone, year)
        assert not own_flag.any()
        # Not vacuous: some of those lone claimants are qualifying young
        # persons by status, in Scotland's working-age scheme too.
        sim = simulate(alone, year)
        status = sim.calculate("is_qualifying_young_person_for_universal_credit", year)
        scottish_alone = np.array(
            [follows_universal_credit(unit, year) for unit in alone]
        )
        assert status.any()
        assert (status & scottish_alone).any() == (year >= 2022)


@SETTINGS
@given(st.lists(families(), min_size=1, max_size=4))
def test_schemes_differ_only_where_the_two_definitions_differ(units):
    # Invariant 4: the same members under every country, pensioner test and
    # year. The flags can differ only for a member whose Universal Credit and
    # Child Benefit qualifying young person statuses differ in that year.
    variants = [
        dict(unit, country=country, pensioner=pensioner)
        for unit in units
        for country in COUNTRIES
        for pensioner in (False, True)
    ]
    size = len(COUNTRIES) * 2
    for year in YEARS:
        sim = simulate(variants, year)
        flag = sim.calculate("is_child_or_young_person_for_council_tax_reduction", year)
        agree = sim.calculate(
            "is_qualifying_young_person_for_universal_credit", year
        ) == sim.calculate("is_qualifying_young_person_for_child_benefit", year)
        offset = 0
        for unit in units:
            n = len(unit["members"])
            block = flag[offset : offset + size * n].reshape(size, n)
            same = agree[offset : offset + n]
            assert (block[:, same] == block[0, same]).all()
            offset += size * n


@SETTINGS
@given(st.lists(families(), min_size=1, max_size=6), st.sampled_from(YEARS))
def test_lone_parent_and_working_age_personal_allowance(units, year):
    # Invariant 5, from the allowance table alone.
    units = [dict(unit, pensioner=False) for unit in units]
    sim = simulate(units, year)
    allowances = sim.tax_benefit_system.parameters(
        f"{year}-06-01"
    ).gov.dwp.housing_benefit.allowances
    flag = sim.calculate("is_child_or_young_person_for_council_tax_reduction", year)
    lone_parent = sim.calculate("is_council_tax_reduction_lone_parent", year)
    couple = sim.calculate("is_couple", year)
    amount = sim.calculate("council_tax_reduction_applicable_amount", year)
    premiums = sim.calculate("working_age_benefits_premiums", year)
    offset = 0
    for i, unit in enumerate(units):
        n = len(unit["members"])
        claimant_ages = [
            p["age"] for p in unit["members"] if p["is_claimant_or_partner"]
        ]
        responsible = bool(flag[offset : offset + n].any())
        offset += n
        assert couple[i] == (len(claimant_ages) == 2)
        assert lone_parent[i] == (len(claimant_ages) == 1 and responsible)
        eldest = max(claimant_ages)
        if len(claimant_ages) == 2:
            weekly = (
                allowances.couple.younger
                if eldest < allowances.age_threshold.younger
                else allowances.couple.older
            )
        elif responsible:
            weekly = (
                allowances.lone_parent.younger
                if eldest < allowances.age_threshold.younger
                else allowances.lone_parent.older
            )
        else:
            weekly = (
                allowances.single.younger
                if eldest < allowances.age_threshold.older
                else allowances.single.older
            )
        np.testing.assert_allclose(amount[i] - premiums[i], weekly * 52, rtol=1e-6)


def test_scottish_working_age_differs_from_child_benefit_at_19():
    # Not vacuous: past the Universal Credit terminal date a 19-year-old at
    # school is a Child Benefit young person and not a Universal Credit one,
    # so the Scottish working-age flag is a different rule from the legacy
    # flag. Before the date the two agree.
    base = {
        "current_education": "UPPER_SECONDARY",
        "is_in_approved_training": False,
        "receives_benefits_in_own_right": False,
        "is_looked_after_by_local_authority": False,
        "age_started_or_accepted_current_education_or_training": 17,
    }
    adult = dict(
        base,
        age=45,
        current_education="NOT_IN_EDUCATION",
        is_before_universal_credit_qualifying_young_person_terminal_date=False,
        is_claimant_or_partner=True,
    )
    past = dict(
        base,
        age=19,
        is_before_universal_credit_qualifying_young_person_terminal_date=False,
        is_claimant_or_partner=False,
    )
    before = dict(
        past, is_before_universal_credit_qualifying_young_person_terminal_date=True
    )
    units = [
        {"country": country, "pensioner": pensioner, "members": [adult, young]}
        for country in COUNTRIES
        for pensioner in (False, True)
        for young in (past, before)
    ]
    sim = simulate(units, 2026)
    flag = sim.calculate("is_child_or_young_person_for_council_tax_reduction", 2026)
    young = flag[1::2]
    expected = [
        not (
            unit["country"] == "SCOTLAND"
            and not unit["pensioner"]
            and not unit["members"][1][
                "is_before_universal_credit_qualifying_young_person_terminal_date"
            ]
        )
        for unit in units
    ]
    np.testing.assert_array_equal(young, expected)
    assert not all(expected) and any(expected)


def test_applicants_own_earnings_count_under_every_scheme():
    # Invariant 6. Parents aged 45 and 46 are the benefit unit's claimant and
    # partner; with them lives a member aged 18 or 19 at school or in approved
    # training. Either that member heads the household, is liable for the
    # council tax and applies alone, or the father heads it and the member is
    # only a possible young person of the family. No benefit is claimed, and
    # the earnings are below the income tax and National Insurance thresholds,
    # so the applicable income is the earnings that count.
    year, earnings = 2026, 9_000
    cases = list(
        product(
            ("ENGLAND", "WALES", "SCOTLAND"),
            (18, 19),
            (False, True),  # approved training, or school
            (False, True),  # before the Universal Credit terminal date
            (False, True),  # the member heads the household
        )
    )
    situation = {"people": {}, "benunits": {}, "households": {}}
    for i, (country, age, training, before, heads) in enumerate(cases):
        situation["people"][f"member{i}"] = {
            "age": {year: age},
            "is_household_head": {year: heads},
            "is_claimant_or_partner": {year: False},
            "current_education": {
                year: "NOT_IN_EDUCATION" if training else "UPPER_SECONDARY"
            },
            "is_in_approved_training": {year: training},
            "age_started_or_accepted_current_education_or_training": {year: 17},
            "is_before_universal_credit_qualifying_young_person_terminal_date": {
                year: before
            },
            "employment_income": {year: earnings},
        }
        for parent, parent_age in (("father", 45), ("mother", 46)):
            situation["people"][f"{parent}{i}"] = {
                "age": {year: parent_age},
                "is_household_head": {year: parent == "father" and not heads},
                "is_claimant_or_partner": {year: True},
            }
        names = [f"member{i}", f"father{i}", f"mother{i}"]
        situation["benunits"][f"b{i}"] = {
            "members": names,
            "would_claim_uc": {year: False},
            "would_claim_child_benefit": {year: False},
        }
        situation["households"][f"h{i}"] = {
            "members": names,
            "country": {year: country},
        }
    with patch(
        "policyengine_uk.simulation.CountryTaxBenefitSystem",
        side_effect=_PROPERTY_SYSTEM.clone,
    ):
        sim = Simulation(situation=situation)
    applicant = sim.calculate("is_council_tax_reduction_applicant_or_partner", year)
    heads = np.array([case[4] for case in cases])
    # Where the member heads the household they are the applicant, alone.
    np.testing.assert_array_equal(applicant[0::3], heads)
    np.testing.assert_array_equal(applicant[1::3], ~heads)
    young_person = sim.calculate(
        "is_child_or_young_person_for_council_tax_reduction", year
    )[0::3]
    income = sim.calculate("council_tax_reduction_applicable_income", year)
    np.testing.assert_allclose(income, earnings * (heads | young_person), atol=0.01)
    # The applicant's earnings count in every case.
    np.testing.assert_allclose(income[heads], earnings, atol=0.01)
    # Not vacuous: some applicants are not young persons under their scheme,
    # and a member who is neither does not count.
    assert (heads & ~young_person).any()
    assert (income[~heads & ~young_person] == 0).all()
    assert (~heads & ~young_person).any() and (~heads & young_person).any()
