"""National Minimum Wage rates checked against the statutory instruments.

Both tables below are transcribed from the National Minimum Wage Regulations
2015 (S.I. 2015/621), the National Minimum Wage Regulations 1999 before them,
and each amending S.I. on legislation.gov.uk. They are written out by hand
rather than read from the parameter files, so the tests can catch a missing or
wrong entry there.

``RATES_FROM_COMMENCEMENT`` holds the rates each S.I. set, from the date it
came into force. ``RATES_AT_30_APRIL`` holds, for each year Y, the rates in
force on 30 April Y. That is the value PolicyEngine UK uses for year Y:
``convert_to_fiscal_year_parameters`` reads each parameter that has neither
``fiscal_year_blend`` nor ``preserve_calendar_dates`` metadata (these have
neither) at 30 April of each year from 2015 to 2040, and uses that value for
the whole year. A rate that changed on 1 October (until October 2016)
therefore first appears in the following year's row, and the October 2016
rates never appear.

Columns are the rate bands: apprentice, under 18, 18 to 20, 21 to 22, 23 to 24
and 25 or over. The national living wage applied from age 25 from 1 April 2016
(S.I. 2016/68), from 23 from 1 April 2021 (S.I. 2021/329 reg. 2(3)(b)) and from
21 from 1 April 2024 (S.I. 2024/432 reg. 2(3)(a)). The 2023 row is the case
the parameters used to get wrong: with no 1 April 2023 entry, 2023 read the
April 2022 rates, for example £9.50 instead of the £10.42 national living wage.

The model reads ``is_apprentice`` as "the apprenticeship rate applies"
(2015 Regs reg. 5: an apprentice under 19 or in the first 12 months). Ages
under 16 are not checked: the Act does not cover workers of compulsory school
age, and the model gives them the under-18 rate.

Properties:

1. For every year from 2015 to the year of the latest dated rate, the value
   for year Y equals the value in force on 30 April Y in the raw parameter
   file, read without the fiscal-year conversion.
2. For every year from 2015 to 2040, no rate falls as age rises, and the
   apprenticeship rate is never above the rate for any age from 16.
3. No rate falls from one year to the next, 2015 to 2040. This holds for
   every rate set from October 2011 to April 2026; it is a property of the
   enacted rates, not a rule in the Act, so a future cut would need this test
   changing.

Rates dated after the last row of ``RATES_FROM_COMMENCEMENT`` (for example
announced rates whose S.I. is not yet made) need a reference but are not
checked against the tables until a row is added for them.
"""

import datetime
from pathlib import Path

import numpy as np
import pytest
import yaml
from hypothesis import given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation
from policyengine_uk.system import system

PARAMETER_DIR = (
    Path(__file__).resolve().parent.parent
    / "parameters"
    / "gov"
    / "hmrc"
    / "minimum_wage"
)

BANDS = (
    "apprentice",
    "under_18",
    "18_to_20",
    "21_to_22",
    "23_to_24",
    "25_or_over",
)

# Ages that fall in each non-apprentice band.
BAND_AGES = {
    "under_18": (16, 17),
    "18_to_20": (18, 19, 20),
    "21_to_22": (21, 22),
    "23_to_24": (23, 24),
    "25_or_over": (25, 30, 64, 80),
}

