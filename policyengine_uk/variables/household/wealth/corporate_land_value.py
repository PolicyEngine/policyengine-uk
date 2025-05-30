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
        wealth = parameters(period).household.wealth
        corporate_wealth = household("corporate_wealth", period)
        corporate_wealth_intensity = (
            wealth.land.value.aggregate_corporate_land_value
            / wealth.corporate_wealth
        )
        return corporate_wealth * corporate_wealth_intensity
