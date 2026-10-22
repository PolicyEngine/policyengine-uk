"""Liquid and solid heating fuel inputs (#2572).

Homes off the gas grid heat with oil, LPG, coal or wood: COICOP 04.5.3 and
04.5.4. Their spending is part of housing_water_and_electricity_consumption,
so the inputs default to zero, add nothing to consumption, and are projected
as the other domestic energy inputs are.
"""

from pathlib import Path

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


def test_fuels_are_projected_as_the_other_energy_inputs_are():
    listed = yaml.safe_load(UPRATING_INDICES.read_text())
    for fuel in FUELS:
        assert fuel in DATASET_UPRATING_EXCLUSIONS
        assert not any(fuel in variables for variables in listed.values())
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
    projected = extend_single_year_dataset(dataset, system.parameters)
    for year, single_year in projected.datasets.items():
        for fuel, stored in (
            ("liquid_fuel_consumption", 1_500.0),
            ("solid_fuel_consumption", 300.0),
        ):
            assert single_year.household[fuel].iloc[0] == stored, (fuel, year)