# (commencement date, S.I. and provisions, rates by band). Where an S.I. left a
# rate unchanged the row repeats the rate then in force.
RATES_FROM_COMMENCEMENT = [
    # 1999 Regs reg. 11 (21 and over) and reg. 13(3) (apprentices); the
    # 18 to 20 and under 18 rates (reg. 13(1), (2)) stayed at the levels set
    # by S.I. 2011/2345 reg. 5 from 1 October 2011.
    (
        "2012-10-01",
        "S.I. 2012/2397 reg. 2(2), 2(4)(a)",
        (2.65, 3.68, 4.98, 6.19, 6.19, 6.19),
    ),
    (
        "2013-10-01",
        "S.I. 2013/1975 reg. 2(2), 2(3)",
        (2.68, 3.72, 5.03, 6.31, 6.31, 6.31),
    ),
    ("2014-10-01", "S.I. 2014/2485 reg. 3", (2.73, 3.79, 5.13, 6.50, 6.50, 6.50)),
    # 2015 Regs reg. 4(1)(a) to (d).
    ("2015-10-01", "S.I. 2015/1724 reg. 2(2)", (3.30, 3.87, 5.30, 6.70, 6.70, 6.70)),
    # Substitutes reg. 4 (national living wage, 25 and over) and reg. 4A
    # (21 to 24, 18 to 20, under 18, apprentices).
    ("2016-04-01", "S.I. 2016/68 reg. 3", (3.30, 3.87, 5.30, 6.70, 6.70, 7.20)),
    ("2016-10-01", "S.I. 2016/953 reg. 2(2)", (3.40, 4.00, 5.55, 6.95, 6.95, 7.20)),
    (
        "2017-04-01",
        "S.I. 2017/465 reg. 2(2), 2(3)",
        (3.50, 4.05, 5.60, 7.05, 7.05, 7.50),
    ),
    (
        "2018-04-01",
        "S.I. 2018/455 reg. 2(2), 2(3)",
        (3.70, 4.20, 5.90, 7.38, 7.38, 7.83),
    ),
    (
        "2019-04-01",
        "S.I. 2019/603 reg. 2(2), 2(3)",
        (3.90, 4.35, 6.15, 7.70, 7.70, 8.21),
    ),
    (
        "2020-04-01",
        "S.I. 2020/338 reg. 2(2), 2(3)",
        (4.15, 4.55, 6.45, 8.20, 8.20, 8.72),
    ),
    # Reg. 2(3)(b): the reg. 4A(1)(a) band becomes 21 to 22.
    (
        "2021-04-01",
        "S.I. 2021/329 reg. 2(2), 2(3)",
        (4.30, 4.62, 6.56, 8.36, 8.91, 8.91),
    ),
    (
        "2022-04-01",
        "S.I. 2022/382 reg. 2(2), 2(3)",
        (4.81, 4.81, 6.83, 9.18, 9.50, 9.50),
    ),
    (
        "2023-04-01",
        "S.I. 2023/354 reg. 2(2), 2(3)",
        (5.28, 5.28, 7.49, 10.18, 10.42, 10.42),
    ),
    # Reg. 2(3)(a) omits reg. 4A(1)(a): 21 and over get the national living wage.
    (
        "2024-04-01",
        "S.I. 2024/432 reg. 2(2), 2(3)",
        (6.40, 6.40, 8.60, 11.44, 11.44, 11.44),
    ),
    (
        "2025-04-01",
        "S.I. 2025/401 reg. 2(2), 2(3)",
        (7.55, 7.55, 10.00, 12.21, 12.21, 12.21),
    ),
    (
        "2026-04-01",
        "S.I. 2026/357 reg. 2(2), 2(3)",
        (8.00, 8.00, 10.85, 12.71, 12.71, 12.71),
    ),
]

# Rates in force on 30 April of each year, and the S.I. that set them.
RATES_AT_30_APRIL = {
    # 2015 Regs reg. 4(1) as made (in force 6 April 2015), carrying over the
    # 1 October 2014 rates.
    2015: (2.73, 3.79, 5.13, 6.50, 6.50, 6.50),  # S.I. 2015/621, S.I. 2014/2485
    2016: (3.30, 3.87, 5.30, 6.70, 6.70, 7.20),  # S.I. 2016/68
    2017: (3.50, 4.05, 5.60, 7.05, 7.05, 7.50),  # S.I. 2017/465
    2018: (3.70, 4.20, 5.90, 7.38, 7.38, 7.83),  # S.I. 2018/455
    2019: (3.90, 4.35, 6.15, 7.70, 7.70, 8.21),  # S.I. 2019/603
    2020: (4.15, 4.55, 6.45, 8.20, 8.20, 8.72),  # S.I. 2020/338
    2021: (4.30, 4.62, 6.56, 8.36, 8.91, 8.91),  # S.I. 2021/329
    2022: (4.81, 4.81, 6.83, 9.18, 9.50, 9.50),  # S.I. 2022/382
    2023: (5.28, 5.28, 7.49, 10.18, 10.42, 10.42),  # S.I. 2023/354
    2024: (6.40, 6.40, 8.60, 11.44, 11.44, 11.44),  # S.I. 2024/432
    2025: (7.55, 7.55, 10.00, 12.21, 12.21, 12.21),  # S.I. 2025/401
    2026: (8.00, 8.00, 10.85, 12.71, 12.71, 12.71),  # S.I. 2026/357
}

