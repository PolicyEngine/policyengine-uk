"""The published Ofwat years of the water bills series match their sources.

2025-26: Ofwat, "Ofwat responds to water sector average bill figures"
(29 January 2026) reports a 27% increase in 2025-26, replacing the 26%
forecast in its 30 January 2025 statement.
2026-27: Water UK (28 January 2026) puts the national average bill at GBP 639,
up GBP 33 or 5.4%.
"""

import pytest

from policyengine_uk.system import system

WATER_BILLS = system.parameters.gov.economic_assumptions.yoy_growth.ofwat.water_bills
WATER_INDEX = system.parameters.gov.economic_assumptions.indices.ofwat.water_bills


@pytest.mark.parametrize("year, growth", [(2025, 0.27), (2026, 0.054)])
def test_published_water_bill_growth(year, growth):
    assert WATER_BILLS(f"{year}-01-01") == pytest.approx(growth)


def test_water_index_compounds_the_published_years():
    ratio = WATER_INDEX("2026-01-01") / WATER_INDEX("2024-01-01")
    assert ratio == pytest.approx(1.27 * 1.054, rel=1e-3)
