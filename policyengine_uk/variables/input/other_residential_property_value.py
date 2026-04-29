from policyengine_uk.model_api import *


class other_residential_property_value(Variable):
    label = "other residence value"
    documentation = (
        "Total value of residential property owned by the household other than "
        "the main residence, before any additional Universal Credit Schedule "
        "10 disregards within this broad asset class that are not separately "
        "split out in the current dataset"
    )
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
    quantity_type = STOCK
    uprating = "gov.economic_assumptions.indices.obr.per_capita.gdp"
