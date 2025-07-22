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
