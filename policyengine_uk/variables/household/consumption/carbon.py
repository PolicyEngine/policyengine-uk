from policyengine_uk.model_api import *


class carbon_consumption(Variable):
    entity = Household
    label = "Carbon consumption"
    documentation = "Estimated total carbon footprint of the household"
    unit = "tonne CO2"
    definition_period = YEAR
    value_type = float

    def formula(household, period, parameters):
        CONSUMPTION_VARIABLES = [
            "food_and_non_alcoholic_beverages_consumption",
            "alcohol_and_tobacco_consumption",
            "clothing_and_footwear_consumption",
            "housing_water_and_electricity_consumption",
            "household_furnishings_consumption",
            "health_consumption",
            "transport_consumption",
            "communication_consumption",
            "recreation_consumption",
            "education_consumption",
            "restaurants_and_hotels_consumption",
            "miscellaneous_consumption",
        ]
        consumption = parameters(period).household.consumption
        aggregate_spending_by_sector = [
            consumption.total_by_category[category]
            for category in CONSUMPTION_VARIABLES
        ]
        carbon = consumption.carbon
        aggregate_emissions_by_sector = [
            carbon.emissions[category.replace("_consumption", "")]
            for category in CONSUMPTION_VARIABLES
        ]
        carbon_intensity_by_sector = [
            emissions / spending if spending > 0 else carbon.intensity[name]
            for emissions, spending, name in zip(
                aggregate_emissions_by_sector,
                aggregate_spending_by_sector,
                CONSUMPTION_VARIABLES,
            )
        ]
        spending_by_sector = [
            household(category, period) for category in CONSUMPTION_VARIABLES
        ]
        return sum(
            [
                spending * carbon_intensity
                for spending, carbon_intensity in zip(
                    spending_by_sector, carbon_intensity_by_sector
                )
            ]
        )
