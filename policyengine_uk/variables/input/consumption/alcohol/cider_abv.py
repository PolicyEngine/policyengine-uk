from policyengine_uk.model_api import *


class cider_abv(Variable):
    value_type = float
    entity = Household
    definition_period = YEAR
    label = "Cider alcohol by volume"
    unit = "/1"
    quantity_type = STOCK

    def formula(household, period, parameters):
        return parameters(period).household.consumption.alcohol.cider_abv
