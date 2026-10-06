from policyengine_uk.model_api import *


class sparkling_cider_abv(Variable):
    value_type = float
    entity = Household
    definition_period = YEAR
    label = "Sparkling cider alcohol by volume"
    unit = "/1"
    quantity_type = STOCK

    def formula(household, period, parameters):
        return parameters(period).household.consumption.alcohol.sparkling_cider_abv
