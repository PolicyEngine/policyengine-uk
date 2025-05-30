from policyengine_uk.model_api import *


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
    uprating = "household.wealth.financial_assets"
