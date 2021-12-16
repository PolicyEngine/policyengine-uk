from openfisca_uk.model_api import *


class owned_land(Variable):
    entity = Household
    label = "Owned land"
    documentation = "Total value of all land-only plots owned by the household"
    unit = "currency-GBP"
    definition_period = YEAR
    value_type = float


class land_value(Variable):
    entity = Household
    label = "Land value"
    documentation = "Estimated total land value exposure (your property's land value, and any share of corporate land value)"
    unit = "currency-GBP"
    definition_period = YEAR
    value_type = float

    def formula(household, period, parameters):
        property_wealth = household("property_wealth", period)
        corporate_wealth = household("corporate_wealth", period)
        wealth = parameters(period).wealth
        land_value = wealth.land_value
        property_wealth_intensity = (
            land_value.aggregate_household_land_value / wealth.aggregates.property_wealth
        )
        corporate_wealth_intensity = (
            land_value.aggregate_corporate_land_value / wealth.aggregates.corporate_wealth
        )
        return (
            property_wealth * property_wealth_intensity
            + corporate_wealth * corporate_wealth_intensity
            + household("owned_land", period)
        )
