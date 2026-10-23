import pytest

from policyengine_uk import parameters
from policyengine_uk.utils import create_ahc_deflator

AHC_GROWTH = parameters.gov.economic_assumptions.yoy_growth.obr.consumer_price_index_ahc


def _derived_growth():
    table = create_ahc_deflator.create_modified_cpi_forecast(
        create_ahc_deflator.cpi,
        create_ahc_deflator.water_index,
        create_ahc_deflator.rent_index,
        create_ahc_deflator.historical_modified_cpi,
        create_ahc_deflator.initial_weights,
    )
    return {
        int(row["period"][:4]): row["modified_cpi_yoy"] for _, row in table.iterrows()
    }


def test_stored_ahc_cpi_growth_matches_the_documented_derivation():
    # The OBR does not publish CPI excluding housing costs. Every stored value
    # must be the ONS outturn or the output of create_ahc_deflator.py, so that
    # updating CPI, rent or water bill forecasts without rerunning the script
    # fails here.
    derived = _derived_growth()
    assert sorted(derived) == list(range(2022, 2031))
    for year, growth in derived.items():
        assert AHC_GROWTH(f"{year}-01-01") == pytest.approx(
            round(growth, 4), abs=1e-9
        ), year


def test_ahc_cpi_growth_2026_removes_rents_from_cpi():
    # OBR March 2026: calendar-2026 CPI 2.30%, actual rents 3.34%. Rents grow
    # faster than CPI, so removing them leaves lower growth than CPI.
    cpi_growth = parameters.gov.economic_assumptions.yoy_growth.obr.consumer_price_index
    assert AHC_GROWTH("2026-01-01") == pytest.approx(0.0217, abs=1e-9)
    assert AHC_GROWTH("2026-01-01") < cpi_growth("2026-01-01")
