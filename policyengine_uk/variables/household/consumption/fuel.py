from policyengine_uk.model_api import *


class petrol_litres(Variable):
    label = "Petrol volume"
    documentation = "Total litres of petrol bought"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(household, period, parameters):
        return household("petrol_spending", period) / household(
            "petrol_price", period
        )


class diesel_litres(Variable):
    label = "Diesel volume"
    documentation = "Total litres of diesel bought"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(household, period, parameters):
        return household("diesel_spending", period) / household(
            "diesel_price", period
        )


class petrol_price(Variable):
    label = "Price of petrol per litre"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(household, period, parameters):
        return parameters(period).household.consumption.fuel.prices.petrol


class diesel_price(Variable):
    label = "Price of diesel per litre"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(household, period, parameters):
        return parameters(period).household.consumption.fuel.prices.petrol
