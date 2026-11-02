"""Property-based tests for the dates SDLT's 2016 and 2017 changes start on
(issue #2801).

Parliament set these starts:

- Finance Act 2018 s41(8): first-time buyers' relief (Sch 6ZA) from 22
  November 2017.
- Finance Act 2016 s128(5): the higher rates for additional dwellings (Sch
  4ZA) from 1 April 2016. Before then a buyer of an additional dwelling paid
  the main rates in Finance Act 2003 s55(1B) Table A.
- Finance Act 2016 s127(12): the sliced non-residential rates and the 2% lease
  rent band above £5,000,000 from 17 March 2016. Before then HMRC charged a
  non-residential purchase "the percentage of the chargeable consideration for
  the transaction determined in accordance with Table B" (s55(2) as at 30
  April 2015): 0% up to £150,000, 1% above £150,000 up to £250,000, 3% above
  £250,000 up to £500,000 and 4% above £500,000.

HMRC charged SDLT on land in Wales until 31 March 2018 (s48(1)(a) as at 30
April 2017). Parliament ended SDLT in Wales from 1 April 2018 (Wales Act 2014
s16(2), (4); SI 2018/214 art 2(a)), and the Welsh Revenue Authority charges
Land Transaction Tax from then (LTTADT(W)A 2017 s2; WSI 2018/34 art 3); the
Welsh Ministers set LTT's rates in WSI 2018/128. Each model year reads the
parameters in force on 30 April.

Invariants, for any generated households or dates:

1. In every model year from 2015 to 2030, a purchase in Wales is liable to
   exactly one of SDLT and LTT, and the other tax is zero: SDLT up to model
   year 2017, LTT from 2018.
2. In model year 2015, a non-residential purchase priced at or around a Table
   B threshold pays the percentage for its band times the whole price.
3. No transaction tax is ever negative.
4. In model years 2018 to 2030, apart from 2021, 2023 and 2024, SDLT and LTT
   on a grid of purchases equal the values `main` (2da212abc) gave, pinned in
   tests/fixtures/sdlt_ltt_main_grid_2018_2030.csv.
5. On any date from 1 January 2015, the raw dated parameters hold the
   statutory switches and tables: SDLT applies in Wales before 1 April 2018;
   HMRC charges a non-residential purchase on the whole price at Table B's
   rates before 17 March 2016 and on slices at 0%, 2% and 5% from then; the
   non-residential lease rent table adds a 2% band above £5,000,000 from 17
   March 2016.
6. Before 1 April 2016 a buyer of an additional dwelling pays what a buyer of
   a main home pays, at every price, on the raw dated parameters and in model
   year 2015.
7. Before 22 November 2017 a first-time buyer pays what any other buyer pays,
   at every price, on the raw dated parameters and in model years 2015 to
   2017.
8. In every model year from 2015 to 2030, SDLT on a non-residential purchase
   never falls as the price rises, on the whole-price path and the sliced
   path.
"""

from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from hypothesis import HealthCheck, example, given, settings
from hypothesis import strategies as st

from policyengine_core.parameters import ParameterNode

import policyengine_uk
from policyengine_uk import Simulation

PROPERTY_SETTINGS = settings(
    max_examples=15,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)
YEARS = list(range(2015, 2031))
LTT_FIRST_YEAR = 2018
REGIONS = ["LONDON", "NORTH_EAST", "WALES", "SCOTLAND", "NORTHERN_IRELAND"]
TAXES = [
    "stamp_duty_land_tax",
    "sdlt_on_residential_property_transactions",
    "sdlt_on_non_residential_property_transactions",
    "sdlt_on_residential_property_rent",
    "sdlt_on_non_residential_property_rent",
    "land_transaction_tax",
    "land_and_buildings_transaction_tax",
]
# Table B in s55(2) as at 30 April 2015: each band covers prices that exceed
# its threshold and do not exceed the next one.
TABLE_B = ((0, 0.0), (150_000, 0.01), (250_000, 0.03), (500_000, 0.04))
TABLE_B_YEAR = 2015
GRID_PATH = Path(__file__).parent / "fixtures" / "sdlt_ltt_main_grid_2018_2030.csv"

