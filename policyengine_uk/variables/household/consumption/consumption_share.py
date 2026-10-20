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
        if household.simulation.dataset is not None:
            weight = household("household_weight", period)
            weighted_total = (consumption * weight).sum()
            if weighted_total != 0:
                return consumption / weighted_total
        return 0
