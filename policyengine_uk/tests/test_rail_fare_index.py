"""The projected regulated rail fare rises follow the RPI forecast.

Regulated fares rise each January by July RPI of the year before plus 1
point (2026 was frozen under current law). The 2027 rise uses the published
July 2026 RPI (3.2%). From 2028 the projection uses the previous calendar
year's growth in yoy_growth.obr.rpi plus 1 point, rounded to 0.1 points, so a
refreshed RPI forecast that leaves these indices stale fails here.
"""

import pytest

from policyengine_uk import parameters

RAIL = parameters.gov.dft.rail
RPI = parameters.gov.economic_assumptions.yoy_growth.obr.rpi


def rise(index, year):
    return index(f"{year}-01-01") / index(f"{year - 1}-01-01") - 1


@pytest.mark.parametrize("name", ["fare_index", "prior_law_fare_index"])
def test_2027_rise_is_july_2026_rpi_plus_one_point(name):
    assert rise(getattr(RAIL, name), 2027) == pytest.approx(0.042, abs=5e-4)


@pytest.mark.parametrize("name", ["fare_index", "prior_law_fare_index"])
@pytest.mark.parametrize("year", range(2028, 2032))
def test_projected_rise_is_previous_year_rpi_plus_one_point(name, year):
    expected = round(RPI(f"{year - 1}-01-01") + 0.01, 3)
    # Each index level is rounded to 3 decimals, which moves a rise by at
    # most about 0.05 points.
    assert rise(getattr(RAIL, name), year) == pytest.approx(expected, abs=5e-4)


def test_current_law_holds_the_2026_freeze():
    assert rise(RAIL.fare_index, 2026) == 0
