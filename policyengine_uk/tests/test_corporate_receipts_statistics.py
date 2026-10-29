"""Corporate SDLT and business rates statistics: published values and projection.

corporate_sdlt and business_rates allocate these receipts to households by
shareholding. The outturn values are checked against the published figures,
and the projection against the OBR receipts levels it is built from.
"""

import numpy as np
import pandas as pd
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from policyengine_uk import Microsimulation, Simulation, parameters
from policyengine_uk.data import UKSingleYearDataset
from policyengine_uk.scenarios import no_economic_assumptions

SDLT = parameters.gov.hmrc.stamp_duty.statistics
BUSINESS_RATES = parameters.gov.hmrc.business_rates.statistics.revenue
GROWTH = parameters.gov.economic_assumptions.yoy_growth.obr
INSTANT = "{}-01-01".format

# HMRC Annual Stamp Tax Statistics, buyer-type tables, "All price bands" row,
# £m: receipts from individuals (household) and from other buyers (corporate).
# 2019-20 and 2020-21: historic tables 2023 to 2024, Tables 6a/6b; 2021-22 and
# 2022-23: 2023 to 2024 edition, Tables 6a/6b; 2023-24 and 2024-25: 2024 to
# 2025 edition (corrected March 2026), Tables 8a/8b.
SDLT_RECEIPTS_M = {
    ("residential", "corporate"): (885, 705, 1_100, 1_215, 975, 1_230),
    ("residential", "household"): (7_540, 5_310, 9_070, 10_505, 7_595, 9_145),
    ("non_residential", "corporate"): (2_965, 2_425, 3_620, 3_380, 2_810, 3_260),
    ("non_residential", "household"): (210, 230, 310, 260, 230, 245),
}
SDLT_FROM = 2019

# Non-domestic rates, £ (first year in brackets):
# - England local lists: MHCLG NNDR3 non-domestic rating income (2019;
#   2019-20 and 2020-21 from the November 2025 revised data, later years
#   from the 2025-26 release, published in £m to four decimals).
# - England central list: Main Non-Domestic Rating Accounts, amounts received
#   from ratepayers on the central list, published in £ thousand (2019).
# - Scotland: NDRI contributable amount, latest outturn return (2019).
# - Wales local lists: StatsWales contribution to the pool, published in
#   £ thousand (2019); central list: StatsWales total rates received (2019).
#   Values published in pounds and pence are rounded to the pound (half to even).
# - Northern Ireland: LPS non-domestic rates paid (2020).
BUSINESS_RATES_OUTTURN = {
    "ENGLAND": (2019, (25_332_567_663, 13_115_709_138, 20_447_905_400,
                       22_923_982_400, 25_079_394_900, 26_397_345_600,
                       27_591_022_700)),
    "ENGLAND_CENTRAL_LIST": (2019, (1_764_413_000, 1_822_745_000,
                                    1_776_808_000, 1_770_409_000,
                                    1_954_686_000, 2_064_205_000,
                                    2_102_772_000)),
    "SCOTLAND": (2019, (2_752_830_731, 1_816_120_309, 2_108_180_163,
                        2_791_962_750, 3_033_471_284, 3_146_317_233,
                        3_079_138_735)),
    "WALES": (2019, (990_231_844, 952_827_214, 991_820_618, 986_435_966,
                     893_667_788, 980_085_115)),
    "WALES_CENTRAL_LIST": (2019, (100_671_014, 102_668_488, 100_212_013,
                                  101_438_110, 96_926_991, 104_685_854)),
    "NORTHERN_IRELAND": (2020, (380_876_615, 446_688_825, 609_651_544,
                                702_804_905, 741_337_437, 766_153_718)),
}  # fmt: skip

