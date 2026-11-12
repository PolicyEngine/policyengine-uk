from policyengine_uk.model_api import *


class corporate_land_value(Variable):
    entity = Household
    label = "Land value"
    documentation = (
        "Estimated total land value indirectly owned by the household from "
        "corporate holdings: its shareholding of the land UK corporations "
        "hold. A household situation holds none unless shareholding is set."
    )
    unit = GBP
    definition_period = YEAR
    value_type = float
    quantity_type = STOCK

    def formula(household, period, parameters):
        land = parameters(period).household.wealth.land.value
        return household("shareholding", period) * land.aggregate_corporate_land_value
