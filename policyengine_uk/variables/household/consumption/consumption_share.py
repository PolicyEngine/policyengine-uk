from policyengine_uk.model_api import *


class consumption_shareholding(Variable):
    label = "share of UK consumption"
    documentation = "Exposure to taxes on consumption"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(household, period, parameters):
        consumption = household("consumption", period)
        if (
            household.simulation.dataset is not None
            and household("consumption", period).sum() != 0
        ):
            weight = household("household_weight", period)
            return consumption / (consumption * weight).sum()
        return 0
