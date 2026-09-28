"""The HBAI absolute low-income line uses the FYE 2025 reference year from FYE 2022.

HBAI FYE 2025 (DWP, 26 March 2026) moved the absolute low-income reference
year from FYE 2011 to FYE 2025 for every year with administrative data
linking, currently FYE 2022 onward. The summer 2026 extension back to FYE 2019
was moved to the March 2027 release, so FYE 2021 and earlier keep the FYE 2011
line. policyengine-uk labels FYE 2025 (2024-25) as period 2024.

Invariants:

1. Anchor: at FYE 2025 the lines are 60% of the FYE 2025 medians to the
   penny: HBAI table 2.4ts gives 431.6886 (BHC) and 373.8864 (AHC) a week,
   60% of the unrounded medians in table 2.1ts (the report rounds them to
   719 and 623).
2. Back-cast: for FYE 2022 to FYE 2024 each line equals the FYE 2025 line
   times the ratio of financial-year averages of HBAI's deflator (BHC: ONS
   experimental CPI including mortgage interest payments, ground rent and
   dwelling insurance; AHC: CPI excluding rents, maintenance repairs and
   water charges; ONS ad hoc 2863), to the penny. The monthly indices are
   transcribed from the ONS workbook. As an independent check on that
   transcription and on the choice of series, the BHC deflator's year-on-year
   growth matches the deflator DWP used, backed out of HBAI table 1.2a (mean
   income growth in cash and in real terms), to within 0.05 percentage
   points, which headline CPI does not.
3. Switch year: FYE 2022 (period 2021) is the first year on the FYE 2025
   reference; FYE 2021 (period 2020) and earlier keep the FYE 2011 line.
4. Forward uprating: for every year from FYE 2025, both lines move with OBR
   CPI, so the AHC/BHC ratio stays at its FYE 2025 value.
5. The AHC line is below the BHC line in every year, and both are positive.
6. Variable layer: poverty_threshold_* is the weekly line times 52, and the
   absolute poverty flags hold exactly when equivalised income is below it.
"""

from statistics import fmean

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation
from policyengine_uk.system import system

POVERTY = system.parameters.household.poverty
CPI = system.parameters.gov.economic_assumptions.indices.obr.consumer_price_index

# HBAI FYE 2025 population medians, pounds a week in 2024/25 prices, from
# data table 2.1ts; the main report rounds them to 719 (BHC) and 623 (AHC).
MEDIAN_FYE_2025 = {"bhc": 719.4810615125072, "ahc": 623.1440591131203}
# 60% of median for the reference couple, table 2.4ts.
LINE_TABLE_2_4TS = {"bhc": 431.6886369075043, "ahc": 373.88643546787216}
FYE_2025 = 2024
FIRST_REBASED_YEAR = 2021  # FYE 2022

# Monthly indices (2015 = 100), April to March of each financial year, from
# ONS ad hoc 2863 (released 5 June 2025): sheet 1b is the BHC deflator and
# sheet 1a the AHC deflator.
DEFLATOR = {
    "bhc": {
        2021: (110.0, 110.6, 111.2, 111.2, 111.9, 112.2)
        + (113.4, 114.2, 114.9, 114.8, 115.8, 117.0),
        2022: (119.9, 120.7, 121.7, 122.6, 123.2, 123.9)
        + (126.4, 127.0, 127.6, 127.1, 128.7, 129.7),
        2023: (131.4, 132.3, 132.6, 132.2, 132.8, 133.5)
        + (133.6, 133.4, 134.0, 133.4, 134.2, 135.1),
        2024: (135.6, 136.1, 136.3, 136.1, 136.6, 136.6)
        + (137.4, 137.5, 138.0, 137.9, 138.5, 139.0),
    },
    "ahc": {
        2021: (110.5, 111.2, 111.8, 111.7, 112.6, 112.9)
        + (114.3, 115.2, 115.8, 115.6, 116.6, 118.0),
        2022: (121.2, 122.0, 123.1, 123.8, 124.5, 125.1)
        + (127.8, 128.3, 128.8, 127.9, 129.5, 130.6),
        2023: (132.1, 133.0, 133.2, 132.3, 132.8, 133.5)
        + (133.4, 133.0, 133.6, 133.1, 133.9, 134.7),
        2024: (134.7, 135.1, 135.2, 134.6, 134.9, 135.0)
        + (135.9, 136.0, 136.4, 136.2, 136.8, 137.3),
    },
}

