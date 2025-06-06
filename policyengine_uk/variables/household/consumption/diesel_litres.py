from policyengine_uk.model_api import *


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
