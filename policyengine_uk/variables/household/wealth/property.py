from policyengine_uk.model_api import *


class residential_property_value(Variable):
    label = "Residential property value"
    documentation = "Total value of all owned residential property"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
    quantity_type = STOCK

    adds = ["main_residence_value", "other_residential_property_value"]


class property_wealth(Variable):
    label = "Property wealth"
    documentation = "Total property wealth across all owned properties"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
    quantity_type = STOCK

    adds = ["residential_property_value", "non_residential_property_value"]
