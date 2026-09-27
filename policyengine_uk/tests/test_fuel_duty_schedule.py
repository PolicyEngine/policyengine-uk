"""
The petrol and diesel fuel duty rate follows its dated schedule.

Each rate is keyed to the date it takes effect, and `fiscal_year_blend`
day-weights the schedule across each model year (6 April to 5 April). Rates
from 1 April 2027 are an RPI forecast: Budget 2025 policy, not yet law.
"""

import datetime
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from policyengine_core.parameters import ParameterNode

import policyengine_uk
from policyengine_uk import Microsimulation
from policyengine_uk.model_api import Scenario
from policyengine_uk.system import system

PATH = "gov.hmrc.fuel_duty.petrol_and_diesel"
FORECAST_YEARS = range(2027, 2032)
CONVERTED_YEARS = range(2015, 2041)


def raw_parameters() -> ParameterNode:
    """Parameters as written, before uprating and fiscal-year conversion."""
    directory = Path(policyengine_uk.__file__).parent / "parameters"
    return ParameterNode(directory_path=str(directory))


def dated_schedule():
    """The dated rate after uprating extends it, before annual conversion.

    The baseline tree goes through uprating but not fiscal-year conversion.
    """
    return system.parameters.baseline.gov.hmrc.fuel_duty.petrol_and_diesel


def model_year_rate(year: int) -> float:
    return system.parameters.gov.hmrc.fuel_duty.petrol_and_diesel(str(year))


def model_year_days(year: int) -> list:
    start = datetime.date(year, 4, 6)
    end = datetime.date(year + 1, 4, 6)
    return [start + datetime.timedelta(days=i) for i in range((end - start).days)]


@pytest.mark.parametrize(
    "date, rate",
    [
        # 60.97p was written into the Act for 2012 but never charged.
        ("2012-06-01", 0.5795),
        ("2022-03-22", 0.5795),
        ("2022-03-23", 0.5295),
        # SI 2026/555 removed the 1 September 2026 step and moved the
        # 1 December 2026 step to 1 January 2027.
        ("2026-09-01", 0.5295),
        ("2026-12-01", 0.5295),
        ("2026-12-31", 0.5295),
        ("2027-01-01", 0.5595),
        ("2027-02-28", 0.5595),
        ("2027-03-01", 0.5795),
        ("2027-03-31", 0.5795),
    ],
)
def test_statutory_rate_on_each_date(date, rate):
    schedule = raw_parameters().gov.hmrc.fuel_duty.petrol_and_diesel
    assert schedule(date) == pytest.approx(rate, abs=1e-12)


# Model year Y runs from 6 April Y to 5 April Y+1. Rates from 1 April 2027:
# 59.75p, then 61.54p (2028), 63.26p (2029), 65.09p (2030), 66.59p (2031).
HAND_COMPUTED = {
    2025: 0.5295,
    # 6 Apr to 31 Dec 2026, Jan to Feb 2027, Mar 2027, 1 to 5 Apr 2027.
    2026: (0.5295 * 270 + 0.5595 * 59 + 0.5795 * 31 + 0.5975 * 5) / 365,
    # 2028 is a leap year: 361 days to 31 March, then 5 days.
    2027: (0.5975 * 361 + 0.6154 * 5) / 366,
    2028: (0.6154 * 360 + 0.6326 * 5) / 365,
    2029: (0.6326 * 360 + 0.6509 * 5) / 365,
    2030: (0.6509 * 360 + 0.6659 * 5) / 365,
}


@pytest.mark.parametrize("year, rate", HAND_COMPUTED.items())
def test_model_year_rate_is_hand_computed_day_weighted_average(year, rate):
    assert model_year_rate(year) == pytest.approx(rate, abs=1e-12)


def test_forecast_steps_use_current_rpi_forecast():
    """The written 1 April steps match the RPI series they claim to use.

    Fails when the RPI forecast in yoy_growth.yaml changes. Regenerate with
    `uv run python policyengine_uk/parameters/gov/hmrc/fuel_duty/calculate_fuel_duty_rates.py --update`.
    """
    parameters = raw_parameters()
    rpi = parameters.gov.economic_assumptions.yoy_growth.obr.rpi
    schedule = parameters.gov.hmrc.fuel_duty.petrol_and_diesel
    rate = Decimal("0.5795")
    for year in FORECAST_YEARS:
        growth = Decimal(str(rpi(f"{year - 1}-01-01")))
        rate = (rate * (1 + growth)).quantize(Decimal("0.0001"), ROUND_HALF_UP)
        assert schedule(f"{year}-04-01") == pytest.approx(float(rate), abs=1e-12), (
            f"{year}-04-01 is stale against the RPI forecast; run "
            "calculate_fuel_duty_rates.py --update"
        )
        assert schedule(f"{year}-03-31") != schedule(f"{year}-04-01")