purchase_strategy = st.fixed_dictionaries(
    {
        "main_residential_property_purchased": st.integers(0, 3_000_000),
        "main_residential_property_purchased_is_first_home": st.booleans(),
        "additional_residential_property_purchased": st.integers(0, 3_000_000),
        "non_residential_property_purchased": st.integers(0, 3_000_000),
        "rent": st.integers(0, 2_000_000),
        "cumulative_residential_rent": st.integers(0, 2_000_000),
        "non_residential_rent": st.integers(0, 8_000_000),
        "cumulative_non_residential_rent": st.integers(0, 8_000_000),
    }
)


def _situation(households, years):
    situation = {"people": {}, "benunits": {}, "households": {}}
    for i, household in enumerate(households):
        person = f"p{i}"
        situation["people"][person] = {"age": {year: 40 for year in years}}
        situation["benunits"][f"b{i}"] = {"members": [person]}
        situation["households"][f"h{i}"] = {
            "members": [person],
            **{
                key: {year: value for year in years} for key, value in household.items()
            },
        }
    return situation


def _calculate(simulation, variable, year):
    return np.array(simulation.calculate(variable, year), dtype=float)


@PROPERTY_SETTINGS
@given(st.lists(purchase_strategy, min_size=1, max_size=6))
@example(
    [
        {
            "main_residential_property_purchased": 300_000,
            "main_residential_property_purchased_is_first_home": False,
            "additional_residential_property_purchased": 300_000,
            "non_residential_property_purchased": 1_000_000,
            "rent": 0,
            "cumulative_residential_rent": 0,
            "non_residential_rent": 0,
            "cumulative_non_residential_rent": 0,
        }
    ]
)
def test_wales_pays_exactly_one_of_sdlt_and_ltt(purchases):
    households = [{"region": "WALES", **purchase} for purchase in purchases]
    simulation = Simulation(situation=_situation(households, YEARS))
    for year in YEARS:
        sdlt_liable = np.array(simulation.calculate("sdlt_liable", year), dtype=bool)
        ltt_liable = np.array(simulation.calculate("ltt_liable", year), dtype=bool)
        assert np.all(sdlt_liable != ltt_liable), year
        assert np.all(ltt_liable == (year >= LTT_FIRST_YEAR)), year
        sdlt = _calculate(simulation, "stamp_duty_land_tax", year)
        ltt = _calculate(simulation, "land_transaction_tax", year)
        np.testing.assert_array_equal(sdlt[~sdlt_liable], 0, err_msg=str(year))
        np.testing.assert_array_equal(ltt[~ltt_liable], 0, err_msg=str(year))
        # A £1,000,000 purchase in any of these forms pays the liable tax.
        large = np.array(
            [
                max(
                    p["main_residential_property_purchased"],
                    p["additional_residential_property_purchased"],
                    p["non_residential_property_purchased"],
                )
                >= 1_000_000
                for p in purchases
            ]
        )
        assert np.all(np.where(sdlt_liable, sdlt, ltt)[large] > 0), year


def _table_b_tax(price):
    rate = [rate for threshold, rate in TABLE_B if price > threshold or threshold == 0]
    return rate[-1] * price


threshold_prices = st.sampled_from(
    [
        threshold + offset
        for threshold, _ in TABLE_B
        for offset in (-100, -1, -0.5, 0, 0.5, 1, 100)
        if threshold + offset >= 0
    ]
)
table_b_prices = st.one_of(threshold_prices, st.integers(0, 3_000_000))


@PROPERTY_SETTINGS
@given(st.lists(table_b_prices, min_size=1, max_size=40))
@example([150_000, 150_000.5, 250_000, 250_000.5, 500_000, 500_000.5, 1_000_000])
def test_table_b_charges_the_whole_price_in_2015(prices):
    # Prices are whole pounds or halves, which float32 stores exactly.
    households = [
        {"region": "LONDON", "non_residential_property_purchased": price}
        for price in prices
    ]
    simulation = Simulation(situation=_situation(households, [TABLE_B_YEAR]))
    tax = _calculate(simulation, "stamp_duty_land_tax", TABLE_B_YEAR)
    expected = [_table_b_tax(price) for price in prices]
    np.testing.assert_allclose(tax, expected, rtol=1e-6, atol=0.01)


