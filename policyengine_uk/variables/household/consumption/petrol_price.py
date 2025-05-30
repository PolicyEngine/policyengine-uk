from policyengine_uk.model_api import *


class petrol_price(Variable):
    label = "Price of petrol per litre"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(household, period, parameters):
        return parameters(period).household.consumption.fuel.prices.petrol
