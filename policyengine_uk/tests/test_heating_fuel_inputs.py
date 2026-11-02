"""Liquid and solid heating fuel inputs (#2572).

Homes off the gas grid heat with oil (COICOP 04.5.3), LPG (04.5.2), coal or
wood (04.5.4). Their spending is part of
housing_water_and_electricity_consumption, so the inputs default to zero and
add nothing to consumption. Ofgem's price cap does not cover them, so dataset
projection uprates them by CPI like other LCFS spending.
"""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml

from policyengine_uk import Simulation
from policyengine_uk.data import UKSingleYearDataset
from policyengine_uk.data.economic_assumptions import (
    DATASET_UPRATING_EXCLUSIONS,
    extend_single_year_dataset,
)
from policyengine_uk.system import system

FUELS = ("liquid_fuel_consumption", "solid_fuel_consumption")
UPRATING_INDICES = Path(__file__).parents[1] / "data" / "uprating_indices.yaml"
CPI_GROWTH = "gov.economic_assumptions.yoy_growth.obr.consumer_price_index"
CPI = system.parameters.gov.economic_assumptions.yoy_growth.obr.consumer_price_index


def household(**inputs):
    return Simulation(
        situation={
            "people": {"adult": {"age": 50}},
            "households": {
                "home": {
                    "members": ["adult"],
                    "housing_water_and_electricity_consumption": {2026: 3_000},
                    **{k: {2026: v} for k, v in inputs.items()},
                }
            },
        }
    )


@pytest.mark.parametrize("fuel", FUELS)
def test_defaults_are_zero_and_add_nothing_to_consumption(fuel):
    assert household().calculate(fuel, 2026)[0] == 0
    with_fuel = household(**{fuel: 1_200})
    assert with_fuel.calculate(fuel, 2026)[0] == 1_200
    assert with_fuel.calculate("consumption", 2026)[0] == pytest.approx(
        household().calculate("consumption", 2026)[0]
    )


def test_fuels_are_uprated_by_cpi_like_other_lcfs_spending():
    # Ofgem's cap prices the electricity and gas inputs, which are held at
    # their stored prices; it does not cover heating oil, LPG, coal or wood.
    listed = yaml.safe_load(UPRATING_INDICES.read_text())
    for fuel in FUELS:
        assert fuel not in DATASET_UPRATING_EXCLUSIONS
        assert [i for i, v in listed.items() if fuel in v] == [CPI_GROWTH]
    dataset = UKSingleYearDataset(
        person=pd.DataFrame(
            {
                "person_id": [1],
                "person_benunit_id": [1],
                "person_household_id": [1],
                "age": [50],
            }
        ),
        benunit=pd.DataFrame({"benunit_id": [1]}),
        household=pd.DataFrame(
            {
                "household_id": [1],
                "household_weight": [1.0],
                "region": ["NORTHERN_IRELAND"],
                "tenure_type": ["OWNED_OUTRIGHT"],
                "rent": [0.0],
                "council_tax": [0.0],
                "gas_consumption": [0.0],
                "liquid_fuel_consumption": [1_500.0],
                "solid_fuel_consumption": [300.0],
            }
        ),
        fiscal_year=2024,
    )
    projected = extend_single_year_dataset(dataset, system.parameters, end_year=2029)
    growth = np.prod([1 + CPI(str(year)) for year in range(2025, 2030)])
    household = projected.datasets[2029].household
    assert household["liquid_fuel_consumption"].iloc[0] == pytest.approx(
        1_500.0 * growth
    )
    assert household["solid_fuel_consumption"].iloc[0] == pytest.approx(300.0 * growth)
    assert growth > 1