def _whole_price_tax(table, price):
    # The rate for the highest band whose threshold the price exceeds, on the
    # whole price, or nothing when the price exceeds no threshold.
    rates = [rate for threshold, rate in table if price > threshold]
    return rates[-1] * price if rates else 0.0


NON_RESIDENTIAL_FIRST_BAND = "gov.hmrc.stamp_duty.non_residential.purchase[0]"


@settings(PROPERTY_SETTINGS, max_examples=10)
@example(10_000, 0.005, [0, 5_000, 9_999.5, 10_000, 10_000.5, 20_000, 150_000.5])
@given(
    st.integers(1, 149_999),
    st.sampled_from([0.001, 0.005, 0.0075]),
    st.lists(
        st.one_of(threshold_prices, st.integers(0, 3_000_000)), min_size=1, max_size=20
    ),
)
def test_reformed_first_threshold_charges_the_whole_price_above_it(
    threshold, rate, prices
):
    # A reform gives Table B's first band a positive threshold and rate in
    # model year 2015. A price that exceeds no threshold pays nothing, and a
    # price above the first threshold pays its band's rate on the whole price.
    table = ((threshold, rate),) + TABLE_B[1:]
    prices = prices + [threshold, threshold + 0.5, threshold + 1]
    households = [
        {"region": "LONDON", "non_residential_property_purchased": price}
        for price in prices
    ]
    period = f"{TABLE_B_YEAR}-01-01.{TABLE_B_YEAR}-12-31"
    reform = {
        f"{NON_RESIDENTIAL_FIRST_BAND}.threshold": {period: threshold},
        f"{NON_RESIDENTIAL_FIRST_BAND}.rate": {period: rate},
    }
    simulation = Simulation(
        situation=_situation(households, [TABLE_B_YEAR]), reform=reform
    )
    tax = _calculate(simulation, "stamp_duty_land_tax", TABLE_B_YEAR)
    expected = [_whole_price_tax(table, price) for price in prices]
    np.testing.assert_allclose(tax, expected, rtol=1e-6, atol=0.01, err_msg=str(table))


@settings(PROPERTY_SETTINGS, max_examples=6)
@given(
    st.lists(
        st.tuples(st.sampled_from(REGIONS), purchase_strategy),
        min_size=4,
        max_size=12,
    )
)
def test_transaction_taxes_are_never_negative(households):
    households = [{"region": region, **purchase} for region, purchase in households]
    simulation = Simulation(situation=_situation(households, YEARS))
    for year in YEARS:
        for tax in TAXES:
            assert np.all(_calculate(simulation, tax, year) >= 0), (tax, year)


GRID_INPUTS = {
    "main": ("main_residential_property_purchased",),
    "first": ("main_residential_property_purchased",),
    "additional": ("additional_residential_property_purchased",),
    "non_residential": ("non_residential_property_purchased",),
    "residential_lease": ("rent",),
    "non_residential_lease": ("non_residential_rent",),
    "non_residential_lease_above_5m": ("non_residential_rent",),
}
ZERO_INPUTS = (
    "main_residential_property_purchased",
    "additional_residential_property_purchased",
    "non_residential_property_purchased",
    "rent",
    "cumulative_residential_rent",
    "non_residential_rent",
    "cumulative_non_residential_rent",
)


def _grid_household(row):
    household = {variable: 0 for variable in ZERO_INPUTS}
    household["region"] = row.region
    household["main_residential_property_purchased_is_first_home"] = row.kind == "first"
    for variable in GRID_INPUTS[row.kind]:
        household[variable] = row.price
    if row.kind == "non_residential_lease_above_5m":
        household["cumulative_non_residential_rent"] = 5_000_000
    return household


@pytest.fixture(scope="module")
def pinned_grid():
    grid = pd.read_csv(GRID_PATH)
    years = sorted({int(column.split("_")[-1]) for column in grid.columns[3:]})
    households = [_grid_household(row) for row in grid.itertuples()]
    return grid, years, Simulation(situation=_situation(households, years))