def test_uprating_continues_each_april_after_the_written_steps():
    schedule = dated_schedule()
    rpi = system.parameters.baseline.gov.economic_assumptions.yoy_growth.obr.rpi
    for year in range(max(FORECAST_YEARS) + 1, 2041):
        previous = schedule(f"{year - 1}-04-01")
        assert schedule(f"{year}-03-31") == previous
        expected = previous * (1 + rpi(f"{year - 1}-01-01"))
        # Rounded to 0.01p, from a five-decimal index.
        assert schedule(f"{year}-04-01") == pytest.approx(expected, abs=6e-5)


@pytest.mark.parametrize("year", CONVERTED_YEARS)
def test_model_year_rate_equals_day_by_day_average(year):
    """Differential check of the interval average against a daily sum."""
    schedule = dated_schedule()
    days = model_year_days(year)
    daily = sum(schedule(day.isoformat()) for day in days) / len(days)
    assert model_year_rate(year) == pytest.approx(daily, rel=1e-12)


@pytest.mark.parametrize("year", CONVERTED_YEARS)
def test_model_year_rate_lies_between_the_rates_in_force(year):
    schedule = dated_schedule()
    rates = {schedule(day.isoformat()) for day in model_year_days(year)}
    assert min(rates) - 1e-12 <= model_year_rate(year) <= max(rates) + 1e-12


def test_model_year_rates_do_not_fall_after_the_2022_cut():
    """Intended while every scheduled step and forecast RPI rate is a rise."""
    rates = [model_year_rate(year) for year in range(2022, 2041)]
    # Equal-rate segments can sum to a last-digit float difference.
    assert all(later >= earlier - 1e-12 for earlier, later in zip(rates, rates[1:]))


def fuel_duty_simulation(parameter_changes=None):
    situation = {
        "people": {"adult": {"age": {2026: 40}}},
        "benunits": {"benunit": {"members": ["adult"]}},
        "households": {
            "household": {
                "members": ["adult"],
                "petrol_litres": {year: 1_000 for year in range(2025, 2032)},
            }
        },
    }
    scenario = (
        Scenario(parameter_changes=parameter_changes) if parameter_changes else None
    )
    return Microsimulation(situation=situation, scenario=scenario)


def test_holding_55_95p_for_2027_removes_the_full_2027_28_rate_rise():
    """Regression: calendar-year averaging cut this effect to 3.30p a litre.

    The 2027-28 baseline is 59.77p, so holding 55.95p saves 3.82p a litre.
    """
    baseline = fuel_duty_simulation()
    reformed = fuel_duty_simulation({PATH: {"2027": 0.5595}})
    saving = (
        baseline.calculate("fuel_duty", 2027).values[0]
        - reformed.calculate("fuel_duty", 2027).values[0]
    )
    assert saving == pytest.approx(1_000 * (HAND_COMPUTED[2027] - 0.5595))


@settings(max_examples=8, deadline=None)
@given(
    year=st.integers(min_value=2026, max_value=2030),
    rate=st.decimals(min_value=0, max_value=2, places=4).map(float),
)
def test_annual_override_applies_at_full_strength_and_only_to_its_year(year, rate):
    reformed = fuel_duty_simulation({PATH: {str(year): rate}})
    parameter = reformed.tax_benefit_system.parameters.gov.hmrc.fuel_duty
    assert parameter.petrol_and_diesel(str(year)) == pytest.approx(rate, abs=1e-12)
    assert reformed.calculate("fuel_duty", year).values[0] == pytest.approx(
        1_000 * rate
    )
    for other in CONVERTED_YEARS:
        if other != year:
            assert parameter.petrol_and_diesel(str(other)) == pytest.approx(
                model_year_rate(other), abs=1e-12
            )
