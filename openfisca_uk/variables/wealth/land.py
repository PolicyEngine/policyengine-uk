from openfisca_uk.model_api import *


class owned_land(Variable):
    entity = Household
    label = "Owned land"
    documentation = "Total value of all land-only plots owned by the household"
    unit = "currency-GBP"
    definition_period = YEAR
    value_type = float


class land_value(Variable):
    label = "Land value"
    documentation = (
        "Estimated total land value (directly and indirectly owned)"
    )
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = "currency-GBP"

    def formula(household, period):
        VARIABLES = [
            "household_land_value",
            "corporate_land_value",
        ]
        return add(household, period, VARIABLES)


class household_land_value(Variable):
    entity = Household
    label = "Land value"
    documentation = (
        "Estimated total land value directly owned by the household"
    )
    unit = "currency-GBP"
    definition_period = YEAR
    value_type = float

    def formula(household, period, parameters):
        property_wealth = household("property_wealth", period)
        total_property_wealth = (
            property_wealth * household("household_weight", period)
        ).sum()
        land = parameters(period).wealth.land
        property_wealth_intensity = (
            land.value.aggregate_household_land_value / total_property_wealth
        )
        property_wealth_intensity = where(
            total_property_wealth > 0,
            property_wealth_intensity,
            land.intensity.property_wealth,
        )
        owned_land = household("owned_land", period)
        return property_wealth * property_wealth_intensity + owned_land


class corporate_land_value(Variable):
    entity = Household
    label = "Land value"
    documentation = "Estimated total land value indirectly owned by the household from corporate holdings"
    unit = "currency-GBP"
    definition_period = YEAR
    value_type = float

    def formula(household, period, parameters):
        corporate_wealth = household("corporate_wealth", period)
        total_corporate_wealth = (
            corporate_wealth * household("household_weight", period)
        ).sum()
        land = parameters(period).wealth.land
        corporate_wealth_intensity = (
            land.value.aggregate_corporate_land_value / total_corporate_wealth
        )
        corporate_wealth_intensity = where(
            total_corporate_wealth > 0,
            corporate_wealth_intensity,
            land.intensity.corporate_wealth,
        )
        return corporate_wealth * corporate_wealth_intensity
