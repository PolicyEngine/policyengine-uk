"""Class 1 rates under the Health and Social Care Levy in 2022-23.

The Health and Social Care Levy Act 2021 s.5(2) raised two Class 1
percentages for the tax year 2022-23 by 1.25 points: the main primary
percentage from 12% to 13.25% (s.5(2)(a)(i)) and the secondary percentage
from 13.8% to 15.05% (s.5(2)(b)). The Health and Social Care Levy (Repeal) Act
2022 s.2(1) kept both only for payments of earnings made before 6 November
2022. Para 5(3) of its Schedule gives the annual rates for directors' annual
earnings periods: 12.73% main primary and 14.53% secondary.

The rate parameters store these as dated values. The model reads each tax
year at 30 April (convert_to_fiscal_year_parameters), so model year 2022
takes the levy rate on both sides. Whether to average across the year instead
is open in #1807.

Invariants, checked on the parameter files as stored:

1. Statutory window: for any date d, the employer rate is 15.05% if and only
   if 6 April 2022 <= d < 6 November 2022, and the employee main rate is
   13.25% on exactly the same dates.
2. Same dates: in the 2022-23 tax year the two rates change on the same
   dates, 6 April and 6 November 2022.
3. Same uplift: inside the window each rate is 1.25 points above its value on
   5 April 2022.
4. Annual equivalent: the day-weighted average of each rate over 2022-23,
   computed exactly, rounds to the Repeal Act's directors' rate.
   fiscal_year_average gives the same figure (differential).

And on the model:

5. Same convention: neither rate is blended, so in every model year from 2015
   to 2030 each annual rate is the stored rate at 30 April. Model year 2022 is
   15.05% and 13.25%; 2021 and 2023 are 13.8% and 12%.
"""

import datetime
from fractions import Fraction
from pathlib import Path

import pytest
from hypothesis import example, given, settings
from hypothesis import strategies as st
from policyengine_core.parameters import load_parameter_file

import policyengine_uk
from policyengine_uk import CountryTaxBenefitSystem
from policyengine_uk.utils.parameters import fiscal_year_average

RATES = (
    Path(policyengine_uk.__file__).parent
    / "parameters"
    / "gov"
    / "hmrc"
    / "national_insurance"
    / "class_1"
    / "rates"
)
EMPLOYER_FILE = RATES / "employer.yaml"
EMPLOYEE_MAIN_FILE = RATES / "employee" / "main.yaml"

LEVY_START = datetime.date(2022, 4, 6)  # HSCL Act 2021 s.5(1): tax year 2022-23
LEVY_END = datetime.date(2022, 11, 6)  # Repeal Act 2022 s.2(1)
TAX_YEAR_END = datetime.date(2023, 4, 6)

EMPLOYER_LEVY_RATE = Fraction("0.1505")  # s.5(2)(b)
EMPLOYEE_LEVY_RATE = Fraction("0.1325")  # s.5(2)(a)(i)
UPLIFT = Fraction("0.0125")
# Repeal Act 2022 Sch para 5(3), as percentages.
EMPLOYER_DIRECTORS_RATE = Fraction("14.53")
EMPLOYEE_DIRECTORS_RATE = Fraction("12.73")


@pytest.fixture(scope="module")
def employer():
    return load_parameter_file(str(EMPLOYER_FILE), "employer")


@pytest.fixture(scope="module")
def employee_main():
    return load_parameter_file(str(EMPLOYEE_MAIN_FILE), "main")


@pytest.fixture(scope="module")
def system():
    return CountryTaxBenefitSystem()


def rate_on(param, date):
    """The stored rate in force on a date, as an exact fraction."""
    return Fraction(str(param(date.isoformat())))


def change_dates(param, start, end):
    """Dates in [start, end) on which the stored rate takes a new value."""
    dates = []
    for value_at_instant in param.values_list:
        date = datetime.date.fromisoformat(value_at_instant.instant_str)
        if not start <= date < end:
            continue
        if rate_on(param, date) != rate_on(param, date - datetime.timedelta(days=1)):
            dates.append(date)
    return sorted(dates)


