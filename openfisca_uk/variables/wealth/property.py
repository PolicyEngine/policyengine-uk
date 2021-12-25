from openfisca_uk.model_api import *


class main_residence_value(Variable):
    label = "Main residence value"
    documentation = "Total value of the main residence"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = "currency-GBP"


class other_residential_property_value(Variable):
    label = "Other residence value"
    documentation = (
        "Total value of all residential property owned by the household"
    )
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = "currency-GBP"


class residential_property_value(Variable):
    label = "Residential property value"
    documentation = "Total value of all owned residential property"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = "currency-GBP"

    def formula(household, period, parameters):
        return household("main_residence_value", period) + household(
            "other_residential_property_value", period
        )


class non_residential_property_value(Variable):
    label = "Non-residential property value"
    documentation = (
        "Total value of all non-residential property owned by the household"
    )
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = "currency-GBP"


class property_wealth(Variable):
    label = "Property wealth"
    documentation = "Total property wealth across all owned properties"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = "currency-GBP"

    def formula(household, period):
        VARIABLES = [
            "residential_property_value",
            "non_residential_property_value",
        ]
        return add(household, period, VARIABLES)