# OBR receipts, £bn, as published: 2023-24 outturn from the March 2025 EFO,
# 2024-25 outturn from the March 2026 EFO, and 2025-26 outturn to 2031-32
# from the October 2026 EFO (receipts Tables 4.7 for SDLT by property type,
# 4.8 for business rates and 4.2 for Northern Ireland business rates; March
# 2026: 3.7, 3.8 and 3.2; March 2025: 3.7, 3.9 and 3.2).
OBR_FROM = 2023
OBR_RECEIPTS_BN = {
    "stamp_duty_land_tax.residential": (
        8.57, 10.38, 11.55444496305409, 11.598497804863152, 12.81121827423391,
        14.275385542155488, 15.523034837312446, 16.708206755202507,
        17.97120998332108,
    ),
    "stamp_duty_land_tax.non_residential": (
        3.045, 3.505, 3.6048001541859174, 3.4392848579522055, 4.060008995487192,
        4.6692547224804075, 4.8746831796154595, 5.306606478148783,
        5.725680069577546,
    ),
    "business_rates.great_britain": (
        29.599814327646055, 32.37681432764605, 33.929814327646056,
        35.43608032863263, 37.21735218338801, 38.66510919685915,
        41.462982206056644, 42.42035811098974, 43.447399285510656,
    ),
    "business_rates.northern_ireland": (
        0.3702940455770644, 0.3823335073068893, 0.3955394050104385,
        0.40595301023058955, 0.414556055466312, 0.4226801104356366,
        0.43095512116333085, 0.4394491849889923, 0.44783993918412923,
    ),
}  # fmt: skip
OBR_LAST_YEAR = OBR_FROM + len(OBR_RECEIPTS_BN["business_rates.great_britain"]) - 1


def _obr(series, year):
    return OBR_RECEIPTS_BN[series][year - OBR_FROM]


def _growth(series):
    node = GROWTH
    for part in series.split("."):
        node = getattr(node, part)
    return node


# Each projected statistic, the OBR series it follows and its last outturn year.
PROJECTED = {
    "residential.corporate": ("stamp_duty_land_tax.residential", 2024),
    "residential.household": ("stamp_duty_land_tax.residential", 2024),
    "non_residential.corporate": ("stamp_duty_land_tax.non_residential", 2024),
    "non_residential.household": ("stamp_duty_land_tax.non_residential", 2024),
    "ENGLAND": ("business_rates.great_britain", 2025),
    "ENGLAND_CENTRAL_LIST": ("business_rates.great_britain", 2025),
    "SCOTLAND": ("business_rates.great_britain", 2025),
    "WALES": ("business_rates.great_britain", 2024),
    "WALES_CENTRAL_LIST": ("business_rates.great_britain", 2024),
    "NORTHERN_IRELAND": ("business_rates.northern_ireland", 2025),
}


def _statistic(name):
    if name in BUSINESS_RATES_OUTTURN:
        return getattr(BUSINESS_RATES, name)
    property_type, buyer = name.split(".")
    return getattr(getattr(SDLT, property_type), buyer).revenue


@pytest.mark.parametrize("key", list(SDLT_RECEIPTS_M))
def test_sdlt_receipts_match_hmrc_tables(key):
    property_type, buyer = key
    revenue = getattr(getattr(SDLT, property_type), buyer).revenue
    for offset, receipts_m in enumerate(SDLT_RECEIPTS_M[key]):
        assert revenue(INSTANT(SDLT_FROM + offset)) == receipts_m * 1e6


@pytest.mark.parametrize("nation", list(BUSINESS_RATES_OUTTURN))
def test_business_rates_match_published_outturn(nation):
    first_year, values = BUSINESS_RATES_OUTTURN[nation]
    for offset, value in enumerate(values):
        assert getattr(BUSINESS_RATES, nation)(INSTANT(first_year + offset)) == value


# LPS rates paid, Northern Ireland, £: total and domestic ("Rates collected by
# District Council and Sector"), 2020-21 to 2025-26.
NI_TOTAL_RATES_PAID = (1_101_723_078, 1_195_019_197, 1_380_794_919,
                       1_540_739_422, 1_630_880_597, 1_714_042_296)  # fmt: skip
NI_DOMESTIC_RATES_PAID = (720_846_463, 748_330_372, 771_143_375, 837_934_517,
                          889_543_160, 947_888_579)  # fmt: skip


