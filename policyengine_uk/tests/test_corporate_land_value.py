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


def test_corporate_land_value_key_is_unchanged_by_the_pension_split():
    """Moving wealth between corporate_wealth and private_pension_wealth must not
    move corporate land value: the allocation key is corporate_sector_wealth."""

    def land_values(household_1: dict, household_2: dict):
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
                        "household_weight": {2025: 2},
                        **household_1,
                    },
                    "household_2": {
                        "members": ["person_2"],
                        "household_weight": {2025: 1},
                        **household_2,
                    },
                },
            }
        )
        return (
            sim.calculate("corporate_land_value", map_to="household", period=2025),
            sim.calculate("shareholding", map_to="household", period=2025),
        )

    folded_land, folded_share = land_values(
        {"corporate_wealth": {2025: 100_000}},
        {"corporate_wealth": {2025: 300_000}},
    )
    split_land, split_share = land_values(
        {"corporate_wealth": {2025: 20_000}, "private_pension_wealth": {2025: 80_000}},
        {"corporate_wealth": {2025: 50_000}, "private_pension_wealth": {2025: 250_000}},
    )

    assert split_land[0] == pytest.approx(folded_land[0])
    assert split_land[1] == pytest.approx(folded_land[1])
    assert split_share[0] == pytest.approx(folded_share[0])
    assert split_share[1] == pytest.approx(folded_share[1])


def test_employer_ni_capital_incidence_is_unchanged_by_the_pension_split():
    """The employer-NI capital response allocates by corporate_sector_wealth,
    so moving wealth between corporate_wealth and private_pension_wealth must
    not move any household's incidence."""
    reform = {
        "gov.contrib.policyengine.employer_ni.employee_incidence": {"2025": 0.5},
        "gov.contrib.policyengine.employer_ni.capital_incidence": {"2025": 0.5},
    }

    def incidence(household_1: dict, household_2: dict):
        sim = Simulation(
            reform=reform,
            situation={
                "people": {
                    "person_1": {
                        "age": {2025: 40},
                        "employment_income": {2025: 30_000},
                    },
                    "person_2": {
                        "age": {2025: 50},
                        "employment_income": {2025: 60_000},
                    },
                },
                "benunits": {
                    "benunit_1": {"members": ["person_1"]},
                    "benunit_2": {"members": ["person_2"]},
                },
                "households": {
                    "household_1": {
                        "members": ["person_1"],
                        "household_weight": {2025: 2},
                        **household_1,
                    },
                    "household_2": {
                        "members": ["person_2"],
                        "household_weight": {2025: 1},
                        **household_2,
                    },
                },
            },
        )
        return sim.calculate(
            "employer_ni_response_capital_incidence", map_to="household", period=2025
        )

    folded = incidence(
        {"corporate_wealth": {2025: 100_000}},
        {"corporate_wealth": {2025: 300_000}},
    )
    split = incidence(
        {"corporate_wealth": {2025: 20_000}, "private_pension_wealth": {2025: 80_000}},
        {"corporate_wealth": {2025: 50_000}, "private_pension_wealth": {2025: 250_000}},
    )

    assert split[0] == pytest.approx(folded[0])
    assert split[1] == pytest.approx(folded[1])
