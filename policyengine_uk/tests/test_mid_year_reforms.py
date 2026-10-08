"""
Reforms dated part-way through a year on fiscal-year-blended parameters.

Parameters with `fiscal_year_blend: true` hold one day-weighted average per
model year (6 April to 5 April). A reform dated part-way through a year is
replayed on the dated schedule and re-averaged, so model year 2026 changes
by the day-weighted fiscal-year amount. Whole-year reforms (bare years, and
ranges starting 1 January and ending 31 December) keep their values exactly.

The expected amounts assume equal daily consumption across the year, which
is what the day weighting means.
"""

import datetime

import pytest
from policyengine_core.periods import instant
from policyengine_core.reforms import Reform

from policyengine_uk import Simulation
from policyengine_uk.model_api import Scenario
from policyengine_uk.system import system

FUEL = "gov.hmrc.fuel_duty.petrol_and_diesel"
CGT = "gov.hmrc.cgt.basic_rate"
LITRES = 1_200
YEARS = range(2015, 2041)

SITUATION = {
    "people": {"adult": {"age": {2026: 40}}},
    "benunits": {"benunit": {"members": ["adult"]}},
    "households": {
        "household": {
            "members": ["adult"],
            "petrol_litres": {year: LITRES for year in (2026, 2027)},
            "diesel_litres": {year: 0 for year in (2026, 2027)},
            "in_rural_fuel_duty_relief_area": {2026: False, 2027: False},
        }
    },
}


def dated(path):
    """The dated schedule the model-year values are averaged from."""
    return system.parameters.baseline.get_child(path)


def model_year_days(year):
    start = datetime.date(year, 4, 6)
    end = datetime.date(year + 1, 4, 6)
    return [start + datetime.timedelta(days=i) for i in range((end - start).days)]


def day_weighted(path, year, overrides):
    """Average of the dated schedule over a model year, with dated overrides.

    overrides is a list of (first_day, last_day, value), applied in order.
    """
    schedule = dated(path)
    total = 0.0
    days = model_year_days(year)
    for day in days:
        value = schedule(day.isoformat())
        for first, last, override in overrides:
            if first <= day <= last:
                value = override
        total += value
    return total / len(days)


def fuel_duty(year, reform=None, scenario=None):
    simulation = Simulation(situation=SITUATION, reform=reform, scenario=scenario)
    return float(simulation.calculate("fuel_duty", year)[0])


def change(year, reform):
    return fuel_duty(year, reform) - fuel_duty(year)


def converted(path):
    return system.parameters.get_child(path)


ONWARDS = datetime.date(2100, 12, 31)


def test_mid_year_start_is_day_weighted_over_the_model_year():
    """The #2167 example: 60p a litre from 1 September 2026, persistently.

    Before the fix the 2026 change was +£24.19, because months before
    September kept a baseline average that includes the January and March
    2027 increases the reform replaces.
    """
    reform = Reform.from_dict({FUEL: {"2026-09-01.2100-12-31": 0.60}}, "uk")
    expected = LITRES * (
        day_weighted(FUEL, 2026, [(datetime.date(2026, 9, 1), ONWARDS, 0.60)])
        - converted(FUEL)("2026")
    )
    assert expected == pytest.approx(38.2636, abs=1e-4)
    # fuel_duty is computed in float32.
    assert change(2026, reform) == pytest.approx(expected, rel=1e-5)
    # From model year 2027 the reform covers the whole year.
    assert change(2027, reform) == pytest.approx(
        LITRES * (0.60 - converted(FUEL)("2027")), rel=1e-5
    )


def test_change_that_expires_within_the_year_reverts_to_the_schedule():
    reform = Reform.from_dict({FUEL: {"2026-09-01.2027-01-31": 0.60}}, "uk")
    window = (datetime.date(2026, 9, 1), datetime.date(2027, 1, 31), 0.60)
    expected = LITRES * (day_weighted(FUEL, 2026, [window]) - converted(FUEL)("2026"))
    assert change(2026, reform) == pytest.approx(expected, rel=1e-5)
    assert change(2027, reform) == pytest.approx(0, abs=1e-6)


def test_several_changes_within_one_year():
    reform = Reform.from_dict(
        {FUEL: {"2026-07-01.2026-10-31": 0.50, "2026-11-01.2100-12-31": 0.62}},
        "uk",
    )
    expected = LITRES * (
        day_weighted(
            FUEL,
            2026,
            [
                (datetime.date(2026, 7, 1), datetime.date(2026, 10, 31), 0.50),
                (datetime.date(2026, 11, 1), ONWARDS, 0.62),
            ],
        )
        - converted(FUEL)("2026")
    )
    assert change(2026, reform) == pytest.approx(expected, rel=1e-5)


def test_cgt_rate_change_part_way_through_the_year():
    reform = Reform.from_dict({CGT: {"2026-10-01.2100-12-31": 0.24}}, "uk")
    simulation = Simulation(situation=SITUATION, reform=reform)
    rate = simulation.tax_benefit_system.parameters.get_child(CGT)
    expected = day_weighted(CGT, 2026, [(datetime.date(2026, 10, 1), ONWARDS, 0.24)])
    assert rate("2026") == pytest.approx(expected, abs=1e-12)
    assert converted(CGT)("2026") < rate("2026") < 0.24
    assert rate("2027") == pytest.approx(0.24, abs=1e-12)