PROPERTY_YEARS = range(2015, 2041)
LAST_TRANSCRIBED = datetime.date.fromisoformat(RATES_FROM_COMMENCEMENT[-1][0])


def _rates(row):
    return dict(zip(BANDS, row))


def _model_rate(year, age):
    scale = system.parameters(str(year)).gov.hmrc.minimum_wage.non_apprentice
    return float(scale.calc(np.array([age]))[0])


def _model_apprentice_rate(year):
    return float(system.parameters(str(year)).gov.hmrc.minimum_wage.apprentice)


def _load_raw(name):
    return yaml.safe_load((PARAMETER_DIR / f"{name}.yaml").read_text())


def _dated_values(values):
    """Sorted (date, value) pairs from a raw parameter value mapping."""
    pairs = []
    for instant, entry in values.items():
        date = datetime.date.fromisoformat(str(instant))
        value = entry["value"] if isinstance(entry, dict) else entry
        pairs.append((date, float(value)))
    return sorted(pairs)


def _in_force(pairs, date):
    applicable = [value for start, value in pairs if start <= date]
    assert applicable, f"no value in force on {date}"
    return applicable[-1]


RAW_APPRENTICE = _dated_values(_load_raw("apprentice")["values"])
RAW_BRACKETS = [
    (_dated_values(bracket["threshold"]), _dated_values(bracket["amount"]))
    for bracket in _load_raw("non_apprentice")["brackets"]
]
LATEST_DATED_YEAR = max(
    start.year
    for pairs in [
        RAW_APPRENTICE,
        *(series for bracket in RAW_BRACKETS for series in bracket),
    ]
    for start, _ in pairs
)


def _raw_rate(date, age):
    """The non-apprentice rate on a date, read straight from the YAML."""
    rate = None
    for thresholds, amounts in RAW_BRACKETS:
        if _in_force(thresholds, date) <= age:
            rate = _in_force(amounts, date)
    return rate


@pytest.mark.parametrize("year", sorted(RATES_AT_30_APRIL))
def test_fiscal_year_rates_match_statutory_instruments(year):
    expected = _rates(RATES_AT_30_APRIL[year])
    assert _model_apprentice_rate(year) == pytest.approx(expected["apprentice"])
    for band, ages in BAND_AGES.items():
        for age in ages:
            assert _model_rate(year, age) == pytest.approx(expected[band]), (
                f"{year}, age {age} ({band})"
            )


def test_minimum_wage_variable_matches_statutory_instruments():
    years = sorted(RATES_AT_30_APRIL)
    people = {
        f"{band}_{age}": {"age": {str(year): age for year in years}}
        for band, ages in BAND_AGES.items()
        for age in ages
    }
    # The apprenticeship rate displaces the age rates (2015 Regs reg. 4A(2)).
    # is_apprentice stands for "the apprenticeship rate applies" (reg. 5).
    people["apprentice_19"] = {
        "age": {str(year): 19 for year in years},
        "is_apprentice": {str(year): True for year in years},
    }
    names = list(people)
    sim = Simulation(
        situation={
            "people": people,
            "benunits": {f"b_{name}": {"members": [name]} for name in names},
            "households": {f"h_{name}": {"members": [name]} for name in names},
        }
    )
    for year in years:
        expected = _rates(RATES_AT_30_APRIL[year])
        actual = sim.calculate("minimum_wage", year)
        for name, value in zip(names, actual):
            band = (
                "apprentice"
                if name.startswith("apprentice")
                else name.rsplit("_", 1)[0]
            )
            assert float(value) == pytest.approx(expected[band]), f"{year}, {name}"


