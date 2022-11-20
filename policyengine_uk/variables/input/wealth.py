from policyengine_uk.model_api import *

label = "Wealth"
description = "Wealth held by households."

class corporate_wealth(Variable):
    label = "Corporate wealth"
    documentation = "Total owned wealth in corporations"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
    quantity_type = STOCK

class owned_land(Variable):
    entity = Household
    label = "Owned land"
    documentation = "Total value of all land-only plots owned by the household"
    unit = GBP
    definition_period = YEAR
    value_type = float
    quantity_type = STOCK


class main_residence_value(Variable):
    label = "Main residence value"
    documentation = "Total value of the main residence"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
    quantity_type = STOCK


class other_residential_property_value(Variable):
    label = "Other residence value"
    documentation = (
        "Total value of all residential property owned by the household"
    )
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
    quantity_type = STOCK



class non_residential_property_value(Variable):
    label = "Non-residential property value"
    documentation = (
        "Total value of all non-residential property owned by the household"
    )
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
    quantity_type = STOCK
