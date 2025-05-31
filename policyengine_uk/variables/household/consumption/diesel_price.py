from policyengine_uk.model_api import *


class diesel_price(Variable):
    label = "Price of diesel per litre"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(household, period, parameters):
        return parameters(period).household.consumption.fuel.prices.diesel