@pytest.mark.parametrize("offset", range(len(NI_TOTAL_RATES_PAID)))
def test_northern_ireland_business_rates_are_total_rates_less_domestic(offset):
    # The previous value, £1,334m, was total NI rates (district £590m plus
    # regional £744m, domestic and non-domestic together), so business_rates
    # repeated NI domestic rates, which domestic_rates already charges.
    year = 2020 + offset
    business_rates = BUSINESS_RATES.NORTHERN_IRELAND(INSTANT(year))
    # LPS publishes each column to the pound, so the difference can be £1 off.
    assert business_rates == pytest.approx(
        NI_TOTAL_RATES_PAID[offset] - NI_DOMESTIC_RATES_PAID[offset], abs=1
    )


# OBR's Business rates line (cash basis, £bn): the 2024-25 outturn (March 2026
# EFO, receipts Table 3.8) and the 2025-26 outturn (October 2026 EFO, Table
# 4.8). England, Scotland and Wales, local and central lists together, should
# cover the same receipts.
GB_SERIES = (
    "ENGLAND",
    "ENGLAND_CENTRAL_LIST",
    "SCOTLAND",
    "WALES",
    "WALES_CENTRAL_LIST",
)


@pytest.mark.parametrize("year", [2024, 2025])
def test_great_britain_statistics_cover_the_obr_business_rates_line(year):
    total = sum(getattr(BUSINESS_RATES, n)(INSTANT(year)) for n in GB_SERIES)
    assert total / 1e9 == pytest.approx(
        _obr("business_rates.great_britain", year), rel=0.02
    )


@pytest.mark.parametrize("series", list(OBR_RECEIPTS_BN))
@pytest.mark.parametrize("year", range(OBR_FROM + 1, OBR_LAST_YEAR + 1))
def test_growth_is_the_ratio_of_published_obr_receipts(series, year):
    published = _obr(series, year) / _obr(series, year - 1) - 1
    assert _growth(series)(INSTANT(year)) == pytest.approx(published, abs=5e-7)


@pytest.mark.parametrize("series", list(OBR_RECEIPTS_BN))
@pytest.mark.parametrize("year", range(OBR_LAST_YEAR + 1, 2046))
def test_growth_follows_average_earnings_after_the_obr_forecast(series, year):
    assert _growth(series)(INSTANT(year)) == GROWTH.average_earnings(INSTANT(year))


@pytest.mark.parametrize("name", list(PROJECTED))
def test_projection_tracks_obr_receipts(name):
    series, last_outturn = PROJECTED[name]
    statistic = _statistic(name)
    base = statistic(INSTANT(last_outturn))
    for year in range(last_outturn + 1, OBR_LAST_YEAR + 1):
        expected = base * _obr(series, year) / _obr(series, last_outturn)
        assert statistic(INSTANT(year)) == pytest.approx(expected, rel=2e-5)


# The economic-assumption indices run to 2039, so the projections do too.
LAST_INDEXED_YEAR = 2039


@settings(max_examples=200, deadline=None, derandomize=True)
@given(
    year=st.integers(2025, LAST_INDEXED_YEAR),
    other_year=st.integers(2025, LAST_INDEXED_YEAR),
)
def test_projection_preserves_shares(year, other_year):
    """Uprating scales a whole receipts line, so shares within it never move.

    Each buyer type keeps its 2024-25 share of its property type's SDLT, and
    the England, Scotland and Wales series (local and central lists) keep
    their shares of the Great Britain total from 2025-26 on (the Welsh
    series' 2024-25 outturn is grown by the same index).
    """

    def shares(t):
        out = []
        for property_type in ("residential", "non_residential"):
            node = getattr(SDLT, property_type)
            corporate = node.corporate.revenue(INSTANT(t))
            out.append(corporate / (corporate + node.household.revenue(INSTANT(t))))
        gb = [getattr(BUSINESS_RATES, n)(INSTANT(t)) for n in GB_SERIES]
        out += [value / sum(gb) for value in gb]
        return np.array(out)

    np.testing.assert_allclose(shares(year), shares(other_year), rtol=1e-9)
    np.testing.assert_allclose(shares(year)[:2], shares(2024)[:2], rtol=1e-9)


