"""The HBAI absolute low-income line from FYE 2011 to FYE 2021.

Before FYE 2022, HBAI's absolute low-income line is 60% of the FYE 2011
median held constant in real terms. DWP publishes that median in each year's
prices (UK Data Service SN 5828, "Net absolute median household income values
over time"). HBAI deflates with its own CPI variants: the ONS experimental CPI
including mortgage interest payments, ground rent and dwelling insurance
before housing costs, and CPI excluding rents, maintenance repairs and water
charges after housing costs (DWP statistical notice on adjusting for
inflation, April 2016). policyengine-uk labels FYE 2011 (2010-11) as period
2010, so these are periods 2010 to 2020.

Invariants:

1. Published values: in every period from 2010 to 2020 the line is 60% of
   DWP's published FYE 2011 median in that year's prices, to the penny.
2. Deflator differential: HBAI's annual deflator is the April-to-March mean
   of its monthly deflator, rounded half up to one decimal place (SN 5828
   variables guide, Deflators sheet). The published medians are the FYE 2011
   median times the ratio of annual deflators, to float32 precision, and the
   line is the FYE 2011 line times the same ratio, to within half a penny.
3. Monotonicity: between any two of these years the line moves in the same
   direction as the deflator: up where the deflator rises and flat where it
   is flat (AHC, FYE 2015 to FYE 2016).
4. No flat gap: every period from 2011 to 2020 has its own explicit value,
   above the FYE 2011 line. From #1212 until #1890 fixed it, periods 2011 to
   2019 returned the FYE 2011 value, because parameter uprating only extends
   values after the last explicit date.

test_absolute_poverty_reference_year.py and the poverty_threshold_* YAML
tests cover the variable layer for these years.
"""

import itertools
from decimal import ROUND_HALF_UP, Decimal

import numpy as np
import pytest
from hypothesis import HealthCheck, example, given, settings
from hypothesis import strategies as st

from policyengine_uk.system import system

POVERTY = system.parameters.household.poverty
MEASURES = ("bhc", "ahc")
FYE_2011 = 2010
FYE_2021 = 2020
YEARS = range(FYE_2011, FYE_2021 + 1)

# DWP's published FYE 2011 absolute median in each year's prices, pounds a
# week, (BHC, AHC): UK Data Service SN 5828, HBAI FYE 1995 to FYE 2025
# harmonised dataset, "Net absolute median household income values over time",
# unrounded column. DWP took them from Stat-Xplore to FYE 2020 and from HBAI
# table 1.2db for FYE 2021. The FYE 2011 medians were first published as 419
# and 359 and revised in the FYE 2020 edition (child maintenance income).
PUBLISHED_MEDIAN = {
    2010: (418.9101257, 358.1600647),
    2011: (436.4997253, 373.5775452),
    2012: (448.0718384, 383.4605408),
    2013: (458.2552795, 392.1575928),
    2014: (462.8841248, 395.7154541),
    2015: (463.3470154, 395.7154541),
    2016: (467.51297, 399.6686707),
    2017: (480.0108337, 411.923584),
    2018: (491.5829468, 421.8065796),
    2019: (500.3777466, 429.317688),
    2020: (502.2292843647297, 431.6895982245351),
}

