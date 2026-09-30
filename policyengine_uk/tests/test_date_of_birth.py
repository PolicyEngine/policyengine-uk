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
from hypothesis import given, settings
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
    6 April of the year the person turned that age. So for households the
    date rule gives what the old birth-year rule (period - age < 2017) gave,
    and birth_year is still period - age: only microdata, which spreads
    birthdays over the year, moves."""
    for year in range(2015, 2036):
        ages = range(20)
        people = {f"p{age}": {"age": {year: age}} for age in ages}
        sim = Simulation(situation=situation(people))
        born = sim.calculate("date_of_birth", year)
        birth_year = sim.calculate("birth_year", year)
        exempt = sim.calculate("is_CTC_child_limit_exempt", year)
        old_rule = np.array([year - age < 2017 for age in ages])
        assert np.array_equal(born < ymd(CUTOFF), old_rule), year
        assert np.array_equal(exempt, old_rule), year
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
