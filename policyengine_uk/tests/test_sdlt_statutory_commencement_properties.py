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

HMRC charges SDLT on land in Wales until 1 April 2018 (s48(1)(a) as at 30
April 2017). From then the Welsh Revenue Authority charges Land Transaction
Tax (WSI 2018/128). Each model year reads the parameters in force on 30 April.

Invariants, for any generated households:

1. In every model year from 2015 to 2030, a purchase in Wales is liable to
   exactly one of SDLT and LTT, and the other tax is zero: SDLT up to model
   year 2017, LTT from 2018.
2. In model year 2015, a non-residential purchase priced at or around a Table
   B threshold pays the percentage for its band times the whole price.
3. No transaction tax is ever negative.
4. In model years 2018 to 2030, apart from 2021, 2023 and 2024, SDLT and LTT
   on a grid of purchases equal the values `main` (2da212abc) gave, pinned in
   tests/fixtures/sdlt_ltt_main_grid_2018_2030.csv.
"""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from hypothesis import HealthCheck, example, given, settings
from hypothesis import strategies as st

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


def test_pinned_grid_covers_the_years_2787_leaves_alone(pinned_grid):
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
