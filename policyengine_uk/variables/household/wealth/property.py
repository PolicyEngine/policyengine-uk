from policyengine_uk.model_api import *


class residential_property_value(Variable):
    label = "Residential property value"
    documentation = "Total value of all owned residential property"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
    quantity_type = STOCK

    def formula(household, period, parameters):
        return household("main_residence_value", period) + household(
            "other_residential_property_value", period
        )


class property_wealth(Variable):
    label = "Property wealth"
    documentation = "Total property wealth across all owned properties"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
    quantity_type = STOCK

    def formula(household, period):
        VARIABLES = [
            "residential_property_value",
            "non_residential_property_value",
        ]
        return add(household, period, VARIABLES)
