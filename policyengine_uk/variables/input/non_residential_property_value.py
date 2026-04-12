from policyengine_uk.model_api import *


class non_residential_property_value(Variable):
    label = "non-residential property value"
    documentation = (
        "Total value of non-residential property owned by the household, before "
        "any additional Universal Credit Schedule 10 disregards within this "
        "broad asset class that are not separately split out in the current "
        "dataset"
    )
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
    quantity_type = STOCK
    uprating = "gov.economic_assumptions.indices.obr.per_capita.gdp"
