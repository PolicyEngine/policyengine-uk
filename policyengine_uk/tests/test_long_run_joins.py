"""The long-run paths join the last EFO year in equal steps.

The October 2026 EFO forecasts to 2031. From 2032, RPI and CPIH step from
its 2031 forecast to 2.39% in 2035, and average earnings to 3.83% in 2036,
each step rounded to 4 decimals; the rates then hold. The receipts series
follow average earnings after their own forecast. Before this, the March
2026 path jumped earnings from 3.32% in 2031 to 3.71% in 2032, and no test
noticed.
"""

import pytest

from policyengine_uk.system import system

OBR = system.parameters.gov.economic_assumptions.yoy_growth.obr
LAST_EFO_YEAR = 2031


def rate(series, year):
    return series(f"{year}-01-01")


def equal_steps(start, end, steps):
    return [round(start + (end - start) * k / steps, 4) for k in range(steps + 1)]


@pytest.mark.parametrize(
    "name, steady_state, steady_year",
    [("rpi", 0.0239, 2035), ("cpih", 0.0239, 2035), ("average_earnings", 0.0383, 2036)],
)
def test_long_run_path_steps_evenly_to_its_steady_state(
    name, steady_state, steady_year
):
    series = getattr(OBR, name)
    start = rate(series, LAST_EFO_YEAR)
    years = range(LAST_EFO_YEAR, steady_year + 1)
    expected = equal_steps(start, steady_state, steady_year - LAST_EFO_YEAR)
    assert [rate(series, year) for year in years] == pytest.approx(expected, abs=1e-12)
    for year in range(steady_year, 2074):
        assert rate(series, year) == steady_state, (name, year)


def test_cpi_holds_its_target_after_the_efo():
    for year in range(LAST_EFO_YEAR + 1, 2074):
        assert rate(OBR.consumer_price_index, year) == 0.02, year


@pytest.mark.parametrize(
    "path",
    [
        ("stamp_duty_land_tax", "residential"),
        ("stamp_duty_land_tax", "non_residential"),
        ("business_rates", "great_britain"),
        ("business_rates", "northern_ireland"),
    ],
)
def test_receipts_series_follow_earnings_after_the_efo(path):
    series = OBR
    for key in path:
        series = getattr(series, key)
    for year in range(LAST_EFO_YEAR + 1, 2074):
        assert rate(series, year) == rate(OBR.average_earnings, year), (path, year)
