from policyengine_uk.model_api import *


class other_residential_property_value(Variable):
    label = "other residence value"
    documentation = (
        "Current market value of residential property owned by the household "
        "other than the main residence, before sale expenses and secured debt. "
        "Universal Credit values this in the assessment year, assuming sale "
        "expenses and no additional Schedule "
        "10 disregards within this broad asset class that are not separately "
        "split out in the current dataset"
    )
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
    quantity_type = STOCK
    uprating = "gov.economic_assumptions.indices.obr.per_capita.gdp"
