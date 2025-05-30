from policyengine_uk.model_api import *


class household_land_value(Variable):
    entity = Household
    label = "Land value"
    documentation = (
        "Estimated total land value directly owned by the household"
    )
    unit = GBP
    definition_period = YEAR
    value_type = float
    quantity_type = STOCK

    def formula(household, period, parameters):
        wealth = parameters(period).household.wealth
        property_wealth_intensity = (
            wealth.land.value.aggregate_household_land_value
            / wealth.property_wealth
        )
        property_wealth = household("property_wealth", period)
        owned_land = household("owned_land", period)
        return property_wealth * property_wealth_intensity + owned_land
