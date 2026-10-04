"""Date-of-birth cutoffs in Universal Credit, Child Tax Credit and Pension Credit.

UC Regs 2013 reg 24A(3), UC (Transitional Provisions) Regs 2014 reg 43, Tax
Credits Act 2002 s.9(3A) and SPC Regs 2002 Sch IIA para 10 all turn on whether a
child was born before 6 April 2017. The model compares date_of_birth with that
date. The reference here reads the date of birth with datetime, sharing no code
with policyengine_uk.utils.dates.
"""

from datetime import date, timedelta

import numpy as np
import pandas as pd
import pytest
from hypothesis import example, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation

CUTOFF = date(2017, 4, 6)


def ymd(day: date) -> int:
    return day.year * 10000 + day.month * 100 + day.day


def from_ymd(value: int) -> date:
    value = int(value)
    return date(value // 10000, value // 100 % 100, value % 100)


def grid_months(day: date) -> float:
    """Months on a grid whose months start on the 6th."""
    whole = 12 * day.year + day.month - 1 - (day.day < 6)
    start = date(whole // 12, whole % 12 + 1, 6)
    end = date((whole + 1) // 12, (whole + 1) % 12 + 1, 6)
    return whole + (day - start).days / (end - start).days


def birth_day_from_grid(months: float) -> date:
    """The calendar day starting at or after an instant on the grid, within
    about a minute and a half, as the model treats float error."""
    whole = int(np.floor(months))
    start = date(whole // 12, whole % 12 + 1, 6)
    end = date((whole + 1) // 12, (whole + 1) % 12 + 1, 6)
    offset = int(np.ceil((months - whole) * (end - start).days - 1e-3))
    return start + timedelta(days=offset)


def legal_age(birth: date, on: date) -> int:
    return on.year - birth.year - ((on.month, on.day) < (birth.month, birth.day))


def situation(people: dict) -> dict:
    return {
        "people": people,
        "benunits": {"benunit": {"members": list(people)}},
        "households": {"household": {"members": list(people)}},
    }


def test_household_situations_match_the_birth_year_rule():
    """A whole age in a household situation is the middle of the year of age,
    6 April of the year the person turned that age. So for households with
    whole ages the date rule gives what the old birth-year rule (period - age
    < 2017) gave, and birth_year is still period - age: only microdata, which
    spreads birthdays over the year, and fractional ages move."""
    for year in range(2015, 2036):
        ages = range(20)
        people = {f"p{age}": {"age": {year: age}} for age in ages}
        sim = Simulation(situation=situation(people))
        born = sim.calculate("date_of_birth", year)
        birth_year = sim.calculate("birth_year", year)
        exempt = sim.calculate("is_CTC_child_limit_exempt", year)
        uc = sim.calculate("uc_is_child_born_before_child_limit", year)
        old_rule = np.array([year - age < 2017 for age in ages])
        assert np.array_equal(born < ymd(CUTOFF), old_rule), year
        assert np.array_equal(exempt, old_rule), year
        under_16 = np.array(ages) < 16
        assert np.array_equal(uc[under_16], old_rule[under_16]), year
        assert np.array_equal(birth_year, [year - age for age in ages]), year


@settings(max_examples=30, deadline=None)
@given(
    cases=st.lists(
        st.tuples(
            st.integers(min_value=0, max_value=15),
            st.floats(min_value=0, max_value=12, exclude_max=True),
        ),
        min_size=1,
        max_size=12,
    ),
    year=st.integers(min_value=2015, max_value=2040),
)
def test_cutoffs_follow_the_date_of_birth(cases, year):
    """For any whole age and position in the year, including instants within a
    day: date_of_birth is the day the reference places, the person has that
    legal age on 6 October, birth_year is its year, and each cutoff holds
    exactly when the person was born before 6 April 2017."""
    people = {"parent": {"age": {year: 40}, "months_since_last_birthday": {year: 6}}}
    for i, (age, months) in enumerate(cases):
        people[f"c{i}"] = {
            "age": {year: age},
            "months_since_last_birthday": {year: months},
        }
    sim = Simulation(situation=situation(people))
    born = sim.calculate("date_of_birth", year)[1:]
    birth_year = sim.calculate("birth_year", year)[1:]
    uc = sim.calculate("uc_is_child_born_before_child_limit", year)[1:]
    ctc = sim.calculate("is_CTC_child_limit_exempt", year)[1:]
    mid_year = date(year, 10, 6)
    for i, (age, months) in enumerate(cases):
        # The model caps months since the last birthday about four minutes
        # short of 12, so the exact age never rounds onto the next birthday.
        months = min(months, 12 - 1e-4)
        expected = birth_day_from_grid(grid_months(mid_year) - 12 * age - months)
        assert from_ymd(born[i]) == expected, (year, age, months)
        assert legal_age(expected, mid_year) == age, (year, age, months)
        assert birth_year[i] == expected.year
        assert uc[i] == (expected < CUTOFF), (year, age, months)
        assert ctc[i] == (expected < CUTOFF), (year, age, months)


@settings(max_examples=25, deadline=None)
@given(
    children=st.lists(
        st.tuples(
            st.integers(min_value=0, max_value=15),
            st.floats(min_value=0, max_value=12, exclude_max=True),
        ),
        min_size=2,
        max_size=6,
    ),
    year=st.integers(min_value=2017, max_value=2030),
)
def test_children_are_ordered_by_date_of_birth(children, year):
    """Universal Credit numbers children eldest first by date of birth (reg
    24B), which refines the order by whole age: an older child always comes
    first, and children of the same age come in the order they were born."""
    people = {
        "parent": {
            "age": {year: 40},
            "months_since_last_birthday": {year: 6},
            "is_benunit_head": {year: True},
            "is_parent": {year: True},
        }
    }
    for i, (age, months) in enumerate(children):
        people[f"c{i}"] = {
            "age": {year: age},
            "months_since_last_birthday": {year: months},
            "is_benunit_head": {year: False},
        }
    sim = Simulation(situation=situation(people))
    index = sim.calculate("uc_child_index", year)[1:]
    born = sim.calculate("date_of_birth", year)[1:]
    ages = np.array([age for age, _ in children])
    assert sorted(index) == list(range(1, len(children) + 1))
    for a in range(len(children)):
        for b in range(len(children)):
            if born[a] < born[b]:
                assert index[a] < index[b]
            if ages[a] > ages[b]:
                assert index[a] < index[b]


def cohort_share_born_before_cutoff(year: int, age: int) -> float:
    """Share of people aged `age` on 6 October with birthdays spread evenly
    over the days of the year who were born before 6 April 2017."""
    mid_year = date(year, 10, 6)
    last = date(year - age, 10, 6)
    first = date(year - age - 1, 10, 7)
    days = [first + timedelta(days=d) for d in range((last - first).days + 1)]
    return np.mean([day < CUTOFF for day in days])


def cohort_share_born_before_calendar_year(year: int, age: int) -> float:
    last = date(year - age, 10, 6)
    first = date(year - age - 1, 10, 7)
    days = [first + timedelta(days=d) for d in range((last - first).days + 1)]
    return np.mean([day.year < year - age for day in days])


def microdata_simulation(weights: np.ndarray, years):
    """A simulation built from data: one child per household, aged 5 to 12 in
    turn, alternating sex."""
    from policyengine_uk import Microsimulation
    from policyengine_uk.data import UKMultiYearDataset, UKSingleYearDataset

    n = len(weights)
    ids = np.arange(n)
    ages = 5 + ids % 8

    def year(y):
        person = pd.DataFrame(
            {
                "person_id": ids * 10 + 3,
                "person_benunit_id": ids,
                "person_household_id": ids,
                "age": ages,
                "gender": np.where(ids % 16 < 8, "MALE", "FEMALE"),
            }
        )
        return UKSingleYearDataset(
            person=person,
            benunit=pd.DataFrame({"benunit_id": ids}),
            household=pd.DataFrame({"household_id": ids, "household_weight": weights}),
            fiscal_year=y,
        )

    dataset = UKMultiYearDataset(datasets=[year(y) for y in years])
    return Microsimulation(dataset=dataset), ages


def test_microdata_share_born_before_cutoff_matches_statute():
    """In data each single year of age and sex is spread evenly over the year
    by weight, so the weighted share of the cohort that straddles 6 April 2017
    born before it is the statutory share, about half, where the birth-year
    rule gave none. Every other cohort is wholly before or after."""
    weights = np.random.default_rng(3).lognormal(7, 0.5, 8 * 2 * 150)
    years = (2022, 2024, 2025, 2026, 2028)
    sim, ages = microdata_simulation(weights, years)
    for year in years:
        born = np.asarray(sim.calculate("date_of_birth", year))
        birth_year = np.asarray(sim.calculate("birth_year", year))
        uc = np.asarray(sim.calculate("uc_is_child_born_before_child_limit", year))
        ctc = np.asarray(sim.calculate("is_CTC_child_limit_exempt", year))
        assert np.array_equal(uc, born < ymd(CUTOFF))
        assert np.array_equal(ctc, born < ymd(CUTOFF))
        for age in range(5, 13):
            cell = ages == age
            # Within the largest weight in the cell, plus a day of births for
            # where the month grid and the calendar differ.
            tolerance = weights[cell].max() / weights[cell].sum() + 1 / 365
            share = np.average(born[cell] < ymd(CUTOFF), weights=weights[cell])
            expected = cohort_share_born_before_cutoff(year, age)
            assert abs(share - expected) <= tolerance, (year, age, share)
            earlier_year = np.average(
                birth_year[cell] < year - age, weights=weights[cell]
            )
            expected = cohort_share_born_before_calendar_year(year, age)
            assert abs(earlier_year - expected) <= tolerance, (year, age)


@st.composite
def births_and_year(draw):
    """A year from 2015 (when the State Pension Credit qualifying age still
    differs from State Pension age for men born before 6 December 1953) and
    people born before its 6 October, of either sex."""
    year = draw(st.integers(min_value=2015, max_value=2040))
    births = draw(
        st.lists(
            st.tuples(
                st.dates(min_value=date(1935, 1, 1), max_value=date(year - 1, 12, 31)),
                st.booleans(),
            ),
            min_size=1,
            max_size=8,
        )
    )
    return births, year


@settings(max_examples=25, deadline=None)
@given(case=births_and_year())
# Transitional cohorts in the year they reach the qualifying age, where a
# wrong birth instant changes has_attained_state_pension_credit_qualifying_age
# but a uniform draw rarely lands: a woman born 10 December 1952 (qualifying
# age 62 years and about 9 months, reached in 2015-16) and a man born 10
# November 1960 (66 years and 7 months, reached in 2027-28).
@example(case=([(date(1952, 12, 10), False)], 2015))
@example(case=([(date(1960, 11, 10), True)], 2027))
def test_a_date_of_birth_input_matches_the_same_birthday_by_age(case):
    """Setting date_of_birth (with the legal age on 6 October) gives the same
    State Pension age, State Pension Credit qualifying age, statuses, Savings
    Credit age test and cutoffs as placing the same day with
    months_since_last_birthday. A person left without the input in the same
    situation gets what they would with no input at all."""
    people, year = case
    births = [birth for birth, _ in people]
    mid_year = date(year, 10, 6)
    by_date = {"unset": {"age": {year: 40}}}
    by_months = {"unset": {"age": {year: 40}, "months_since_last_birthday": {year: 6}}}
    for i, (birth, male) in enumerate(people):
        age = legal_age(birth, mid_year)
        months = grid_months(mid_year) - grid_months(birth) - 12 * age
        by_date[f"p{i}"] = {
            "age": {year: age},
            "date_of_birth": {year: ymd(birth)},
            "is_male": {year: male},
        }
        by_months[f"p{i}"] = {
            "age": {year: age},
            "months_since_last_birthday": {year: months},
            "is_male": {year: male},
        }
    a = Simulation(situation=situation(by_date))
    b = Simulation(situation=situation(by_months))
    for variable in [
        "birth_year",
        "is_SP_age",
        "has_attained_state_pension_credit_qualifying_age",
        "meets_savings_credit_age_requirement",
        "uc_is_child_born_before_child_limit",
        "is_CTC_child_limit_exempt",
    ]:
        assert np.array_equal(
            a.calculate(variable, year), b.calculate(variable, year)
        ), variable
    for variable in [
        "state_pension_age",
        "state_pension_credit_qualifying_age",
        "months_since_state_pension_age",
    ]:
        assert np.allclose(
            a.calculate(variable, year), b.calculate(variable, year), rtol=0, atol=1e-9
        ), variable
    # A woman's qualifying age for State Pension Credit is her State Pension
    # age (SPCA 2002 s.1(6)(a)), so on the date path both statuses agree.
    women = ~a.calculate("is_male", year)
    assert np.array_equal(
        a.calculate("has_attained_state_pension_credit_qualifying_age", year)[women],
        a.calculate("is_SP_age", year)[women],
    )
    assert list(a.calculate("date_of_birth", year)[1:]) == [ymd(d) for d in births]
    assert a.calculate("date_of_birth", year)[0] == 0


@pytest.mark.parametrize(
    "date_of_birth, age",
    [
        (20170229, 8),  # 29 February 2017 does not exist
        (20170340, 8),  # nor does 40 March
        (2017, 8),  # a birth year, not a date
        (-20170405, 8),  # 0 means not given; a negative number is no date
    ],
)
def test_an_invalid_date_of_birth_is_rejected(date_of_birth, age):
    people = {"child": {"age": {2025: age}, "date_of_birth": {2025: date_of_birth}}}
    sim = Simulation(situation=situation(people))
    with pytest.raises(ValueError, match="calendar date"):
        sim.calculate("uc_is_child_born_before_child_limit", 2025)


def test_a_date_of_birth_that_contradicts_age_is_rejected():
    """A child given only a date of birth keeps the default age; the rules
    would read them as a 40-year-old born in 2017."""
    people = {"child": {"date_of_birth": {2025: 20170405}}}
    sim = Simulation(situation=situation(people))
    with pytest.raises(ValueError, match="aged 8 on 6 October 2025"):
        sim.calculate("is_SP_age", 2025)
