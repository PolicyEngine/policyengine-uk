from policyengine_uk.model_api import *


class beer_abv(Variable):
    value_type = float
    entity = Household
    definition_period = YEAR
    label = "Beer alcohol by volume"
    unit = "/1"
    quantity_type = STOCK

    def formula(household, period, parameters):
        return parameters(period).household.consumption.alcohol.beer_abv
