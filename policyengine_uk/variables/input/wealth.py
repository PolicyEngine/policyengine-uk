from policyengine_uk.model_api import *

label = "Wealth"
description = "Wealth held by households."


class corporate_wealth(Variable):
    label = "corporate wealth"
    documentation = "Total owned wealth in corporations"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
    quantity_type = STOCK


class owned_land(Variable):
    entity = Household
    label = "owned land value"
    documentation = "Total value of all land-only plots owned by the household"
    unit = GBP
    definition_period = YEAR
    value_type = float
    quantity_type = STOCK


class main_residence_value(Variable):
    label = "main residence value"
    documentation = "Total value of the main residence"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
    quantity_type = STOCK


class other_residential_property_value(Variable):
    label = "other residence value"
    documentation = (
        "Total value of all residential property owned by the household"
    )
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
    quantity_type = STOCK


class non_residential_property_value(Variable):
    label = "non-residential property value"
    documentation = (
        "Total value of all non-residential property owned by the household"
    )
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
    quantity_type = STOCK