def test_pinned_grid_leaves_out_2021_2023_and_2024(pinned_grid):
    _, years, _ = pinned_grid
    assert years == [y for y in range(2018, 2031) if y not in (2021, 2023, 2024)]


@pytest.mark.parametrize(
    "year", [y for y in range(2018, 2031) if y not in (2021, 2023, 2024)]
)
def test_model_years_from_2018_match_main(pinned_grid, year):
    grid, _, simulation = pinned_grid
    for tax, column in (
        ("stamp_duty_land_tax", "sdlt"),
        ("land_transaction_tax", "ltt"),
    ):
        np.testing.assert_allclose(
            _calculate(simulation, tax, year),
            grid[f"{column}_{year}"],
            rtol=0,
            atol=0.01,
            err_msg=f"{tax} {year}",
        )


# Invariant 5: the raw dated switches and tables.

RAW = ParameterNode(
    "stamp_duty",
    directory_path=str(
        Path(policyengine_uk.__file__).parent / "parameters/gov/hmrc/stamp_duty"
    ),
)
WALES_SDLT_ENDS = date(2018, 4, 1)  # SI 2018/214 art 2(a)
SLICED_RATES_START = date(2016, 3, 17)  # FA 2016 s127(12)
HIGHER_RATES_START = date(2016, 4, 1)  # FA 2016 s128(5)
RELIEF_START = date(2017, 11, 22)  # FA 2018 s41(8)
# FA 2003 s55(2) Table B as amended by FA 2016 s127, and Sch 5 para 2(3)
# Table B before and after it.
SLICED_RATES = ((0, 0.0), (150_000, 0.02), (250_000, 0.05))
RENT_BEFORE = ((0, 0.0), (150_000, 0.01))
RENT_FROM = ((0, 0.0), (150_000, 0.01), (5_000_000, 0.02))
STATUTORY_DATES = (WALES_SDLT_ENDS, SLICED_RATES_START, HIGHER_RATES_START)
STATUTORY_DATES += (RELIEF_START,)
RAW_DAYS = sorted({d + timedelta(days=k) for d in STATUTORY_DATES for k in (-1, 0)})
raw_dates = st.one_of(
    st.dates(min_value=date(2015, 1, 1), max_value=date(2035, 12, 31)),
    st.sampled_from(RAW_DAYS),
)


def _bands(scale):
    return tuple(zip(map(float, scale.thresholds), map(float, scale.rates)))


def _check_raw_switches(effective_date):
    stamp_duty = RAW(effective_date.isoformat())
    non_residential = stamp_duty.non_residential
    before_sliced_rates = effective_date < SLICED_RATES_START
    assert bool(stamp_duty.applies_in_wales) == (effective_date < WALES_SDLT_ENDS)
    assert bool(non_residential.purchase_charged_on_whole_price) == before_sliced_rates
    assert _bands(non_residential.purchase) == (
        TABLE_B if before_sliced_rates else SLICED_RATES
    )
    assert _bands(non_residential.rent) == (
        RENT_BEFORE if before_sliced_rates else RENT_FROM
    )
    purchase = stamp_duty.residential.purchase
    assert bool(purchase.additional.higher_rates_apply) == (
        effective_date >= HIGHER_RATES_START
    )
    # first.max holds 0 from 8 July 2020 to 30 June 2021, which
    # test_sdlt_dated_schedule_properties.py checks in
    # test_omitted_relief_ignores_buyer_status_under_any_rates.
    if effective_date < date(2020, 7, 8):
        assert (purchase.main.first.max > 0) == (effective_date >= RELIEF_START)


@pytest.mark.parametrize("effective_date", RAW_DAYS, ids=str)
def test_raw_switches_change_on_their_statutory_dates(effective_date):
    _check_raw_switches(effective_date)


@settings(PROPERTY_SETTINGS, max_examples=60)
@given(raw_dates)
def test_raw_switches_hold_on_any_date(effective_date):
    _check_raw_switches(effective_date)


# Invariants 6 and 7: before a surcharge or relief starts, the buyer pays the
# main rates.

