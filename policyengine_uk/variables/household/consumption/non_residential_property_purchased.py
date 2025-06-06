from policyengine_uk.model_api import *


class non_residential_property_purchased(Variable):
    label = "Non-residential property bought"
    documentation = "The price paid for the purchase of a non-residential property in the year. Only include the value of a single purchase."
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
    defined_for = "property_purchased"
    adds = ["non_residential_property_value"]
