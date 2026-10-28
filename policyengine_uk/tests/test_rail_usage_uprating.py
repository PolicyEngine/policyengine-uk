"""Rail usage is projected by ORR passenger journeys per person (#1862).

ORR Table 1220 (published 18 June 2026) gives passenger journeys on Great
Britain's railways in millions, by financial year. gov.dft.rail.ridership_index
divides them by the 2020-21 figure. No official body forecasts journeys, so
from 2026-27 they are held flat.

Household weights grow by ons.population, so each household's rail_usage
grows by journeys growth net of population growth. Growing it by journeys
growth itself would count population growth twice.
"""

import numpy as np
import pandas as pd
import pytest

from policyengine_uk import parameters
from policyengine_uk.data import UKSingleYearDataset
from policyengine_uk.data.economic_assumptions import (
    PROJECTION_END_YEAR,
    extend_single_year_dataset,
)

RIDERSHIP = parameters.gov.dft.rail.ridership_index
POPULATION = parameters.gov.economic_assumptions.yoy_growth.ons.population
PER_PERSON = (
    "gov.economic_assumptions.yoy_growth.orr.per_capita.rail_passenger_journeys"
)

# ORR Table 1220, passenger journeys (million), by the year each financial
# year starts in (2020 is April 2020 to March 2021).
JOURNEYS = {
    2020: 387.885467,
    2021: 990.062033,
    2022: 1_384.752483,
    2023: 1_612.028410,
    2024: 1_728.704107,
    2025: 1_829.468293,
}


@pytest.mark.parametrize("year", sorted(JOURNEYS))
def test_ridership_index_is_orr_journeys_on_a_2020_21_base(year):
    # 2021-22: 990.062 / 387.885 = 2.5525; 2024-25: 1,728.704 / 387.885 =
    # 4.4567. Before #1862 these were 0.400 and 0.950.
    expected = JOURNEYS[year] / JOURNEYS[2020]
    assert RIDERSHIP(f"{year}-01-01") == pytest.approx(expected, abs=5e-5)


@pytest.mark.parametrize("year", range(2026, 2031))
def test_journeys_are_held_flat_after_2025_26(year):
    assert RIDERSHIP(f"{year}-01-01") == RIDERSHIP("2025-01-01")


# Every year ons.population has a value for from 2021, so the offset runs as
# far as the population series does and never stops while population growth
# carries on changing.
POPULATION_YEARS = [
    int(value.instant_str[:4])
    for value in POPULATION.values_list
    if int(value.instant_str[:4]) >= 2021
]


@pytest.mark.parametrize("year", POPULATION_YEARS)
def test_per_person_growth_is_journeys_growth_net_of_population_growth(year):
    # 2025-26: (1,829.468 / 1,728.704) / 1.0030 - 1 = 0.0551. Fails if either
    # input series changes without re-deriving this one.
    instant, previous = f"{year}-01-01", f"{year - 1}-01-01"
    expected = RIDERSHIP(instant) / RIDERSHIP(previous) / (1 + POPULATION(instant)) - 1
    assert parameters.get_child(PER_PERSON)(instant) == pytest.approx(
        expected, abs=5e-5
    )


def _dataset(rail_usage):
    ids = np.arange(len(rail_usage))
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
                "household_weight": 1.0,
                "region": "LONDON",
                "tenure_type": "OWNED_OUTRIGHT",
                "rent": 0.0,
                "council_tax": 0.0,
                "rail_usage": rail_usage,
            }
        ),
        fiscal_year=2024,
    )


def _total(dataset):
    household = dataset.household
    return (household["rail_usage"] * household["household_weight"]).sum()


def test_projected_rail_usage_tracks_orr_journeys():
    # Each household's usage grows by 1.0583 / 1.0030 = 1.0551 into 2025-26
    # and the weights by 1.0030, so the weighted total grows by ORR's 5.83%.
    # From 2026-27 the total stays flat in every projected year, past the end
    # of the OBR forecast too. Before #1862 rail_usage was not projected at
    # all.
    projected = extend_single_year_dataset(
        _dataset([100.0, 40.0]), parameters, end_year=PROJECTION_END_YEAR
    )
    datasets = projected.datasets
    assert datasets[2025].household["rail_usage"].tolist() == pytest.approx(
        [105.51, 42.204], rel=1e-4
    )
    assert _total(datasets[2025]) / _total(datasets[2024]) == pytest.approx(
        JOURNEYS[2025] / JOURNEYS[2024], abs=1e-4
    )
    # Four-decimal rounding of the two growth series moves the total by at
    # most 0.005% a year.
    for year in range(2026, PROJECTION_END_YEAR + 1):
        assert _total(datasets[year]) == pytest.approx(
            _total(datasets[2025]), rel=5e-5 * (year - 2025)
        ), year
