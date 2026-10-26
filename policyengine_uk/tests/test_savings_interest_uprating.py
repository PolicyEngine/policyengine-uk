"""Savings interest is projected by interest received per person (#1862).

The aggregate is households' (S.14) interest received, D.41 resources, ONS
series HAXV (UK Economic Accounts, release of 30 September 2026), in £m. From
2026 the OBR forecasts no interest received, so the series is the growth in
household financial assets (OBR March 2026 EFO, economy Table 1.11, ONS NNML,
£bn) times the ratio of deposit rates (Table 1.9, per cent), calendar years.

Household weights grow by ons.population, so each person's interest grows by
the aggregate net of population growth. Growing it by the aggregate itself
would count population growth twice, the defect #2067 fixed for council tax.
"""

import numpy as np
import pandas as pd
import pytest

from policyengine_uk import parameters
from policyengine_uk.data import UKSingleYearDataset
from policyengine_uk.data.economic_assumptions import extend_single_year_dataset

GROWTH = parameters.gov.economic_assumptions.yoy_growth
AGGREGATE = GROWTH.ons.household_interest_income
PER_PERSON = (
    "gov.economic_assumptions.yoy_growth.ons.per_capita.household_interest_income"
)
POPULATION = GROWTH.ons.population

# ONS HAXV, calendar years, £m (release of 30 September 2026).
HAXV = {
    2019: 22_923,
    2020: 15_988,
    2021: 19_566,
    2022: 43_282,
    2023: 86_092,
    2024: 98_189,
    2025: 95_477,
}
# OBR March 2026 EFO economy tables, calendar-year rows: household financial
# assets (Table 1.11, £bn) and the deposit rate (Table 1.9, per cent).
FINANCIAL_ASSETS = {
    2025: 6_858.721440,
    2026: 7_109.482196,
    2027: 7_287.736448,
    2028: 7_460.840218,
    2029: 7_619.197210,
    2030: 7_768.507487,
}
DEPOSIT_RATE = {
    2025: 2.287040,
    2026: 1.999673,
    2027: 2.078212,
    2028: 2.257936,
    2029: 2.417240,
    2030: 2.570582,
}


@pytest.mark.parametrize("year", range(2020, 2026))
def test_outturn_is_haxv_growth(year):
    # 2025: 95,477 / 98,189 - 1 = -0.0276, against +0.0349 before #1862,
    # which was OBR non-labour income growth.
    expected = HAXV[year] / HAXV[year - 1] - 1
    assert AGGREGATE(f"{year}-01-01") == pytest.approx(expected, abs=5e-5)


@pytest.mark.parametrize("year", range(2026, 2031))
def test_forecast_is_financial_assets_growth_times_the_deposit_rate_ratio(year):
    # 2026: (7,109.48 / 6,858.72) x (1.9997 / 2.2870) - 1 = -0.0937.
    expected = (
        FINANCIAL_ASSETS[year]
        / FINANCIAL_ASSETS[year - 1]
        * DEPOSIT_RATE[year]
        / DEPOSIT_RATE[year - 1]
        - 1
    )
    assert AGGREGATE(f"{year}-01-01") == pytest.approx(expected, abs=5e-5)


@pytest.mark.parametrize("year", range(2021, 2031))
def test_per_person_growth_is_the_aggregate_net_of_population_growth(year):
    # 2025: 0.9724 / 1.0030 - 1 = -0.0305. Fails if ons.population is
    # refreshed without re-deriving this series.
    instant = f"{year}-01-01"
    expected = (1 + AGGREGATE(instant)) / (1 + POPULATION(instant)) - 1
    assert parameters.get_child(PER_PERSON)(instant) == pytest.approx(
        expected, abs=5e-5
    )


def _dataset(interest, fiscal_year=2024, **kwargs):
    ids = np.arange(len(interest))
    return UKSingleYearDataset(
        person=pd.DataFrame(
            {
                "person_id": ids,
                "person_benunit_id": ids,
                "person_household_id": ids,
                "age": 40,
                "savings_interest_income": interest,
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
            }
        ),
        fiscal_year=fiscal_year,
        **kwargs,
    )


def test_projected_total_interest_tracks_haxv_in_2025():
    # Each person's interest grows by 0.9724 / 1.0030 = 0.9695 and the
    # weights by 1.0030, so the weighted total grows by 95,477 / 98,189.
    projected = extend_single_year_dataset(
        _dataset([1_000.0, 250.0]), parameters, end_year=2025
    )
    base, after = projected.datasets[2024], projected.datasets[2025]

    def total(dataset):
        weights = dataset.household["household_weight"].to_numpy()
        return (dataset.person["savings_interest_income"].to_numpy() * weights).sum()

    assert after.person["savings_interest_income"].tolist() == pytest.approx(
        [969.5, 242.375], rel=1e-4
    )
    assert total(after) / total(base) == pytest.approx(
        HAXV[2025] / HAXV[2024], abs=1e-4
    )


INDEX = "gov.economic_assumptions.indices.ons.per_capita.household_interest_income"
LEGACY = {"version": 1, "representation": "legacy_gross", "projection": "legacy_gross"}


def test_index_includes_the_first_growth_year():
    # The per-person series starts at 2021 (ons.population has no 2020
    # value), so the index is anchored at 1 on 1 January 2020 and its
    # first step is the 2021 growth: 1.2238 / 1.0036 = 1.2194.
    index = parameters.get_child(INDEX)
    assert index("2020-01-01") == 1
    assert index("2021-01-01") / index("2020-01-01") == pytest.approx(
        1 + parameters.get_child(PER_PERSON)("2021-01-01"), abs=1e-5
    )


def test_direct_index_route_matches_dataset_projection_from_2020_to_2021():
    # A legacy 2020 observation queried for 2021 without projection uses
    # the index ratio (Simulation._run_formula); dataset projection uses the
    # 2021 growth rate. Both must give 100 x 1.2194.
    from copy import deepcopy

    from policyengine_uk import Simulation
    from policyengine_uk.data import UKMultiYearDataset

    def observed():
        return _dataset([100.0], 2020, isa_income_contract=deepcopy(LEGACY))

    direct = Simulation(dataset=UKMultiYearDataset(datasets=[observed()]))
    direct_2021 = float(direct.calculate("savings_interest_income", 2021)[0])

    projected = extend_single_year_dataset(observed(), parameters, end_year=2021)
    projected_2021 = float(
        projected.datasets[2021].person["savings_interest_income"].iloc[0]
    )

    assert projected_2021 == pytest.approx(121.94, abs=0.01)
    assert direct_2021 == pytest.approx(projected_2021, abs=0.01)