# The FYE 2011 line as policyengine-uk has carried it (60% of the FYE 2011
# medians of 419 and 359 a week, and its FYE 2021 value).
FYE_2011_LINE = {
    "bhc": {2010: 251.4, 2020: 305.7},
    "ahc": {2010: 215.4, 2020: 261.92},
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


@pytest.mark.parametrize("measure", ["bhc", "ahc"])
def test_fye_2025_line_is_60_percent_of_the_published_median(measure):
    # Transcription check on the constants above: table 2.4ts is 60% of the
    # table 2.1ts median.
    assert LINE_TABLE_2_4TS[measure] == pytest.approx(
        0.6 * MEDIAN_FYE_2025[measure], rel=1e-12
    )
    # The model's line is the table 2.4ts value to the penny.
    assert line(measure, FYE_2025) == pytest.approx(
        round(LINE_TABLE_2_4TS[measure], 2), abs=1e-9
    )


def test_ahc_and_bhc_lines_come_from_the_same_publication():
    assert line("bhc", FYE_2025) == pytest.approx(431.69, abs=1e-9)
    assert line("ahc", FYE_2025) == pytest.approx(373.89, abs=1e-9)
    # Not the lines implied by the report's rounded medians (719, 623).
    assert line("bhc", FYE_2025) != pytest.approx(0.6 * 719, abs=0.05)
    assert line("ahc", FYE_2025) != pytest.approx(0.6 * 623, abs=0.05)
    assert line("ahc", FYE_2025) / line("bhc", FYE_2025) == pytest.approx(
        MEDIAN_FYE_2025["ahc"] / MEDIAN_FYE_2025["bhc"], rel=1e-4
    )


@pytest.mark.parametrize("measure", ["bhc", "ahc"])
@pytest.mark.parametrize("year", [2021, 2022, 2023])
def test_back_cast_matches_hbai_deflators(measure, year):
    deflator = DEFLATOR[measure]
    for months in deflator.values():
        assert len(months) == 12
    expected = (
        LINE_TABLE_2_4TS[measure] * fmean(deflator[year]) / fmean(deflator[FYE_2025])
    )
    assert line(measure, year) == pytest.approx(round(expected, 2), abs=1e-9)


# HBAI table 1.2a, mean net disposable unequivalised income growth (BHC),
# percent, in cash terms and in real terms; the ratio is DWP's BHC deflator.
# FYE 2022 is omitted: it straddles the series break, and FYE 2021 used an
# earlier deflator vintage.
HBAI_TABLE_1_2A = {
    2022: {"cash": 9.26741118619525, "real": -1.0556909114590507},
    2023: {"cash": 4.927077630138066, "real": -1.611171201169781},
    2024: {"cash": 6.289097504035901, "real": 3.265556437181605},
}
HEADLINE_CPI_FYE_2025 = 2.360610087969106  # table 1.2a, CPI inflation


@pytest.mark.parametrize("year", sorted(HBAI_TABLE_1_2A))
def test_bhc_deflator_matches_the_one_dwp_used(year):
    row = HBAI_TABLE_1_2A[year]
    dwp_growth = 100 * ((1 + row["cash"] / 100) / (1 + row["real"] / 100) - 1)
    ours = 100 * (fmean(DEFLATOR["bhc"][year]) / fmean(DEFLATOR["bhc"][year - 1]) - 1)
    assert ours == pytest.approx(dwp_growth, abs=0.05)
    # The parameters carry the same growth between consecutive years.
    assert 100 * (line("bhc", year) / line("bhc", year - 1) - 1) == pytest.approx(
        dwp_growth, abs=0.05
    )


def test_headline_cpi_would_not_match_the_bhc_deflator():
    row = HBAI_TABLE_1_2A[FYE_2025]
    dwp_growth = 100 * ((1 + row["cash"] / 100) / (1 + row["real"] / 100) - 1)
    assert abs(HEADLINE_CPI_FYE_2025 - dwp_growth) > 0.5


@pytest.mark.parametrize("measure", ["bhc", "ahc"])
def test_switch_year_is_fye_2022(measure):
    old = FYE_2011_LINE[measure]
    # FYE 2021 and earlier keep the FYE 2011 line.
    assert line(measure, 2010) == pytest.approx(old[2010], abs=1e-9)
    assert line(measure, 2020) == pytest.approx(old[2020], abs=1e-9)
    # FYE 2022 is the first rebased year: well above the FYE 2011 line
    # carried forward by a year of CPI.
    carried = old[2020] * CPI(str(FIRST_REBASED_YEAR)) / CPI("2020")
    assert line(measure, FIRST_REBASED_YEAR) > 1.1 * carried
    # And it is the back-cast of the FYE 2025 line, not the FYE 2011 one.
    back_cast = (
        LINE_TABLE_2_4TS[measure]
        * fmean(DEFLATOR[measure][FIRST_REBASED_YEAR])
        / fmean(DEFLATOR[measure][FYE_2025])
    )
    assert line(measure, FIRST_REBASED_YEAR) == pytest.approx(
        round(back_cast, 2), abs=1e-9
    )


@PROPERTY_SETTINGS
@given(year=st.integers(min_value=FYE_2025, max_value=2040))
def test_lines_uprate_with_cpi_from_fye_2025(year):
    growth = CPI(str(year)) / CPI(str(FYE_2025))
    for measure in ("bhc", "ahc"):
        assert line(measure, year) == pytest.approx(
            line(measure, FYE_2025) * growth, rel=1e-9
        )
    assert line("ahc", year) / line("bhc", year) == pytest.approx(
        line("ahc", FYE_2025) / line("bhc", FYE_2025), rel=1e-9
    )


@PROPERTY_SETTINGS
@given(year=st.integers(min_value=2010, max_value=2040))
def test_ahc_line_is_positive_and_below_bhc_line(year):
    assert 0 < line("ahc", year) < line("bhc", year)


@PROPERTY_SETTINGS
@given(
    year=st.sampled_from([2020, 2021, 2024, 2026]),
    earnings=st.lists(
        st.floats(min_value=0, max_value=60_000, allow_nan=False),
        min_size=1,
        max_size=8,
    ),
)
def test_absolute_poverty_flags_follow_the_line(year, earnings):
    period = str(year)
    people = {
        f"p{i}": {"age": {period: 40}, "employment_income": {period: e}}
        for i, e in enumerate(earnings)
    }
    households = {
        f"h{i}": {
            "members": [f"p{i}"],
            "rent": {period: 0},
            "council_tax": {period: 0},
        }
        for i in range(len(earnings))
    }
    benunits = {f"b{i}": {"members": [f"p{i}"]} for i in range(len(earnings))}
    sim = Simulation(
        situation={
            "people": people,
            "benunits": benunits,
            "households": households,
        }
    )
    for measure, income_variable in (
        ("bhc", "equiv_hbai_household_net_income"),
        ("ahc", "equiv_hbai_household_net_income_ahc"),
    ):
        threshold = sim.calculate(f"poverty_threshold_{measure}", year)
        assert threshold == pytest.approx(line(measure, year) * 52, rel=1e-6)
        income = sim.calculate(income_variable, year)
        flags = sim.calculate(f"in_poverty_{measure}", year)
        assert list(flags) == list(income < threshold)
