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


# 2027-28 to 2029-30 (#2384). Ofwat's PR24 final determinations sector summary
# (19 December 2024, page 21) puts the average water and wastewater company
# bill at GBP 440 in 2024-25 and GBP 597 in 2029-30, before inflation. Ofwat
# indexes bills to the previous November's CPIH, approximated by calendar year
# t-1 of obr.cpih.
CPIH = system.parameters.gov.economic_assumptions.yoy_growth.obr.cpih
FD_REAL_GROWTH = 597 / 440  # 1.3568


def test_stored_bills_reach_the_pr24_final_determination_in_real_terms():
    # Real growth 2025-26 to 2029-30 = product of (1 + nominal) / (1 + CPIH t-1).
    # Realised: 1.27 / 1.0327 * 1.054 / 1.0388 = 1.2478, so the remaining
    # three years must add 1.3568 / 1.2478 = 1.0874, or 2.83% a year in real
    # terms. Values stored to three decimals allow about 0.15% of slack.
    real = 1.0
    for year in range(2025, 2030):
        real *= (1 + WATER_BILLS(f"{year}-01-01")) / (1 + CPIH(f"{year - 1}-01-01"))
    assert real == pytest.approx(FD_REAL_GROWTH, rel=2e-3)


@pytest.mark.parametrize(
    "year, growth",
    # 1.02833 real growth times 1 + CPIH t-1 (3.24%, 3.30%, 2.14%).
    [(2027, 0.062), (2028, 0.062), (2029, 0.050)],
)
def test_projected_water_bill_growth(year, growth):
    assert WATER_BILLS(f"{year}-01-01") == pytest.approx(growth)


def test_stored_projection_matches_the_script():
    from policyengine_uk.utils.water.forecast_water_bills import (
        final_determination_real_growth,
        projected_growth,
    )

    assert final_determination_real_growth() == pytest.approx(FD_REAL_GROWTH)
    for year, growth in projected_growth().items():
        assert WATER_BILLS(f"{year}-01-01") == pytest.approx(round(growth, 3)), year
