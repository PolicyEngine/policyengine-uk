from policyengine_uk.model_api import *


class main_residential_property_purchased(Variable):
    label = "Residential property bought (main)"
    documentation = "The price paid for the purchase of a residential property in the year, for use as a main residence. Only include the value of a single purchase."
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(household, period):
        property_purchased = household("property_purchased", period)
        main_residence_value = household("main_residence_value", period)
        return main_residence_value * property_purchased
