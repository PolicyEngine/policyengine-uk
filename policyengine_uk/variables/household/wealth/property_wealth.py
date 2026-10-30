from policyengine_uk.model_api import *


class property_wealth(Variable):
    label = "Property wealth"
    documentation = (
        "Worldwide gross value of all owned property, including direct UK "
        "land, overseas land and property, and unclassified other real estate. "
        "Sale expenses and secured debt are considered separately when "
        "valuing countable benefit capital."
    )
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
    quantity_type = STOCK
    adds = [
        "residential_property_value",
        "non_residential_property_value",
        "owned_land",
        "overseas_property_value",
        "other_property_value",
    ]
