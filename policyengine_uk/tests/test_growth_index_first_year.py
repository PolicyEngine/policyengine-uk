"""Growth indices include their first listed year's growth (#2692).

The index generator puts an index of 1 in a series' first listed year and
multiplies growth only from the next year, so the first listed growth was
never in the index. Each series below sets ``index_base_year`` to the year
before, so the index is 1 there and its first step is that growth. Only a
direct input dated before the first growth year read the dropped step;
dataset projection reads ``yoy_growth`` directly.
"""

import pytest

from policyengine_uk import parameters

YOY = "gov.economic_assumptions.yoy_growth."
INDICES = "gov.economic_assumptions.indices."

# Series and their first listed growth year, from the #2692 table.
FIRST_GROWTH_YEAR = {
    "obr.per_capita.gdp": 2021,
    "obr.per_capita.mixed_income": 2021,
    "obr.house_prices": 2021,
    "obr.mortgage_interest": 2021,
    "obr.petrol_spending_litre_proxy": 2021,
    "obr.diesel_spending_litre_proxy": 2021,
    "orr.per_capita.rail_passenger_journeys": 2021,
    "ons.population": 2021,
    # Generated: min(RPI in the previous year, 5%) from 2020.
    "obr.private_pension_index": 2020,
    # Generated: the previous year's earnings growth from 2022.
    "obr.lagged_average_earnings": 2022,
}

# Index levels are rounded to 5 decimal places as they cumulate, so a ratio
# of two levels matches the growth only to about 1e-5.
ROUNDING = 2e-5


def growth(series, year):
    return parameters.get_child(YOY + series)(f"{year}-01-01")


def index(series, year):
    return parameters.get_child(INDICES + series)(f"{year}-01-01")


@pytest.mark.parametrize("series", FIRST_GROWTH_YEAR)
def test_index_includes_the_first_growth_year(series):
    # For example rail: 2021 / 2020 = 2.5433, not 1.
    first = FIRST_GROWTH_YEAR[series]
    assert index(series, first - 1) == 1
    assert growth(series, first) != 0
    assert index(series, first) / index(series, first - 1) == pytest.approx(
        1 + growth(series, first), rel=ROUNDING
    )


@pytest.mark.parametrize("series", FIRST_GROWTH_YEAR)
def test_index_is_flat_before_its_base_year(series):
    # Backdating carries the base year's 1 back, so no growth is invented
    # before the first listed year.
    first = FIRST_GROWTH_YEAR[series]
    for year in range(2015, first):
        assert index(series, year) == 1


@pytest.mark.parametrize("series", FIRST_GROWTH_YEAR)
def test_later_steps_still_follow_their_growth(series):
    first = FIRST_GROWTH_YEAR[series]
    for year in range(first + 1, 2040):
        assert index(series, year) / index(series, year - 1) == pytest.approx(
            1 + growth(series, year), rel=ROUNDING
        ), year


def test_capital_gains_index_still_copies_gdp_per_person():
    # capital_gains_projection.py copies the per-person GDP index exactly.
    for year in range(2015, 2040):
        assert index("capital_gains", year) == index("obr.per_capita.gdp", year)


def test_direct_rail_input_dated_2020_grows_by_the_2021_step():
    # A 2020 input queried for 2021 is carried forward by the index ratio.
    # Before #2692 the 2020 and 2021 levels were both 1, so it stayed at
    # 100 rather than 100 x 2.5433.
    from policyengine_uk import Simulation

    simulation = Simulation(
        situation={
            "people": {"adult": {"age": {2020: 40, 2021: 41}}},
            "benunits": {"benunit": {"members": ["adult"]}},
            "households": {
                "household": {
                    "members": ["adult"],
                    "rail_usage": {2020: 100.0},
                }
            },
        }
    )
    assert float(simulation.calculate("rail_usage", 2021)[0]) == pytest.approx(
        254.33, abs=0.01
    )
