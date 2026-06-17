import pandas as pd
import pytest

from policyengine_uk.data.dataset_schema import UKSingleYearDataset
from policyengine_uk.data.economic_assumptions import extend_single_year_dataset
from policyengine_uk.system import system


def test_petrol_and_diesel_spending_preserve_road_fuel_litres_not_cpi():
    parameters = system.parameters
    road_fuel_volume = (
        parameters.gov.economic_assumptions.yoy_growth.obr.road_fuel_volume
    )
    petrol_proxy = (
        parameters.gov.economic_assumptions.yoy_growth.obr.petrol_spending_litre_proxy
    )
    diesel_proxy = (
        parameters.gov.economic_assumptions.yoy_growth.obr.diesel_spending_litre_proxy
    )
    population = parameters.gov.economic_assumptions.yoy_growth.ons.population
    petrol_price = parameters.household.consumption.fuel.prices.petrol
    diesel_price = parameters.household.consumption.fuel.prices.diesel
    cpi = parameters.gov.economic_assumptions.yoy_growth.obr.consumer_price_index

    assert road_fuel_volume(2024) < 0
    assert cpi(2024) > 0
    assert petrol_proxy(2024) != road_fuel_volume(2024)
    assert diesel_proxy(2024) != road_fuel_volume(2024)

    dataset = UKSingleYearDataset(
        person=pd.DataFrame(
            {
                "person_id": [1],
                "person_benunit_id": [1],
                "person_household_id": [1],
                "age": [40],
            }
        ),
        benunit=pd.DataFrame({"benunit_id": [1]}),
        household=pd.DataFrame(
            {
                "household_id": [1],
                "region": ["LONDON"],
                "tenure_type": ["OWNED_OUTRIGHT"],
                "council_tax": [1_500.0],
                "rent": [0.0],
                "household_weight": [1.0],
                "petrol_spending": [1_000.0 * petrol_price(2023)],
                "diesel_spending": [2_000.0 * diesel_price(2023)],
            }
        ),
        fiscal_year=2023,
    )

    extended = extend_single_year_dataset(
        dataset,
        tax_benefit_system_parameters=parameters,
        end_year=2035,
    )
    household_2024 = extended[2024].household

    assert household_2024["petrol_spending"].iloc[0] == pytest.approx(
        1_000 * petrol_price(2023) * (1 + petrol_proxy(2024))
    )
    assert household_2024["diesel_spending"].iloc[0] == pytest.approx(
        2_000 * diesel_price(2023) * (1 + diesel_proxy(2024))
    )
    assert household_2024["household_weight"].iloc[0] == pytest.approx(
        1 + population(2024)
    )
    assert (
        household_2024["petrol_spending"].iloc[0]
        / petrol_price(2024)
        * household_2024["household_weight"].iloc[0]
    ) == pytest.approx(1_000 * (1 + road_fuel_volume(2024)))
    assert (
        household_2024["diesel_spending"].iloc[0]
        / diesel_price(2024)
        * household_2024["household_weight"].iloc[0]
    ) == pytest.approx(2_000 * (1 + road_fuel_volume(2024)))

    household_2034 = extended[2034].household
    household_2035 = extended[2035].household

    def weighted_litres(household, spending_variable, price_parameter, year):
        return (
            household[spending_variable].iloc[0]
            / price_parameter(year)
            * household["household_weight"].iloc[0]
        )

    assert weighted_litres(
        household_2035,
        "petrol_spending",
        petrol_price,
        2035,
    ) == pytest.approx(
        weighted_litres(household_2034, "petrol_spending", petrol_price, 2034)
        * (1 + road_fuel_volume(2035))
    )
    assert weighted_litres(
        household_2035,
        "diesel_spending",
        diesel_price,
        2035,
    ) == pytest.approx(
        weighted_litres(household_2034, "diesel_spending", diesel_price, 2034)
        * (1 + road_fuel_volume(2035))
    )


def test_bus_fare_spending_uses_cpi_uprating():
    parameters = system.parameters
    cpi = parameters.gov.economic_assumptions.yoy_growth.obr.consumer_price_index

    dataset = UKSingleYearDataset(
        person=pd.DataFrame(
            {
                "person_id": [1],
                "person_benunit_id": [1],
                "person_household_id": [1],
                "age": [40],
            }
        ),
        benunit=pd.DataFrame({"benunit_id": [1]}),
        household=pd.DataFrame(
            {
                "household_id": [1],
                "region": ["LONDON"],
                "tenure_type": ["OWNED_OUTRIGHT"],
                "council_tax": [1_500.0],
                "rent": [0.0],
                "household_weight": [1.0],
                "bus_fare_spending": [100.0],
            }
        ),
        fiscal_year=2025,
    )

    extended = extend_single_year_dataset(
        dataset,
        tax_benefit_system_parameters=parameters,
        end_year=2026,
    )

    assert extended[2026].household["bus_fare_spending"].iloc[0] == pytest.approx(
        100 * (1 + cpi(2026))
    )
