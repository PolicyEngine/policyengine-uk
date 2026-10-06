from policyengine_uk.model_api import *


class other_fermented_abv(Variable):
    value_type = float
    entity = Household
    definition_period = YEAR
    label = "Other fermented alcohol by volume"
    unit = "/1"
    quantity_type = STOCK

    def formula(household, period, parameters):
        return parameters(period).household.consumption.alcohol.other_fermented_abv
