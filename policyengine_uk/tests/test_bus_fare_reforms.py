"""Exercise data loading, nonlinear calendar dates and real Scenario reforms."""

import numpy as np
import pandas as pd
import pytest

from policyengine_uk import Simulation
from policyengine_uk.data.dataset_schema import UKMultiYearDataset, UKSingleYearDataset
from policyengine_uk.system import system
from policyengine_uk.utils.bus_fares import annual_capped_fare
from policyengine_uk.utils.scenario import Scenario


pytestmark = pytest.mark.usefixtures("cloned_uk_tax_benefit_system")


def bus_dataset(region="SOUTH_EAST", journeys=True, zero=False):
    person = pd.DataFrame(
        {
            "person_id": [1, 2],
            "person_benunit_id": [1, 1],
            "person_household_id": [1, 1],
            "age": [30, 30],
        }
    )
    if journeys:
        person["other_local_bus_trips"] = [0, 0] if zero else [100, 20]
        person["bus_in_london_trips"] = [0, 0]
        person["bus_pass_eligible"] = [False, False]
        person["local_bus_single_fare_share"] = [0.7, 0.7]
    return UKMultiYearDataset(
        datasets=[
            UKSingleYearDataset(
                person=person,
                benunit=pd.DataFrame({"benunit_id": [1]}),
                household=pd.DataFrame(
                    {
                        "household_id": [1],
                        "region": [region],
                        "bus_fare_spending": [999.0],
                    }
                ),
                fiscal_year=2024,
            )
        ]
    )


def test_loaded_total_does_not_mask_journeys_or_cap_reforms():
    simulation = Simulation(
        dataset=bus_dataset(),
        scenario=Scenario(parameter_changes={"gov.dft.bus.fares.cap": {2024: np.inf}}),
    )
    # Published 2024-25 receipts / fare-paying boardings, translated from trips.
    k = 1_850_509_887.26131 / (28.0685543170643 * 58_620_101)
    fare_paying = 1_850_509_887.26131 - 519_107_608.59444
    benchmark = 2_069_953_713.42079 / fare_paying
    uncapped_yield = benchmark + 515_693_216.6 / fare_paying
    baseline_people = np.array([100, 20]) * k * benchmark
    reformed_people = np.array([100, 20]) * k * uncapped_yield
    assert simulation.baseline.calculate(
        "person_bus_fare_spending", 2024
    ) == pytest.approx(baseline_people)
    assert simulation.calculate("person_bus_fare_spending", 2024) == pytest.approx(
        reformed_people
    )
    assert simulation.calculate("bus_fare_spending", 2024)[0] == pytest.approx(
        reformed_people.sum()
    )
    assert simulation.baseline.calculate("bus_fare_spending", 2024)[0] == pytest.approx(
        baseline_people.sum()
    )
    assert simulation.calculate("bus_fare_spending_reported", 2024)[0] == 999


def test_explicit_zero_journeys_replace_a_stale_positive_total():
    simulation = Simulation(dataset=bus_dataset(zero=True))
    assert simulation.calculate("bus_fare_spending", 2024)[0] == 0


@pytest.mark.parametrize("region", ["SOUTH_EAST", "WALES", "UNKNOWN"])
def test_legacy_fallback_and_proportional_reform(region):
    simulation = Simulation(
        dataset=bus_dataset(region, journeys=False),
        scenario=Scenario(parameter_changes={"gov.dft.bus.fare_index": {2024: 0.5}}),
    )
    # Calculating a default trip count must not make it a supplied zero.
    assert simulation.calculate("local_bus_trips", 2024).sum() == 0
    assert simulation.baseline.calculate("bus_fare_spending", 2024)[0] == 999
    assert simulation.calculate("bus_fare_spending", 2024)[0] == 499.5
    assert simulation.calculate("person_bus_fare_spending", 2024) == pytest.approx(
        [249.75, 249.75]
    )


def test_wales_keeps_reported_spending_even_with_journeys():
    simulation = Simulation(dataset=bus_dataset("WALES"))
    assert simulation.calculate("bus_fare_spending", 2024)[0] == 999


@pytest.mark.parametrize("region", ["SCOTLAND", "NORTHERN_IRELAND"])
def test_national_cap_reform_does_not_change_devolved_fares(region):
    simulation = Simulation(
        dataset=bus_dataset(region),
        scenario=Scenario(parameter_changes={"gov.dft.bus.fares.cap": {2024: 0}}),
    )
    assert simulation.calculate("bus_fare_spending", 2024)[0] > 0
    assert simulation.calculate("bus_fare_spending", 2024) == pytest.approx(
        simulation.baseline.calculate("bus_fare_spending", 2024)
    )


def test_ridership_multiplier_is_explicit_and_does_not_change_input_journeys():
    simulation = Simulation(
        dataset=bus_dataset(),
        scenario=Scenario(
            parameter_changes={"gov.dft.bus.ridership_index": {2024: 1.2}}
        ),
    )
    assert simulation.calculate("bus_fare_spending", 2024)[0] == pytest.approx(
        simulation.baseline.calculate("bus_fare_spending", 2024)[0] * 1.2
    )
    assert simulation.calculate("local_bus_trips", 2024).tolist() == [100, 20]


def test_caps_apply_before_annual_averaging_and_preserve_january_changes():
    schedule = system.parameters.gov.dft.bus.fares
    assert schedule("2024-12-31").cap == 2
    assert schedule("2025-01-01").cap == 3
    assert schedule("2026-12-31").cap == 3
    assert schedule("2027-01-01").cap == 2
    assert np.isinf(schedule("2028-01-01").cap)
    # A £2.50 fare is capped at £2 for 270 days, then costs £2.50 for 95.
    assert annual_capped_fare(2.5, schedule, 2024) == pytest.approx(
        (270 * 2 + 95 * 2.5) / 365
    )
    # The £2 cap returns part-way through the 2026 fiscal year.
    assert annual_capped_fare(4, schedule, 2026) == pytest.approx(
        (270 * 3 + 95 * 2) / 365
    )


def test_clone_does_not_lose_journey_input_provenance():
    original = Simulation(dataset=bus_dataset())
    expected = original.calculate("bus_fare_spending", 2024)[0]
    clone = original.clone()
    clone.delete_arrays("bus_fare_spending")
    clone.delete_arrays("person_bus_fare_spending")
    assert clone.calculate("bus_fare_spending", 2024)[0] == expected
    clone.delete_arrays("other_local_bus_trips")
    assert original.calculate("other_local_bus_trips", 2024).tolist() == [100, 20]
