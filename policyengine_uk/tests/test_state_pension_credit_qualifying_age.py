"""The qualifying age for State Pension Credit, and Class 4 liability by age.

State Pension Credit Act 2002 s.1(6): the qualifying age is a woman's
pensionable age, and for a man the pensionable age of a woman born on the same
day. The model is checked against the day-level reading of Pensions Act 1995
Sch 4 para 1 in test_state_pension_age, which shares no code with the model:
a man's qualifying day is that reference's day for a woman born on his birthday.

Class 4: Social Security (Contributions) Regulations 2001 reg 91(a) excepts a
person over pensionable age at the beginning of the year of assessment (6
April), so someone who reaches it during a year is liable for that whole year.
"""

from datetime import date

import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation
from policyengine_uk.tests.test_state_pension_age import (
    YEARS,
    differential_simulation,
    grid_months,
    grid_months_to_date,
    reference_attainment_day,
)

# Men born before this date have a pensionable age of 65 (Sch 4 para 1 rule
# (1)); for everyone else pensionable age and the qualifying age coincide.
MALE_RULE_BORN_BEFORE = date(1953, 12, 6)
# The last fiscal year in which the two can differ: men born on 5 December 1953
# reach 65 on 5 December 2018.
LAST_YEAR_THEY_DIFFER = 2018


def reference_qualifying_day(birth: date) -> date:
    """The day a person reaches the qualifying age for State Pension Credit:
    the day a woman born on the same day attains pensionable age."""
    return reference_attainment_day(birth, male=False)


def one_person_units(people: dict) -> dict:
    """A situation with each person in their own benefit unit and household."""
    return {
        "people": people,
        "benunits": {f"b_{name}": {"members": [name]} for name in people},
        "households": {f"h_{name}": {"members": [name]} for name in people},
    }


@pytest.mark.parametrize("year", YEARS)
def test_qualifying_age_matches_statute_for_every_birth_date(year):
    """For births every third day from 1945 to 1984 and on both sides of every
    statutory boundary, at both sexes: the day the model puts the qualifying
    age on is the statute's day for a woman born the same day, and status on 6
    October follows it."""
    sim, keys = differential_simulation()
    qualifying_age = sim.calculate("state_pension_credit_qualifying_age", year)
    attained = sim.calculate("has_attained_state_pension_credit_qualifying_age", year)
    mid_year = date(year, 10, 6)
    mismatches = []
    for i, (birth, male) in enumerate(keys):
        expected_day = reference_qualifying_day(birth)
        model_day = grid_months_to_date(grid_months(birth) + 12 * qualifying_age[i])
        if model_day != expected_day or attained[i] != (expected_day <= mid_year):
            mismatches.append((birth, male, expected_day, model_day, attained[i]))
    assert not mismatches, mismatches[:10]


@pytest.mark.parametrize("year", YEARS)
def test_class_4_liability_matches_statute_for_every_birth_date(year):
    """Class 4 liability by age is exactly "not over pensionable age on 6
    April", read from the statute for every birth date and both sexes."""
    sim, keys = differential_simulation()
    liable = sim.calculate("ni_class_4_liable", year)
    start_of_year = date(year, 4, 6)
    mismatches = [
        (birth, male, reference_attainment_day(birth, male), liable[i])
        for i, (birth, male) in enumerate(keys)
        if liable[i] == (reference_attainment_day(birth, male) <= start_of_year)
    ]
    assert not mismatches, mismatches[:10]


@pytest.mark.parametrize("year", YEARS)
def test_qualifying_age_and_pensionable_age_differ_only_for_men_born_before_6_december_1953(
    year,
):
    """The qualifying age never exceeds a person's pensionable age; the two are
    equal for women and for men born on or after 6 December 1953; so status at
    the qualifying age holds wherever is_SP_age does, and from 2019-20 the two
    agree for everyone."""
    sim, keys = differential_simulation()
    qualifying_age = sim.calculate("state_pension_credit_qualifying_age", year)
    spa = sim.calculate("state_pension_age", year)
    attained = sim.calculate("has_attained_state_pension_credit_qualifying_age", year)
    sp_age = sim.calculate("is_SP_age", year)
    male_rule = np.array(
        [male and birth < MALE_RULE_BORN_BEFORE for birth, male in keys]
    )
    assert np.all(qualifying_age <= spa + 1e-6)
    assert np.allclose(qualifying_age[~male_rule], spa[~male_rule], atol=1e-6)
    assert np.all(attained >= sp_age)
    if year > LAST_YEAR_THEY_DIFFER:
        assert np.array_equal(attained, sp_age)


