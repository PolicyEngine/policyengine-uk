"""State Pension age by date of birth (Pensions Act 1995 Schedule 4 para 1).

The parameters are checked row by row against the statute's text, and the
model is checked against a day-level reading of the same text that shares no
code with the model.
"""

import calendar
import re
from datetime import date, timedelta
from functools import lru_cache
from pathlib import Path

import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation
from policyengine_uk.system import system
from policyengine_uk.utils.stochastic import splitmix64_uniform, stratified_uniform

STATUTE = (
    Path(__file__).parent / "fixtures" / "pensions_act_1995_schedule_4_paragraph_1.txt"
).read_text()
MONTHS = {name: number for number, name in enumerate(calendar.month_name) if name}
DATE = r"\d+(?:st|nd|rd|th) \w+ \d{4}"
NEW_STATE_PENSION_START = date(2016, 4, 6)  # Pensions Act 2014 s.1(2)
SAVINGS_CREDIT_CUTOFF = date(2016, 4, 6)  # State Pension Credit Act 2002 s.3(1)(a)


def parse_date(text: str) -> date:
    day, month, year = re.fullmatch(r"(\d+)\w\w (\w+) (\d{4})", text.strip()).groups()
    return date(int(year), MONTHS[month], int(day))


def ymd(day: date) -> int:
    return day.year * 10000 + day.month * 100 + day.day


def table(number: int) -> list:
    body = STATUTE.split(f"TABLE {number}\n")[1].split("\n(")[0]
    rows = re.findall(rf"\| ({DATE}) to ({DATE}) \| ([^|]+?) \|", body)
    return [(parse_date(start), parse_date(end), target) for start, end, target in rows]


def rule(number: str, pattern: str) -> tuple:
    line = re.search(rf"^\({number}\) (.+)$", STATUTE, flags=re.M).group(1)
    return re.fullmatch(pattern, line).groups()


TABLE_1 = [(s, e, parse_date(t)) for s, e, t in table(1)]
TABLE_2 = [(s, e, parse_date(t)) for s, e, t in table(2)]
TABLE_3 = [
    (s, e, 12 * int(y) + int(m))
    for s, e, t in table(3)
    for y, m in [re.fullmatch(r"(\d+) years and (\d+) months?", t).groups()]
]
TABLE_4 = [(s, e, parse_date(t)) for s, e, t in table(4)]
MEN_BEFORE, MEN_AGE = rule(
    "1",
    rf"A man born before ({DATE}) attains pensionable age when he attains the age of (\d+) years\.",
)
WOMEN_BEFORE, WOMEN_AGE = rule(
    "2",
    rf"A woman born before ({DATE}) attains pensionable age when she attains the age of (\d+)\.",
)
AGE_RULES = {
    number: rule(
        number,
        rf"A person born after ({DATE})(?: but before ({DATE}))? attains pensionable age "
        r"when the person attains the age of (\d+)\.",
    )
    for number in ("6", "8", "10")
}
SPECIAL_DAYS = {
    parse_date(born): parse_date(attained)
    for born, attained in re.findall(
        rf"a person born on ({DATE}) is to be taken to attain the age of 66 years and "
        rf"\d+ months at the commencement of ({DATE})",
        STATUTE,
    )
}


def after(text: str) -> date:
    return parse_date(text) + timedelta(days=1)


def add_months(day: date, months: int) -> date:
    year, month = divmod(day.month - 1 + months, 12)
    year += day.year
    return date(year, month + 1, min(day.day, calendar.monthrange(year, month + 1)[1]))


def reference_attainment_day(birth: date, male: bool) -> date:
    """The day a person attains pensionable age, read from the statute text."""
    if male and birth < parse_date(MEN_BEFORE):
        return add_months(birth, 12 * int(MEN_AGE))
    if not male and birth < parse_date(WOMEN_BEFORE):
        return add_months(birth, 12 * int(WOMEN_AGE))
    for start, end, day in (TABLE_2 if male else TABLE_1 + TABLE_2) + TABLE_4:
        if start <= birth <= end:
            return day
    for start, end, months in TABLE_3:
        if start <= birth <= end:
            return SPECIAL_DAYS.get(birth, add_months(birth, months))
    for number in ("6", "8", "10"):
        born_after, born_before, age = AGE_RULES[number]
        if birth > parse_date(born_after) and (
            born_before is None or birth < parse_date(born_before)
        ):
            return add_months(birth, 12 * int(age))
    raise ValueError(f"No rule covers {birth}")