def exact_annual_percentage(param, start, end):
    """Day-weighted average of the stored rate over [start, end), in percent."""
    total = Fraction(0)
    day = start
    while day < end:
        total += rate_on(param, day)
        day += datetime.timedelta(days=1)
    return 100 * total / (end - start).days


# Invariant 1: statutory window.
@settings(max_examples=200, deadline=None, derandomize=True)
@given(
    date=st.dates(
        min_value=datetime.date(2015, 4, 6),
        max_value=datetime.date(2031, 4, 5),
    )
)
@example(date=datetime.date(2022, 4, 1))
@example(date=datetime.date(2022, 4, 5))
@example(date=datetime.date(2022, 4, 6))
@example(date=datetime.date(2022, 4, 30))
@example(date=datetime.date(2022, 11, 5))
@example(date=datetime.date(2022, 11, 6))
@example(date=datetime.date(2023, 4, 5))
def test_levy_rates_apply_only_in_the_statutory_window(employer, employee_main, date):
    in_window = LEVY_START <= date < LEVY_END
    assert (rate_on(employer, date) == EMPLOYER_LEVY_RATE) == in_window
    assert (rate_on(employee_main, date) == EMPLOYEE_LEVY_RATE) == in_window


# Invariant 2: same dates.
def test_employer_and_employee_rates_change_on_the_levy_dates(employer, employee_main):
    employer_dates = change_dates(employer, LEVY_START, TAX_YEAR_END)
    employee_dates = change_dates(employee_main, LEVY_START, TAX_YEAR_END)
    assert employer_dates == employee_dates == [LEVY_START, LEVY_END]


# Invariant 3: same uplift.
@pytest.mark.parametrize(
    "date",
    [LEVY_START, datetime.date(2022, 7, 6), LEVY_END - datetime.timedelta(days=1)],
)
def test_levy_adds_one_and_a_quarter_points_to_both_rates(
    employer, employee_main, date
):
    day_before = LEVY_START - datetime.timedelta(days=1)
    for param in (employer, employee_main):
        assert rate_on(param, date) - rate_on(param, day_before) == UPLIFT


# Invariant 4: annual equivalent, exact and via fiscal_year_average.
@pytest.mark.parametrize(
    "param_name, directors_rate",
    [
        ("employer", EMPLOYER_DIRECTORS_RATE),
        ("employee_main", EMPLOYEE_DIRECTORS_RATE),
    ],
)
def test_annual_average_matches_the_directors_rate(request, param_name, directors_rate):
    param = request.getfixturevalue(param_name)
    exact = exact_annual_percentage(param, LEVY_START, TAX_YEAR_END)
    assert round(exact, 2) == directors_rate
    assert 100 * fiscal_year_average(param, 2022) == pytest.approx(
        float(exact), abs=1e-9
    )


# Invariant 5: same convention.
def model_rates(system, year):
    class_1 = system.get_parameters_at_instant(
        str(year)
    ).gov.hmrc.national_insurance.class_1
    return class_1.rates.employer, class_1.rates.employee.main


def test_neither_rate_is_blended(system):
    rates = system.parameters.gov.hmrc.national_insurance.class_1.rates
    for param in (rates.employer, rates.employee.main):
        assert not (param.metadata or {}).get("fiscal_year_blend", False)


@pytest.mark.parametrize("year", range(2015, 2031))
def test_model_year_rate_is_the_rate_at_30_april(system, employer, employee_main, year):
    model_employer, model_employee = model_rates(system, year)
    sample = datetime.date(year, 4, 30)
    assert Fraction(str(model_employer)) == rate_on(employer, sample)
    assert Fraction(str(model_employee)) == rate_on(employee_main, sample)


@pytest.mark.parametrize(
    "year, employer_rate, employee_rate",
    [
        (2021, "0.138", "0.12"),
        (2022, "0.1505", "0.1325"),
        (2023, "0.138", "0.12"),
    ],
)
def test_model_year_2022_carries_the_levy_on_both_sides(
    system, year, employer_rate, employee_rate
):
    model_employer, model_employee = model_rates(system, year)
    assert Fraction(str(model_employer)) == Fraction(employer_rate)
    assert Fraction(str(model_employee)) == Fraction(employee_rate)
