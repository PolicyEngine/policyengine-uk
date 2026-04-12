from policyengine_uk import Simulation
import pytest


def test_corporate_land_value_matches_aggregate_for_weighted_dataset():
    sim = Simulation(
        situation={
            "people": {
                "person_1": {"age": {2025: 40}},
                "person_2": {"age": {2025: 50}},
            },
            "benunits": {
                "benunit_1": {"members": ["person_1"]},
                "benunit_2": {"members": ["person_2"]},
            },
            "households": {
                "household_1": {
                    "members": ["person_1"],
                    "corporate_wealth": {2025: 100_000},
                    "household_weight": {2025: 2},
                },
                "household_2": {
                    "members": ["person_2"],
                    "corporate_wealth": {2025: 300_000},
                    "household_weight": {2025: 1},
                },
            },
        }
    )

    corporate_land_value = sim.calculate(
        "corporate_land_value", map_to="household", period=2025
    )
    household_weight = sim.calculate(
        "household_weight", map_to="household", period=2025
    )
    aggregate = sim.tax_benefit_system.parameters(
        "2025"
    ).household.wealth.land.value.aggregate_corporate_land_value

    assert corporate_land_value[0] == pytest.approx(aggregate * 0.2)
    assert corporate_land_value[1] == pytest.approx(aggregate * 0.6)
    assert (corporate_land_value * household_weight).sum() == pytest.approx(aggregate)


def test_corporate_land_value_is_zero_without_corporate_wealth():
    sim = Simulation(
        situation={
            "people": {"person": {"age": {2025: 40}}},
            "benunits": {"benunit": {"members": ["person"]}},
            "households": {
                "household": {
                    "members": ["person"],
                    "corporate_wealth": {2025: 0},
                    "household_weight": {2025: 1},
                }
            },
        }
    )

    corporate_land_value = sim.calculate(
        "corporate_land_value", map_to="household", period=2025
    )

    assert corporate_land_value[0] == 0
