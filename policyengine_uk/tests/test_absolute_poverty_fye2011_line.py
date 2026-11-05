"""The absolute low-income line on the FYE 2011 reference, in every year.

From its March 2026 release HBAI measures absolute low income against the
FYE 2025 median from FYE 2022 (methodology report, section 2.3), and
absolute_poverty_threshold_* follow it. Most absolute poverty estimates
published before then use the FYE 2011 line in every year.
absolute_poverty_threshold_fye2011_* keep that line. policyengine-uk labels
FYE 2011 (2010-11) as period 2010.

Invariants:

1. Before the switch: from FYE 2011 to FYE 2021 the FYE 2011 line equals
   HBAI's current line, which keeps the FYE 2011 reference for those years.
2. Published values: from FYE 2022 to FYE 2025 the line is 60% of the FYE
   2011 median in that year's prices, to the penny. Each edition's summary
   table 1.2b states every year's medians in that edition's prices, so its
   2010/11 row is the FYE 2011 median in prices of the edition's year.
3. Deflator: those medians are DWP's FYE 2011 median (SN 5828) times the
   ratio of HBAI's annual deflators (BHCYRDEF / AHCYRDEF, HBAI variables
   guide), to float32 precision.
4. Forward uprating: from FYE 2025 the line moves with OBR CPI, as HBAI's
   current line does, so the ratio of the two lines stays at its FYE 2025
   value.
5. The FYE 2011 line is below the FYE 2025 line from FYE 2022, since real
   median income grew between FYE 2011 and FYE 2025.
6. Variable layer: poverty_threshold_fye2011_* is the weekly line times 52,
   and in_absolute_poverty_fye2011_* holds exactly when equivalised income
   is below it.
"""

from decimal import ROUND_HALF_UP, Decimal

import pytest

from policyengine_uk import Simulation
from policyengine_uk.system import system

MEASURES = ("bhc", "ahc")
FYE_2011 = 2010
FYE_2021 = 2020
FYE_2025 = 2024

# DWP's FYE 2011 absolute median, pounds a week in FYE 2011 prices: UK Data
# Service SN 5828, "Net absolute median household income values over time".
MEDIAN_FYE_2011 = {"bhc": 418.9101257, "ahc": 358.1600647}

# The FYE 2011 median in each year's prices: the 2010/11 row, quintile 3
# (median) column, of summary table 1.2b in the HBAI edition for that year
# (FYE 2022, published 23 March 2023; FYE 2023, 21 March 2024; FYE 2024,
# 27 March 2025; FYE 2025, 26 March 2026).
TABLE_1_2B_MEDIAN = {
    "bhc": {
        2021: 523.5219544852621,
        2022: 578.1422821857581,
        2023: 616.5616652293272,
        2024: 634.6141464184742,
    },
    "ahc": {
        2021: 450.26964503456543,
        2022: 498.4987027116655,
        2023: 526.5664329991581,
        2024: 536.4494366215147,
    },
}

# HBAI's annual deflators, 2015 = 100 (HBAI variables guide FYE 2025,
# Deflators sheet): FYE 2011, then FYE 2022 to FYE 2025.
DEFLATOR_FYE_2011 = {"bhc": 90.5, "ahc": 90.6}
DEFLATOR = {
    "bhc": {2021: 113.1, 2022: 124.9, 2023: 133.2, 2024: 137.1},
    "ahc": {2021: 113.9, 2022: 126.1, 2023: 133.2, 2024: 135.7},
}


def fye2011_line(measure, year):
    return getattr(
        system.parameters(str(year)).household.poverty,
        f"absolute_poverty_threshold_fye2011_{measure}",
    )


def current_line(measure, year):
    return getattr(
        system.parameters(str(year)).household.poverty,
        f"absolute_poverty_threshold_{measure}",
    )


def to_penny(value):
    return float(Decimal(repr(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


@pytest.mark.parametrize("measure", MEASURES)
@pytest.mark.parametrize("year", range(FYE_2011, FYE_2021 + 1))
def test_fye2011_line_matches_hbai_line_before_fye_2022(measure, year):
    assert fye2011_line(measure, year) == current_line(measure, year)


@pytest.mark.parametrize("measure", MEASURES)
@pytest.mark.parametrize("year", range(FYE_2021 + 1, FYE_2025 + 1))
def test_fye2011_line_is_60_percent_of_published_fye2011_median(measure, year):
    expected = to_penny(0.6 * TABLE_1_2B_MEDIAN[measure][year])
    assert fye2011_line(measure, year) == pytest.approx(expected, abs=1e-9)


@pytest.mark.parametrize("measure", MEASURES)
@pytest.mark.parametrize("year", range(FYE_2021 + 1, FYE_2025 + 1))
def test_published_fye2011_median_follows_hbai_deflator(measure, year):
    ratio = DEFLATOR[measure][year] / DEFLATOR_FYE_2011[measure]
    assert TABLE_1_2B_MEDIAN[measure][year] == pytest.approx(
        MEDIAN_FYE_2011[measure] * ratio, rel=1e-7
    )


@pytest.mark.parametrize("measure", MEASURES)
@pytest.mark.parametrize("year", range(FYE_2025 + 1, 2031))
def test_fye2011_line_uprates_with_cpi_like_the_current_line(measure, year):
    base_ratio = fye2011_line(measure, FYE_2025) / current_line(measure, FYE_2025)
    ratio = fye2011_line(measure, year) / current_line(measure, year)
    assert ratio == pytest.approx(base_ratio, rel=1e-6)
    assert fye2011_line(measure, year) > fye2011_line(measure, year - 1)


@pytest.mark.parametrize("measure", MEASURES)
@pytest.mark.parametrize("year", range(FYE_2021 + 1, 2031))
def test_fye2011_line_is_below_fye2025_line_after_the_switch(measure, year):
    assert 0 < fye2011_line(measure, year) < current_line(measure, year)


@pytest.mark.parametrize("measure", MEASURES)
@pytest.mark.parametrize("year", [2015, 2020, 2021, 2024, 2025, 2029])
def test_variables_use_the_fye2011_line(measure, year):
    income_variable = {
        "bhc": "equiv_hbai_household_net_income",
        "ahc": "equiv_hbai_household_net_income_ahc",
    }[measure]
    annual_line = fye2011_line(measure, year) * 52
    simulation = Simulation(
        situation={
            "people": {"adult": {"age": 40}},
            "households": {"household": {"members": ["adult"]}},
        }
    )
    assert simulation.calculate(
        f"poverty_threshold_fye2011_{measure}", year
    ) == pytest.approx(annual_line, rel=1e-6)
    for income, in_poverty in (
        (annual_line - 1, True),
        (annual_line + 1, False),
    ):
        simulation = Simulation(
            situation={
                "people": {"adult": {"age": 40}},
                "households": {"household": {"members": ["adult"]}},
            }
        )
        simulation.set_input(income_variable, year, [income])
        assert (
            bool(
                simulation.calculate(f"in_absolute_poverty_fye2011_{measure}", year)[0]
            )
            is in_poverty
        )
