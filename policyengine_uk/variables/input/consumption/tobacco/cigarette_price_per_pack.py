from policyengine_uk.model_api import *


class cigarette_price_per_pack(Variable):
    value_type = float
    entity = Household
    definition_period = YEAR
    label = "Retail price per pack of twenty cigarettes"
    unit = GBP
    quantity_type = STOCK

    def formula(household, period, parameters):
        return parameters(period).household.consumption.tobacco.price_per_pack
