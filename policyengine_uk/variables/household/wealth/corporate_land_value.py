from policyengine_uk.model_api import *


class corporate_land_value(Variable):
    entity = Household
    label = "Land value"
    documentation = "Estimated total land value indirectly owned by the household from corporate holdings"
    unit = GBP
    definition_period = YEAR
    value_type = float
    quantity_type = STOCK

    def formula(household, period, parameters):
        corporate_wealth = household("corporate_wealth", period)
        household_weight = household("household_weight", period)
        total_weighted_corporate_wealth = (corporate_wealth * household_weight).sum()
        if total_weighted_corporate_wealth == 0:
            return corporate_wealth * 0

        aggregate_corporate_land_value = (
            parameters(period).household.wealth.land.value.aggregate_corporate_land_value
        )
        return (
            corporate_wealth
            / total_weighted_corporate_wealth
            * aggregate_corporate_land_value
        )