# HBAI's monthly deflators (2015 = 100), April to March of each financial
# year: SN 5828 variables guide, Deflators sheet. HBAI does not revise a month
# once it has used it, so each year matches the ONS ad hoc release current
# when DWP first published that year: 008572 for FYE 2011 to FYE 2018, 009959
# for FYE 2019, 12455 for FYE 2020 and 13565 for FYE 2021. Later ONS releases
# revised some months (BHC January to March 2021 in 14926, for example).
MONTHLY_DEFLATOR = {
    "bhc": {
        2010: (89.3, 89.5, 89.6, 89.5, 89.9, 90.0)
        + (90.2, 90.5, 91.4, 91.5, 92.1, 92.4),
        2011: (93.3, 93.5, 93.4, 93.4, 93.9, 94.5)
        + (94.6, 94.7, 95.1, 94.7, 95.2, 95.5),
        2012: (96.1, 96.0, 95.6, 95.7, 96.2, 96.6)
        + (97.1, 97.2, 97.7, 97.2, 97.9, 98.2),
        2013: (98.4, 98.6, 98.4, 98.3, 98.8, 99.1)
        + (99.1, 99.2, 99.6, 99.0, 99.5, 99.7),
        2014: (100.0, 100.0, 100.2, 99.9, 100.2, 100.3)
        + (100.4, 100.1, 100.1, 99.3, 99.5, 99.7),
        2015: (100.0, 100.1, 100.2, 100.0, 100.2, 100.1)
        + (100.3, 100.2, 100.3, 99.5, 99.8, 100.1),
        2016: (100.2, 100.4, 100.5, 100.5, 100.7, 101.0)
        + (101.0, 101.2, 101.7, 101.2, 101.9, 102.2),
        2017: (102.7, 103.0, 102.9, 102.8, 103.4, 103.7)
        + (103.8, 104.2, 104.6, 104.2, 104.7, 104.8),
        2018: (105.2, 105.6, 105.6, 105.5, 106.4, 106.4)
        + (106.6, 106.8, 107.0, 106.2, 106.7, 106.9),
        2019: (107.4, 107.8, 107.7, 107.8, 108.2, 108.3)
        + (108.1, 108.4, 108.4, 108.1, 108.5, 108.5),
        2020: (108.4, 108.2, 108.3, 108.8, 108.4, 108.8)
        + (108.8, 108.6, 108.9, 107.8, 108.1, 108.4),
    },
    "ahc": {
        2010: (89.4, 89.6, 89.7, 89.5, 90.0, 89.9)
        + (90.2, 90.5, 91.5, 91.6, 92.3, 92.6),
        2011: (93.5, 93.7, 93.6, 93.5, 94.1, 94.7)
        + (94.8, 95.0, 95.4, 94.8, 95.5, 95.8),
        2012: (96.2, 96.2, 95.7, 95.8, 96.3, 96.7)
        + (97.2, 97.4, 97.9, 97.4, 98.1, 98.5),
        2013: (98.6, 98.8, 98.6, 98.5, 99.0, 99.3)
        + (99.4, 99.5, 99.9, 99.2, 99.8, 100.0),
        2014: (100.3, 100.2, 100.4, 100.0, 100.4, 100.5)
        + (100.6, 100.3, 100.3, 99.3, 99.6, 99.8),
        2015: (100.0, 100.2, 100.2, 100.0, 100.2, 100.1)
        + (100.2, 100.2, 100.3, 99.4, 99.7, 100.1),
        2016: (100.1, 100.3, 100.5, 100.5, 100.8, 101.1)
        + (101.1, 101.4, 101.9, 101.3, 102.1, 102.5),
        2017: (103.0, 103.4, 103.3, 103.3, 103.9, 104.2)
        + (104.4, 104.7, 105.1, 104.5, 105.0, 105.2),
        2018: (105.6, 106.1, 106.0, 106.0, 106.8, 106.9)
        + (107.0, 107.3, 107.5, 106.6, 107.2, 107.4),
        2019: (108.0, 108.3, 108.3, 108.3, 108.8, 108.9)
        + (108.7, 108.9, 108.9, 108.5, 109.0, 109.0),
        2020: (108.8, 108.8, 108.9, 109.4, 108.9, 109.4)
        + (109.4, 109.2, 109.5, 109.2, 109.4, 109.7),
    },
}

# HBAI's annual deflators (BHCYRDEF, AHCYRDEF), FYE 2011 to FYE 2021, as
# quoted in the parameter files.
ANNUAL_DEFLATOR = {
    "bhc": (90.5, 94.3, 96.8, 99.0, 100.0, 100.1, 101.0, 103.7, 106.2, 108.1, 108.5),
    "ahc": (90.6, 94.5, 97.0, 99.2, 100.1, 100.1, 101.1, 104.2, 106.7, 108.6, 109.2),
}

PROPERTY_SETTINGS = settings(
    max_examples=25,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow],
)


def line(measure, year):
    return getattr(
        system.parameters(str(year)).household.poverty,
        f"absolute_poverty_threshold_{measure}",
    )


def published_median(measure, year):
    return PUBLISHED_MEDIAN[year][MEASURES.index(measure)]


def monthly_mean(measure, year):
    months = MONTHLY_DEFLATOR[measure][year]
    assert len(months) == 12
    return sum(Decimal(str(month)) for month in months) / 12


def annual_deflator(measure, year):
    """HBAI's annual deflator: the financial-year mean, rounded half up to 1dp."""
    return monthly_mean(measure, year).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)


def deflator_ratio(measure, year):
    return float(annual_deflator(measure, year) / annual_deflator(measure, FYE_2011))