def grid_months(day: date) -> float:
    """Months on a grid whose months start on the 6th, written independently of
    policyengine_uk.utils.dates."""
    whole = 12 * day.year + day.month - 1 - (day.day < 6)
    start = date(whole // 12, whole % 12 + 1, 6)
    end = date((whole + 1) // 12, (whole + 1) % 12 + 1, 6)
    return whole + (day - start).days / (end - start).days


def grid_months_to_date(months: float) -> date:
    whole = int(np.floor(months))
    start = date(whole // 12, whole % 12 + 1, 6)
    end = date((whole + 1) // 12, (whole + 1) % 12 + 1, 6)
    return start + timedelta(days=int(round((months - whole) * (end - start).days)))


def situation(people: dict) -> dict:
    return {
        "people": people,
        "benunits": {"benunit": {"members": list(people)}},
        "households": {"household": {"members": list(people)}},
    }


class TestParametersMatchStatute:
    """Every parameter row must come from the statute's text."""

    def setup_method(self):
        self.p = system.parameters.gov.dwp.state_pension.age

    def brackets(self, scale) -> list:
        at = scale("2026-01-01")
        return list(zip(map(int, at.thresholds), map(int, at.amounts)))

    def test_statute_tables_are_complete_and_contiguous(self):
        assert [len(TABLE_1), len(TABLE_2), len(TABLE_3), len(TABLE_4)] == [
            44,
            10,
            11,
            12,
        ]
        periods = [(s, e) for s, e, _ in TABLE_1 + TABLE_2]
        periods += [
            (after(AGE_RULES["6"][0]), parse_date(AGE_RULES["6"][1]) - timedelta(1))
        ]
        periods += [(s, e) for s, e, _ in TABLE_3]
        periods += [
            (after(AGE_RULES["8"][0]), parse_date(AGE_RULES["8"][1]) - timedelta(1))
        ]
        periods += [(s, e) for s, e, _ in TABLE_4]
        assert periods[0][0] == parse_date(WOMEN_BEFORE)
        for (_, end), (start, _) in zip(periods, periods[1:]):
            assert start == end + timedelta(days=1)
        assert after(AGE_RULES["10"][0]) == periods[-1][1] + timedelta(days=1)
        assert parse_date(MEN_BEFORE) == TABLE_2[0][0]
        assert len(SPECIAL_DAYS) == 3

    def test_age_by_birth_date_matches_statute(self):
        expected = [(0, 12 * int(WOMEN_AGE)), (ymd(TABLE_1[0][0]), 0)]
        expected += [(ymd(after(AGE_RULES["6"][0])), 12 * int(AGE_RULES["6"][2]))]
        expected += [(ymd(start), months) for start, _, months in TABLE_3]
        expected += [(ymd(after(AGE_RULES["8"][0])), 12 * int(AGE_RULES["8"][2]))]
        expected += [(ymd(TABLE_4[0][0]), 0)]
        expected += [(ymd(after(AGE_RULES["10"][0])), 12 * int(AGE_RULES["10"][2]))]
        assert self.brackets(self.p.age_by_birth_date) == expected

    def test_day_by_birth_date_matches_statute(self):
        expected = [(0, 0)]
        expected += [(ymd(start), ymd(day)) for start, _, day in TABLE_1 + TABLE_2]
        expected += [(ymd(after(AGE_RULES["6"][0])), 0)]
        expected += [(ymd(start), ymd(day)) for start, _, day in TABLE_4]
        expected += [(ymd(after(AGE_RULES["10"][0])), 0)]
        assert self.brackets(self.p.day_by_birth_date) == expected

    def test_male_rule_matches_statute(self):
        year, month, day = self.p.male.born_before("2026-01-01")
        assert date(year, month, day) == parse_date(MEN_BEFORE)
        assert self.p.male.age("2026-01-01") == 12 * int(MEN_AGE)


BIRTHS = [date(1945, 1, 1) + timedelta(days=d) for d in range(0, 40 * 366, 3)]
BOUNDARIES = sorted(
    {
        edge + timedelta(days=shift)
        for start, end, _ in TABLE_1 + TABLE_2 + TABLE_3 + TABLE_4
        for edge in (start, end)
        for shift in (-1, 0, 1)
    }
    | set(SPECIAL_DAYS)
)
YEARS = [2015, 2016, 2017, 2018, 2019, 2020, 2025, 2026, 2027, 2028, 2044, 2045, 2046]


@lru_cache(maxsize=None)
def differential_simulation() -> tuple:
    people, keys = {}, []
    births = sorted(set(BIRTHS) | set(BOUNDARIES))
    for male in (True, False):
        for birth in births:
            name = f"{'m' if male else 'f'}{birth:%Y%m%d}"
            ages, months = {}, {}
            for year in YEARS:
                age_in_months = grid_months(date(year, 10, 6)) - grid_months(birth)
                ages[year] = int(age_in_months // 12)
                months[year] = age_in_months - 12 * ages[year]
            people[name] = {
                "age": ages,
                "months_since_last_birthday": months,
                "is_male": {year: male for year in YEARS},
            }
            keys.append((birth, male))
    return Simulation(situation=situation(people)), keys


@pytest.mark.parametrize("year", YEARS)
def test_status_matches_statute_for_every_birth_date(year):
    """State Pension age status, type and the Savings Credit age test agree with
    a day-level reading of the statute, for births every third day from 1945 to
    1984 and on both sides of every statutory boundary, at both sexes."""
    sim, keys = differential_simulation()
    status = sim.calculate("is_SP_age", year)
    pension_type = sim.calculate("state_pension_type", year)
    savings = sim.calculate("meets_savings_credit_age_requirement", year)
    spa = sim.calculate("state_pension_age", year)
    mid_year = date(year, 10, 6)
    mismatches = []
    for i, (birth, male) in enumerate(keys):
        attained = reference_attainment_day(birth, male)
        expected_type = (
            "NONE"
            if attained > mid_year
            else "BASIC"
            if attained < NEW_STATE_PENSION_START
            else "NEW"
        )
        age_in_months = grid_months(mid_year) - grid_months(birth)
        expected_savings = attained < SAVINGS_CREDIT_CUTOFF and age_in_months >= 12 * 65
        model_day = grid_months_to_date(grid_months(birth) + 12 * spa[i])
        if (
            status[i] != (attained <= mid_year)
            or pension_type[i] != expected_type
            or savings[i] != expected_savings
            # The grid spreads each month's days evenly, so an anniversary a
            # whole number of months on can land a day off when the months
            # differ in length. Status is only read on the 6th, where the grid
            # is exact.
            or abs((model_day - attained).days) > 1
        ):
            mismatches.append((birth, male, attained, status[i], spa[i]))
    assert not mismatches, mismatches[:10]


def mid_year_share(year: int, age: int, male: bool) -> float:
    """Share of people aged `age` on 6 October who have attained pensionable
    age by then, with birthdays spread evenly over the year."""
    mid_year = date(year, 10, 6)
    first = add_months(mid_year, -12 * (age + 1)) + timedelta(days=1)
    days = [
        first + timedelta(days=d)
        for d in range((add_months(mid_year, -12 * age) - first).days + 1)
    ]
    return np.mean([reference_attainment_day(b, male) <= mid_year for b in days])


def test_microdata_share_at_state_pension_age_matches_statute():
    """In representative data, each single year of age and sex is spread evenly
    over the year by weight, so the weighted share of 66-year-olds over State
    Pension age is the statutory share: three quarters in 2026-27 and a quarter
    in 2027-28, as births from 6 April 1960 reach it at 66 and 1 to 11 months."""
    rng = np.random.default_rng(0)
    n = 4_000
    weights = rng.lognormal(7, 1, n)
    people = {}
    for i in range(n):
        people[f"p{i}"] = {
            "age": {y: 60 + i % 11 for y in range(2015, 2031)},
            "is_male": {y: bool(i % 2) for y in range(2015, 2031)},
        }
    households = {
        f"h{i}": {
            "members": [f"p{i}"],
            "household_weight": {y: float(weights[i]) for y in range(2015, 2031)},
        }
        for i in range(n)
    }
    benunits = {f"b{i}": {"members": [f"p{i}"]} for i in range(n)}
    sim = Simulation(
        situation={"people": people, "benunits": benunits, "households": households}
    )
    age = np.array([60 + i % 11 for i in range(n)])
    male = np.array([bool(i % 2) for i in range(n)])
    for year in (2015, 2016, 2017, 2018, 2019, 2020, 2026, 2027, 2028):
        status = sim.calculate("is_SP_age", year)
        for a in range(60, 71):
            for sex in (True, False):
                cell = (age == a) & (male == sex)
                share = np.average(status[cell], weights=weights[cell])
                # Within the largest weight in the cell plus one day of births.
                tolerance = weights[cell].max() / weights[cell].sum() + 1 / 365
                assert abs(share - mid_year_share(year, a, sex)) <= tolerance, (
                    year,
                    a,
                    sex,
                    share,
                )


def test_single_household_uses_the_middle_of_the_year_of_age():
    sim = Simulation(situation=situation({"person": {"age": {2027: 66}}}))
    assert sim.calculate("months_since_last_birthday", 2027)[0] == 6
    assert not sim.calculate("is_SP_age", 2027)[0]


@settings(max_examples=40, deadline=None)
@given(
    births=st.lists(
        st.dates(min_value=date(1935, 1, 1), max_value=date(1995, 12, 31)),
        min_size=2,
        max_size=40,
        unique=True,
    ),
    male=st.booleans(),
    year=st.integers(min_value=2015, max_value=2050),
)
def test_state_pension_age_properties(births, male, year):
    """For any dates of birth: State Pension age lies between 60 and 68; the
    day it is attained never falls earlier for someone born later; and status
    agrees with months_since_state_pension_age."""
    births = sorted(births)
    people = {}
    for i, birth in enumerate(births):
        age_in_months = grid_months(date(year, 10, 6)) - grid_months(birth)
        age = int(age_in_months // 12)
        people[f"p{i}"] = {
            "age": {year: age},
            "months_since_last_birthday": {year: age_in_months - 12 * age},
            "is_male": {year: male},
        }
    sim = Simulation(situation=situation(people))
    spa = sim.calculate("state_pension_age", year)
    since = sim.calculate("months_since_state_pension_age", year)
    status = sim.calculate("is_SP_age", year)
    assert np.all((spa >= 60 - 1e-6) & (spa <= 68 + 1e-6))
    attained = np.array([grid_months(b) for b in births]) + 12 * spa
    assert np.all(np.diff(attained) >= -1e-3)
    assert np.array_equal(status, since >= 0)


@settings(max_examples=100, deadline=None)
@given(
    n=st.integers(min_value=1, max_value=300),
    strata_count=st.integers(min_value=1, max_value=5),
    seed=st.integers(min_value=0, max_value=2**32 - 1),
)
def test_stratified_uniform_properties(n, strata_count, seed):
    """Positions lie in [0, 1), ignore record order, and within each stratum the
    weighted share below any point is that point to within the largest weight."""
    rng = np.random.default_rng(seed)
    strata = rng.integers(0, strata_count, n)
    ids = rng.permutation(10 * n)[:n]
    weights = rng.lognormal(0, 1.5, n)
    draws = splitmix64_uniform(ids, salt=2)
    positions = stratified_uniform(strata, draws, weights)
    assert np.all((positions >= 0) & (positions < 1))
    order = rng.permutation(n)
    shuffled = stratified_uniform(strata[order], draws[order], weights[order])
    assert np.allclose(shuffled, positions[order])
    for s in np.unique(strata):
        cell = strata == s
        w = weights[cell] / weights[cell].sum()
        for x in np.linspace(0, 1, 21):
            below = w[positions[cell] < x].sum()
            assert abs(below - x) <= w.max() / 2 + 1e-9
