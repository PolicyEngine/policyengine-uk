"""Pin data provenance through supported builders using only synthetic data."""

import pandas as pd
import pytest

from policyengine_core.simulations import Simulation as CoreSimulation
from policyengine_uk import Microsimulation, Simulation
from policyengine_uk.data import UKMultiYearDataset, UKSingleYearDataset
from policyengine_uk.system import system
from policyengine_uk.utils.data_source import built_from_data


YEAR = 2026
SITUATION = {
    "people": {"adult": {"age": {YEAR: 70}}},
    "benunits": {"family": {"members": ["adult"]}},
    "households": {
        "home": {
            "members": ["adult"],
            "region": {YEAR: "NORTH_WEST"},
            "tenure_type": {YEAR: "RENT_PRIVATELY"},
            "rent": {YEAR: 8000},
            "council_tax": {YEAR: 1800},
        }
    },
}


@pytest.fixture(scope="module")
def mock_dataset():
    return UKMultiYearDataset(
        datasets=[
            UKSingleYearDataset(
                person=pd.DataFrame(
                    {
                        "person_id": [1],
                        "person_benunit_id": [1],
                        "person_household_id": [1],
                        "age": [70],
                    }
                ),
                benunit=pd.DataFrame({"benunit_id": [1]}),
                household=pd.DataFrame(
                    {
                        "household_id": [1],
                        "region": ["NORTH_WEST"],
                        "tenure_type": ["RENT_PRIVATELY"],
                        "rent": [8000],
                        "council_tax": [1800],
                    }
                ),
                fiscal_year=YEAR,
            )
        ]
    )


@pytest.fixture(scope="module")
def mock_frame():
    return pd.DataFrame(
        {
            f"person_id__{YEAR}": [1],
            f"person_benunit_id__{YEAR}": [1],
            f"person_household_id__{YEAR}": [1],
            f"benunit_id__{YEAR}": [1],
            f"household_id__{YEAR}": [1],
            f"age__{YEAR}": [70],
            f"region__{YEAR}": ["NORTH_WEST"],
            f"tenure_type__{YEAR}": ["RENT_PRIVATELY"],
            f"rent__{YEAR}": [8000],
            f"council_tax__{YEAR}": [1800],
        }
    )


@pytest.fixture(
    scope="module",
    params=[Simulation, Microsimulation, CoreSimulation],
    ids=["uk-simulation", "uk-microsimulation", "core-simulation"],
)
def source_simulations(request, mock_dataset, mock_frame):
    simulation_class = request.param
    if simulation_class is CoreSimulation:
        return {
            "data": CoreSimulation(tax_benefit_system=system, dataset=mock_frame),
            "situation": CoreSimulation(tax_benefit_system=system, situation=SITUATION),
        }
    return {
        "data": simulation_class(dataset=mock_dataset),
        "situation": simulation_class(situation=SITUATION),
    }


@pytest.mark.parametrize("source, expected", [("data", True), ("situation", False)])
@pytest.mark.parametrize("derivation", ["original", "clone", "branch"])
def test_built_from_data_keeps_source_when_copying(
    source_simulations, source, expected, derivation
):
    simulation = source_simulations[source]
    if derivation == "clone":
        simulation = simulation.clone()
    elif derivation == "branch":
        simulation = simulation.get_branch()

    assert built_from_data(simulation) is expected


@pytest.mark.parametrize("simulation_class", [Simulation, Microsimulation])
def test_built_from_data_tracks_uk_situation_rebuild(simulation_class, mock_dataset):
    simulation = simulation_class(dataset=mock_dataset)
    assert built_from_data(simulation) is True

    simulation.build_from_situation(SITUATION)

    assert built_from_data(simulation) is False
