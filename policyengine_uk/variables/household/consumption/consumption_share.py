from policyengine_uk.model_api import *
from policyengine_uk.utils.data_source import built_from_data


class consumption_shareholding(Variable):
    label = "share of UK consumption"
    documentation = (
        "The household's share of the consumption of all UK households, the "
        "key that consumer-incident tax changes are allocated by. In a "
        "simulation built from data it is the household's consumption over "
        "the simulation's weighted total, so the shares sum to one, and 0 "
        "where that total is 0. A household situation has no population to "
        "take a share of, so its share is 0 unless set."
    )
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = "/1"

    def formula(household, period, parameters):
        if not built_from_data(household.simulation):
            return 0
        consumption = household("consumption", period)
        weighted_total = (consumption * household("household_weight", period)).sum()
        if weighted_total == 0:
            return 0
        return consumption / weighted_total
