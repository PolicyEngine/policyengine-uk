from policyengine_uk.model_api import *


class additional_residential_property_purchased(Variable):
    label = "Residential property bought (additional)"
    documentation = "The price paid for the purchase of a residential property in the year, for use as a second home or another non-main-residence purpose. Only include the value of a single purchase."
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(household, period):
        property_purchased = household("property_purchased", period)
        other_residential_property_value = household(
            "other_residential_property_value", period
        )
        return other_residential_property_value * property_purchased
