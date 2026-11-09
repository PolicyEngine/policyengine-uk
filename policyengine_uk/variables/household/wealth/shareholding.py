from policyengine_uk.model_api import *
from policyengine_uk.utils.data_source import built_from_data


class shareholding(Variable):
    label = "Share in the corporate sector"
    documentation = (
        "The household's share of the corporate_sector_wealth of all UK "
        "households, the key that business rates, corporate Stamp Duty Land "
        "Tax, corporate land and the other corporate-incident terms are "
        "allocated by. In a simulation built from data it is the household's "
        "corporate_sector_wealth over the simulation's weighted total, so the "
        "shares sum to one, and 0 where that total is 0. A household situation "
        "has no population to take a share of, so its share is 0 unless set."
    )
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = "/1"

    def formula(household, period, parameters):
        if not built_from_data(household.simulation):
            return 0
        wealth = household("corporate_sector_wealth", period)
        weighted_total = (wealth * household("household_weight", period)).sum()
        if weighted_total == 0:
            return 0
        return wealth / weighted_total
