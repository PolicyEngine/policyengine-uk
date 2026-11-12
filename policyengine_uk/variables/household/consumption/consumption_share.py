from policyengine_uk.model_api import *
from policyengine_uk.utils.data_source import built_from_data
from policyengine_uk.utils.uk_totals import carried_uk_total


class consumption_shareholding(Variable):
    label = "share of UK consumption"
    documentation = (
        "The household's share of the consumption of all UK households, the "
        "key that consumer-incident tax changes are allocated by. Where the "
        "data carries the UK total (policyengine_uk.utils.uk_totals), it is "
        "the household's consumption over that total, whichever households "
        "are simulated. Otherwise, in a simulation built from data, it is "
        "over the simulation's weighted total, so the shares sum to one, and "
        "0 where that total is 0. A household situation that carries no UK "
        "total has no population to take a share of, so its share is 0 "
        "unless set."
    )
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = "/1"

    def formula(household, period, parameters):
        consumption = household("consumption", period)
        uk_total = carried_uk_total(household, "consumption", period)
        carried = uk_total > 0
        share = np.divide(
            consumption, uk_total, out=np.zeros(len(consumption)), where=carried
        )
        if carried.all() or not built_from_data(household.simulation):
            return share
        weighted_total = (consumption * household("household_weight", period)).sum()
        if weighted_total == 0:
            return share
        return where(carried, share, consumption / weighted_total)
