"""Published April upratings against September CPI and the model's rates.

Two checks against DWP's published weekly rates (published_benefit_rates):

1. Differential: each April from 2011 to 2026, the published rate of every
   CPI-linked series below equals the previous April's rate raised by the
   model's September CPI rise and rounded to the nearest 5p. The model's
   rise is the one that projects these benefits forward, so this ties the
   model's series to what the Secretary of State actually did in 16 reviews.
2. (PolicyEngine/policyengine-uk#1925's test_dwp_published_rates.py checks
   that the model's parameters hold the published rates.)

Series that the review does not raise by September CPI are checked for the
departure the published rates show instead: amounts derived from another
rate (constant attendance allowance, the couple severe disability premium)
and the 1% rises and freeze of working-age personal allowances.
"""

from decimal import ROUND_HALF_UP, Decimal

import pytest

from policyengine_uk.system import system
from policyengine_uk.tests.published_benefit_rates import PUBLISHED

# Series whose every published April rise is September CPI, rounded to 5p.
SEPTEMBER_CPI_SERIES = [
    "carers_allowance",
    "attendance_allowance_higher",
    "attendance_allowance_lower",
    "dla_care_highest",
    "dla_care_middle",
    "dla_care_lowest",
    "dla_mobility_higher",
    "dla_mobility_lower",
    "pip_daily_living_enhanced",
    "pip_daily_living_standard",
    "pip_mobility_enhanced",
    "pip_mobility_standard",
    "sda_basic",
    "caa_part_time",
    "premium_carer",
    "premium_disability_single",
    "premium_disability_couple",
    "premium_enhanced_single",
    "premium_enhanced_couple",
    "premium_severe_single",
    "pc_severe_disability_single",
    "pc_carer",
]


def rates(series):
    return PUBLISHED[series][1]


def rise(year):
    return system.parameters.gov.economic_assumptions.yoy_growth.september_cpi_uprating(
        f"{year}-01-01"
    )


def to_nearest(amount, step):
    """Round to the nearest multiple of step, halves up, as DWP rounds."""
    step = Decimal(step)
    units = (Decimal(repr(amount)) / step).quantize(Decimal(1), ROUND_HALF_UP)
    return float(units * step)


def uprated(previous, year, step="0.05"):
    return to_nearest(previous * (1 + rise(year)), step)


@pytest.mark.parametrize("series", SEPTEMBER_CPI_SERIES)
def test_published_april_rates_are_the_previous_rate_raised_by_september_cpi(series):
    published = rates(series)
    years = [year for year in sorted(published) if year - 1 in published]
    assert years[0] <= 2014 and years[-1] == 2026
    for year in years:
        assert uprated(published[year - 1], year) == published[year], (series, year)


def test_carers_allowance_from_april_2011():
    """£53.90 (April 2010) to £86.45 (April 2026), all 16 reviews."""
    published = rates("carers_allowance")
    assert min(published) == 2010
    assert len([year for year in published if year > 2010]) == 16


def test_iidb_rises_by_september_cpi_rounded_to_10p():
    published = rates("iidb_100")
    for year in sorted(published)[1:]:
        assert uprated(published[year - 1], year, "0.1") == published[year], year


def test_constant_attendance_allowance_rates_are_multiples_of_the_part_time_rate():
    part_time = rates("caa_part_time")
    for series, multiple in [
        ("caa_normal_maximum", 2),
        ("caa_intermediate", 3),
        ("caa_exceptional", 4),
    ]:
        for year, value in rates(series).items():
            assert value == pytest.approx(multiple * part_time[year]), (series, year)


def test_couple_severe_disability_premium_is_twice_the_single_rate():
    single = rates("premium_severe_single")
    for year, value in rates("premium_severe_couple_higher").items():
        assert value == pytest.approx(2 * single[year]), year


def test_working_age_personal_allowances_show_the_1_percent_years_and_the_freeze():
    """The published rates rise 1% in April 2014 and 2015 (rounded to 5p),
    stay flat in April 2016 to 2019, and follow September CPI otherwise."""
    for series in [
        "is_single_under_25",
        "is_single_25_or_over",
        "is_couple_both_18_or_over",
        "jsa_ib_25_or_over",
    ]:
        published = rates(series)
        for year in sorted(published)[1:]:
            previous = published[year - 1]
            if year in (2014, 2015):
                expected = to_nearest(previous * 1.01, "0.05")
            elif year in (2016, 2017, 2018, 2019):
                expected = previous
            else:
                expected = uprated(previous, year)
            assert published[year] == expected, (series, year)
