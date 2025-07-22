from policyengine_uk.model_api import *


class property_wealth(Variable):
    label = "Property wealth"
    documentation = "Total property wealth across all owned properties"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
    quantity_type = STOCK
    adds = ["residential_property_value", "non_residential_property_value"]