@pytest.mark.parametrize("measure", MEASURES)
@pytest.mark.parametrize("year", YEARS)
def test_line_is_60_percent_of_the_published_median(measure, year):
    expected = Decimal(repr(0.6 * published_median(measure, year))).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )
    assert line(measure, year) == pytest.approx(float(expected), abs=1e-9)


@pytest.mark.parametrize("measure", MEASURES)
def test_annual_deflators_are_rounded_financial_year_means(measure):
    assert [float(annual_deflator(measure, year)) for year in YEARS] == list(
        ANNUAL_DEFLATOR[measure]
    )


@pytest.mark.parametrize("year, rounded", [(2012, "97.0"), (2015, "100.1")])
def test_hbai_rounds_deflator_ties_up(year, rounded):
    # The AHC means for FYE 2013 and FYE 2016 fall exactly on a tie, and HBAI
    # rounds both up: the published medians match 97.0 and 100.1, not 96.9 and
    # 100.0. round() on the float mean gives 100.0 for FYE 2016, hence Decimal.
    mean = monthly_mean("ahc", year)
    assert mean == Decimal(rounded) - Decimal("0.05")
    assert annual_deflator("ahc", year) == Decimal(rounded)


@pytest.mark.parametrize("measure", MEASURES)
@pytest.mark.parametrize("year", YEARS)
def test_published_medians_and_line_follow_the_hbai_deflator(measure, year):
    base = published_median(measure, FYE_2011)
    ratio = deflator_ratio(measure, year)
    # DWP's medians are float32, so they agree to about 7 significant figures.
    assert published_median(measure, year) == pytest.approx(base * ratio, rel=2e-7)
    # The parameter rounds 60% of the median to the penny.
    assert line(measure, year) == pytest.approx(0.6 * base * ratio, abs=0.0051)


@PROPERTY_SETTINGS
@given(
    measure=st.sampled_from(MEASURES),
    years=st.lists(
        st.integers(min_value=FYE_2011, max_value=FYE_2021),
        min_size=2,
        max_size=2,
        unique=True,
    ).map(sorted),
)
@example(measure="ahc", years=[2014, 2015])  # the deflator is flat
@example(measure="bhc", years=[FYE_2011, FYE_2021])
def test_line_moves_with_the_deflator(measure, years):
    earlier, later = years
    deflator_change = annual_deflator(measure, later) - annual_deflator(
        measure, earlier
    )
    line_change = line(measure, later) - line(measure, earlier)
    # Non-decreasing wherever the deflator rises, and flat where it is flat.
    assert np.sign(line_change) == np.sign(deflator_change)


@pytest.mark.parametrize("measure", MEASURES)
def test_line_moves_with_the_deflator_in_every_consecutive_year(measure):
    # Exhaustive over consecutive years; by transitivity, over every pair.
    for earlier, later in itertools.pairwise(YEARS):
        deflator_change = annual_deflator(measure, later) - annual_deflator(
            measure, earlier
        )
        line_change = line(measure, later) - line(measure, earlier)
        assert np.sign(line_change) == np.sign(deflator_change), (earlier, later)


def test_ahc_deflator_is_flat_only_because_hbai_rounds_it():
    # The unrounded AHC mean falls from FYE 2015 to FYE 2016 (100.14 to
    # 100.05); HBAI's rounded deflator, and so the line, is flat.
    assert monthly_mean("ahc", 2015) < monthly_mean("ahc", 2014)
    assert annual_deflator("ahc", 2015) == annual_deflator("ahc", 2014)
    assert line("ahc", 2015) == line("ahc", 2014)


@pytest.mark.parametrize("measure", MEASURES)
def test_every_year_has_its_own_value(measure):
    parameter = getattr(POVERTY, f"absolute_poverty_threshold_{measure}")
    explicit = {value.instant_str for value in parameter.values_list}
    assert {f"{year}-01-01" for year in YEARS} <= explicit
    assert all(line(measure, year) > line(measure, FYE_2011) for year in YEARS[1:])


@pytest.mark.parametrize("measure", MEASURES)
def test_bhc_and_ahc_lines_use_their_own_deflators(measure):
    # HBAI deflates BHC and AHC incomes by different indices, so the two lines
    # grow at different rates (a single index, such as headline CPI, would
    # give both the same growth).
    growth = {m: line(m, FYE_2021) / line(m, FYE_2011) for m in MEASURES}
    # Rounding each line to the penny moves the ratio by up to about 5e-5.
    assert growth[measure] == pytest.approx(deflator_ratio(measure, FYE_2021), abs=1e-4)
    assert growth["bhc"] != pytest.approx(growth["ahc"], abs=1e-3)