def test_temporary_zero_rate_with_the_electricity_vat_dates():
    """The #2166 dates on a blended parameter: 0% from 1 October 2026 to 31
    March 2027, then 5% from 1 April 2027.

    Replace with the electricity VAT rate once #2166 adds it.
    """
    reform = Reform.from_dict(
        {FUEL: {"2026-10-01.2027-03-31": 0.0, "2027-04-01.2100-12-31": 0.05}},
        "uk",
    )
    simulation = Simulation(situation=SITUATION, reform=reform)
    rate = simulation.tax_benefit_system.parameters.get_child(FUEL)
    expected = day_weighted(
        FUEL,
        2026,
        [
            (datetime.date(2026, 10, 1), datetime.date(2027, 3, 31), 0.0),
            (datetime.date(2027, 4, 1), ONWARDS, 0.05),
        ],
    )
    baseline = dated(FUEL)
    # 6 April to 30 September at the schedule (178 days at 52.95p), 182
    # zero-rated days, and 1 to 5 April 2027 at 5%.
    assert baseline("2026-04-06") == baseline("2026-09-30") == 0.5295
    assert expected == pytest.approx((178 * 0.5295 + 5 * 0.05) / 365, abs=1e-12)
    assert rate("2026") == pytest.approx(expected, abs=1e-12)
    assert rate("2027") == pytest.approx(0.05, abs=1e-12)


@pytest.mark.parametrize(
    "period_values",
    [
        {"2027": 0.5595},
        {"2026-01-01.2100-12-31": 0.60},
        {"2026-01-01.2027-12-31": 0.60},
        {"year:2026:2": 0.60},
        0.60,
    ],
)
def test_whole_year_reforms_keep_their_values_exactly(period_values):
    """1 January and 31 December bound model years on the converted tree.

    These reforms are applied exactly as before: every model-year value is
    the one the reform writes to the converted tree.
    """
    reform = Reform.from_dict({FUEL: period_values}, "uk")
    reformed = Simulation(situation=SITUATION, reform=reform)
    expected = converted(FUEL).clone()
    if isinstance(period_values, dict):
        for key, value in period_values.items():
            if "." in key:
                start, stop = key.split(".")
                expected.update(start=instant(start), stop=instant(stop), value=value)
            elif ":" in key:
                expected.update(period=key, value=value)
            else:
                expected.update(start=instant(key), value=value)
    else:
        expected.update(period="year:2000:100", value=period_values)
    parameter = reformed.tax_benefit_system.parameters.get_child(FUEL)
    for year in YEARS:
        assert parameter(str(year)) == expected(str(year)), year


def test_later_reform_keeps_an_earlier_mid_year_change():
    first = Reform.from_dict({FUEL: {"2026-09-01.2100-12-31": 0.60}}, "uk")
    second = Reform.from_dict({FUEL: {"2028": 0.70}}, "uk")
    simulation = Simulation(situation=SITUATION, reform=(first, second))
    parameter = simulation.tax_benefit_system.parameters.get_child(FUEL)
    assert parameter("2026") == pytest.approx(
        day_weighted(FUEL, 2026, [(datetime.date(2026, 9, 1), ONWARDS, 0.60)]),
        abs=1e-12,
    )
    assert parameter("2027") == pytest.approx(0.60, abs=1e-12)
    assert parameter("2028") == pytest.approx(0.70, abs=1e-12)


def test_dict_reform_with_a_range_key_is_day_weighted():
    reform = {FUEL: {"2026-09-01.2100-12-31": 0.60}}
    expected = LITRES * (
        day_weighted(FUEL, 2026, [(datetime.date(2026, 9, 1), ONWARDS, 0.60)])
        - converted(FUEL)("2026")
    )
    assert change(2026, reform) == pytest.approx(expected, rel=1e-5)


def test_reform_applied_before_data_load_is_day_weighted():
    reform = Reform.from_dict({FUEL: {"2026-09-01.2100-12-31": 0.60}}, "uk")
    scenario = Scenario.from_reform(reform)
    scenario.applied_before_data_load = True
    expected = LITRES * (
        day_weighted(FUEL, 2026, [(datetime.date(2026, 9, 1), ONWARDS, 0.60)])
        - converted(FUEL)("2026")
    )
    assert fuel_duty(2026, scenario=scenario) - fuel_duty(2026) == pytest.approx(
        expected, rel=1e-5
    )


def test_reform_leaves_the_baseline_schedule_untouched():
    reform = Reform.from_dict({FUEL: {"2026-09-01.2100-12-31": 0.60}}, "uk")
    simulation = Simulation(situation=SITUATION, reform=reform)
    schedule = simulation.tax_benefit_system.parameters.baseline.get_child(FUEL)
    assert schedule("2026-10-01") == pytest.approx(0.5295)
    assert schedule("2027-03-01") == pytest.approx(0.5795)
    assert (
        "update"
        not in simulation.tax_benefit_system.parameters.get_child(FUEL).__dict__
    )


def test_unblended_parameter_is_not_re_averaged():
    """Blending is opt-in: a mid-year reform to an unblended parameter is
    applied to the converted tree as written."""
    path = "gov.hmrc.national_insurance.class_1.rates.employee.main"
    reform = Reform.from_dict({path: {"2026-09-01.2100-12-31": 0.10}}, "uk")
    simulation = Simulation(situation=SITUATION, reform=reform)
    parameter = simulation.tax_benefit_system.parameters.get_child(path)
    assert parameter("2026-08-31") == converted(path)("2026")
    assert parameter("2026-09-01") == 0.10