def test_the_two_ages_do_differ_in_2015_to_2018():
    """The years before 2019-20 do contain men over the qualifying age and
    under their own pensionable age, so the checks above are not vacuous."""
    sim, keys = differential_simulation()
    for year in (2015, 2016, 2017, 2018):
        attained = sim.calculate(
            "has_attained_state_pension_credit_qualifying_age", year
        )
        sp_age = sim.calculate("is_SP_age", year)
        differ = attained & ~sp_age
        assert differ.any()
        assert all(
            male and birth < MALE_RULE_BORN_BEFORE
            for (birth, male), d in zip(keys, differ)
            if d
        )


@settings(max_examples=30, deadline=None)
@given(
    births=st.lists(
        st.dates(min_value=date(1945, 1, 1), max_value=date(1965, 12, 31)),
        min_size=1,
        max_size=40,
        unique=True,
    ),
    male=st.booleans(),
    year=st.integers(min_value=2015, max_value=2030),
)
def test_consumers_use_the_qualifying_age(births, male, year):
    """For single people with no income or capital, each programme that the
    statute ties to the qualifying age for State Pension Credit follows it,
    not the person's own pensionable age: Pension Credit is available exactly
    from it, Universal Credit exactly before it, and the pension-age Council
    Tax Reduction scheme and the benefit cap exception exactly from it. Winter
    Fuel Payment follows it until 2023-24, when it still needed no benefit."""
    people = {}
    for i, birth in enumerate(births):
        age_in_months = grid_months(date(year, 10, 6)) - grid_months(birth)
        age = int(age_in_months // 12)
        people[f"p{i}"] = {
            "age": {year: age},
            "months_since_last_birthday": {year: age_in_months - 12 * age},
            "is_male": {year: male},
        }
    sim = Simulation(situation=one_person_units(people))
    attained = sim.calculate("has_attained_state_pension_credit_qualifying_age", year)
    expected = np.array(
        [reference_qualifying_day(b) <= date(year, 10, 6) for b in births]
    )
    assert np.array_equal(attained, expected)
    assert np.array_equal(sim.calculate("is_pension_credit_eligible", year), attained)
    assert np.array_equal(sim.calculate("is_uc_eligible", year), ~attained)
    assert np.array_equal(
        sim.calculate("council_tax_reduction_household_has_pensioner", year), attained
    )
    assert np.array_equal(sim.calculate("is_benefit_cap_exempt_other", year), attained)
    if year <= 2023:
        assert np.array_equal(
            sim.calculate("winter_fuel_allowance", year) > 0, attained
        )


@settings(max_examples=40, deadline=None)
@given(
    births=st.lists(
        st.dates(min_value=date(1945, 1, 1), max_value=date(1975, 12, 31)),
        min_size=1,
        max_size=30,
        unique=True,
    ),
    male=st.booleans(),
    year=st.integers(min_value=2015, max_value=2045),
)
def test_class_4_liability_properties(births, male, year):
    """For any dates of birth: a person liable for Class 4 by age next year is
    liable this year (liability never resumes); liability holds exactly while
    State Pension age is reached after 6 April, so wherever the person is under
    State Pension age on 6 October; and profits are only charged when liable."""
    people = {}
    for i, birth in enumerate(births):
        ages, months = {}, {}
        for y in (year, year + 1):
            age_in_months = grid_months(date(y, 10, 6)) - grid_months(birth)
            ages[y] = int(age_in_months // 12)
            months[y] = age_in_months - 12 * ages[y]
        people[f"p{i}"] = {
            "age": ages,
            "months_since_last_birthday": months,
            "is_male": {y: male for y in (year, year + 1)},
            "self_employment_income": {y: 60_000 for y in (year, year + 1)},
        }
    sim = Simulation(situation=one_person_units(people))
    liable = sim.calculate("ni_class_4_liable", year)
    liable_next = sim.calculate("ni_class_4_liable", year + 1)
    since = sim.calculate("months_since_state_pension_age", year)
    sp_age = sim.calculate("is_SP_age", year)
    class_4 = sim.calculate("ni_class_4", year)
    assert np.all(liable_next <= liable)
    assert np.array_equal(liable, since < 6)
    assert np.all(liable[~sp_age])
    assert np.all((class_4 > 0) == liable)