residential_prices = st.one_of(
    st.integers(0, 300_000_000).map(lambda pence: pence / 100),
    st.sampled_from(
        [
            b + k
            for b in (40_000, 125_000, 250_000, 300_000, 500_000, 925_000, 1_500_000)
            for k in (-1, 0, 1)
        ]
    ),
)


def _residential_tax(purchase, price, buyer):
    # The schedule sdlt_on_residential_property_transactions applies.
    main_rates_tax = purchase.main.subsequent.calc(price)
    if buyer == "first" and purchase.main.first.max > 0:
        return np.where(
            price <= purchase.main.first.max,
            purchase.main.first.rate.calc(price),
            main_rates_tax,
        )
    if buyer == "additional" and purchase.additional.higher_rates_apply:
        chargeable = np.where(price < purchase.additional.min, 0, price)
        return purchase.additional.rate.calc(chargeable)
    return main_rates_tax


@settings(PROPERTY_SETTINGS, max_examples=60)
@example(HIGHER_RATES_START - timedelta(days=1), [40_000, 300_000, 1_000_000])
@example(RELIEF_START - timedelta(days=1), [200_000, 300_000, 500_000])
@given(
    st.dates(min_value=date(2014, 12, 4), max_value=RELIEF_START - timedelta(days=1)),
    st.lists(residential_prices, min_size=1, max_size=8),
)
def test_raw_buyers_pay_the_main_rates_before_their_schedules_start(
    effective_date, price_list
):
    purchase = RAW(effective_date.isoformat()).residential.purchase
    price = np.array(price_list, dtype=float)
    main = _residential_tax(purchase, price, "main")
    np.testing.assert_array_equal(_residential_tax(purchase, price, "first"), main)
    if effective_date < HIGHER_RATES_START:
        np.testing.assert_array_equal(
            _residential_tax(purchase, price, "additional"), main
        )


@settings(PROPERTY_SETTINGS, max_examples=10)
@example([0, 40_000, 125_000, 200_000, 300_000, 500_000, 1_000_000, 1_600_000])
@given(st.lists(residential_prices, min_size=1, max_size=10))
def test_model_years_before_the_schedules_charge_the_main_rates(price_list):
    years = [2015, 2016, 2017]
    households = []
    for price in price_list:
        for buyer in ("main", "first", "additional"):
            households.append(
                {
                    "region": "LONDON",
                    "main_residential_property_purchased": (
                        0 if buyer == "additional" else price
                    ),
                    "main_residential_property_purchased_is_first_home": (
                        buyer == "first"
                    ),
                    "additional_residential_property_purchased": (
                        price if buyer == "additional" else 0
                    ),
                }
            )
    simulation = Simulation(situation=_situation(households, years))
    for year in years:
        tax = _calculate(simulation, "stamp_duty_land_tax", year).reshape(-1, 3)
        main, first, additional = tax.T
        np.testing.assert_array_equal(first, main, err_msg=str(year))
        if year == 2015:
            np.testing.assert_array_equal(additional, main, err_msg=str(year))


# Invariant 8: non-residential SDLT never falls as the price rises.

non_residential_prices = st.one_of(
    st.integers(0, 300_000_000).map(lambda pence: pence / 100),
    st.sampled_from(
        [b + k for b, _ in TABLE_B for k in (-1, -0.5, 0, 0.5, 1) if b + k >= 0]
    ),
)


@settings(PROPERTY_SETTINGS, max_examples=10)
@example([0, 150_000, 150_000.5, 250_000, 250_000.5, 500_000, 500_000.5])
@given(st.lists(non_residential_prices, min_size=2, max_size=20))
def test_non_residential_tax_never_falls_as_the_price_rises(price_list):
    prices = sorted(price_list)
    households = [
        {"region": "LONDON", "non_residential_property_purchased": price}
        for price in prices
    ]
    simulation = Simulation(situation=_situation(households, YEARS))
    for year in YEARS:
        tax = _calculate(
            simulation, "sdlt_on_non_residential_property_transactions", year
        )
        assert np.all(np.diff(tax) >= -1e-6), (year, prices, tax)