@pytest.mark.parametrize(
    "commencement, instrument, row",
    RATES_FROM_COMMENCEMENT,
    ids=[instrument for _, instrument, _ in RATES_FROM_COMMENCEMENT],
)
def test_parameter_files_match_each_instrument_from_commencement(
    commencement, instrument, row
):
    date = datetime.date.fromisoformat(commencement)
    expected = _rates(row)
    assert _in_force(RAW_APPRENTICE, date) == pytest.approx(expected["apprentice"])
    for band, ages in BAND_AGES.items():
        for age in ages:
            assert _raw_rate(date, age) == pytest.approx(expected[band]), (
                f"{instrument}, age {age} ({band})"
            )


def test_parameter_files_change_only_on_commencement_dates():
    commencements = {
        datetime.date.fromisoformat(date) for date, _, _ in RATES_FROM_COMMENCEMENT
    }
    series = [RAW_APPRENTICE]
    for thresholds, amounts in RAW_BRACKETS:
        series += [thresholds, amounts]
    for pairs in series:
        for start, _ in pairs:
            if start <= LAST_TRANSCRIBED:
                assert start in commencements, f"{start} is not a commencement date"


def test_30_april_table_agrees_with_commencement_table():
    for year, row in RATES_AT_30_APRIL.items():
        in_force = [
            rates
            for date, _, rates in RATES_FROM_COMMENCEMENT
            if datetime.date.fromisoformat(date) <= datetime.date(year, 4, 30)
        ][-1]
        assert row == in_force, year


@pytest.mark.parametrize("year", range(2015, LATEST_DATED_YEAR + 1))
def test_fiscal_year_value_is_the_value_in_force_on_30_april(year):
    date = datetime.date(year, 4, 30)
    assert _model_apprentice_rate(year) == pytest.approx(
        _in_force(RAW_APPRENTICE, date)
    )
    for age in range(16, 101):
        assert _model_rate(year, age) == pytest.approx(_raw_rate(date, age)), age


def test_every_rate_cites_a_statutory_instrument():
    entries = list(_load_raw("apprentice")["values"].items())
    for bracket in _load_raw("non_apprentice")["brackets"]:
        entries += list(bracket["amount"].items())
    for instant, entry in entries:
        assert isinstance(entry, dict), f"{instant} has no reference"
        hrefs = [reference["href"] for reference in entry.get("reference", [])]
        assert hrefs, f"{instant} has no reference"
        if datetime.date.fromisoformat(str(instant)) <= LAST_TRANSCRIBED:
            assert any(
                href.startswith("https://www.legislation.gov.uk/uksi/")
                for href in hrefs
            ), f"{instant} does not cite an S.I."


PROPERTY_SETTINGS = settings(max_examples=300, deadline=None, derandomize=True)


@PROPERTY_SETTINGS
@given(
    year=st.sampled_from(PROPERTY_YEARS),
    younger=st.integers(16, 120),
    older=st.integers(16, 120),
)
def test_rates_do_not_fall_with_age(year, younger, older):
    younger, older = sorted((younger, older))
    assert _model_rate(year, younger) <= _model_rate(year, older)
    assert _model_apprentice_rate(year) <= _model_rate(year, younger)


@PROPERTY_SETTINGS
@given(year=st.sampled_from(PROPERTY_YEARS[:-1]), age=st.integers(16, 120))
def test_rates_do_not_fall_from_year_to_year(year, age):
    assert _model_rate(year, age) <= _model_rate(year + 1, age)
    assert _model_apprentice_rate(year) <= _model_apprentice_rate(year + 1)