@pytest.mark.parametrize("name", list(PROJECTED))
def test_projection_is_flat_after_the_last_indexed_year(name):
    statistic = _statistic(name)
    last = statistic(INSTANT(LAST_INDEXED_YEAR))
    assert statistic(INSTANT(LAST_INDEXED_YEAR - 1)) < last
    for year in range(LAST_INDEXED_YEAR + 1, 2050):
        assert statistic(INSTANT(year)) == last


@pytest.mark.parametrize("name", list(PROJECTED))
def test_projection_is_positive_and_finite(name):
    statistic = _statistic(name)
    values = np.array([statistic(INSTANT(year)) for year in range(2019, 2050)])
    assert np.isfinite(values).all() and (values > 0).all()


def _dataset(base_year=2023):
    ids = np.arange(1, 4)
    return UKSingleYearDataset(
        person=pd.DataFrame(
            {
                "person_id": ids,
                "person_benunit_id": ids,
                "person_household_id": ids,
                "age": 40,
            }
        ),
        benunit=pd.DataFrame({"benunit_id": ids}),
        household=pd.DataFrame(
            {
                "household_id": ids,
                "household_weight": [1_000.0, 2_000.0, 500.0],
                "region": ["LONDON", "WALES", "NORTHERN_IRELAND"],
                "tenure_type": "OWNED_OUTRIGHT",
                "rent": 0.0,
                "council_tax": 0.0,
                "domestic_rates": 0.0,
                "corporate_wealth": [10_000.0, 0.0, 50_000.0],
                "private_pension_wealth": [0.0, 20_000.0, 0.0],
            }
        ),
        fiscal_year=base_year,
    )


def _sdlt_statistic(year):
    return sum(
        getattr(SDLT, property_type).corporate.revenue(INSTANT(year))
        for property_type in ("residential", "non_residential")
    )


def _business_rates_statistic(year):
    return sum(
        getattr(BUSINESS_RATES, nation)(INSTANT(year))
        for nation in BUSINESS_RATES_OUTTURN
    )


@pytest.mark.parametrize("year", [2025, 2026, 2030])
def test_microsimulation_allocates_each_statistic_once(year):
    # Variables are float32, so weighted totals match to about 1e-7.
    sim = Microsimulation(dataset=_dataset())
    weights = sim.calculate("household_weight", year).values

    def weighted(variable):
        return float((sim.calculate(variable, year).values * weights).sum())

    sdlt = weighted("corporate_sdlt")
    business_rates = weighted("business_rates")
    assert sdlt == pytest.approx(_sdlt_statistic(year), rel=1e-6)
    assert business_rates == pytest.approx(_business_rates_statistic(year), rel=1e-6)
    assert weighted("baseline_business_rates") == pytest.approx(business_rates)
    assert weighted("corporate_tax_incidence") == pytest.approx(sdlt + business_rates)
    assert weighted("hbai_excluded_income") == pytest.approx(-(sdlt + business_rates))


def test_no_economic_assumptions_holds_statistics_at_latest_outturn():
    # The scenario runs before the dataset loads, so it zeroes growth from the
    # class default input period, not the dataset's year. Every statistic's
    # latest outturn is 2024-25 or 2025-26, so the projection holds at that
    # outturn only while the cutoff is 2025 or earlier.
    assert Simulation.default_input_period <= 2025
    sim = Microsimulation(dataset=_dataset(), scenario=no_economic_assumptions)
    weights = sim.calculate("household_weight", 2030).values

    def weighted(variable):
        return float((sim.calculate(variable, 2030).values * weights).sum())

    latest_business_rates = sum(
        getattr(BUSINESS_RATES, nation)(INSTANT(PROJECTED[nation][1]))
        for nation in BUSINESS_RATES_OUTTURN
    )
    assert weighted("corporate_sdlt") == pytest.approx(_sdlt_statistic(2024), rel=1e-6)
    assert weighted("business_rates") == pytest.approx(latest_business_rates, rel=1e-6)
