from policyengine_uk.model_api import *


class owned_land(Variable):
    entity = Household
    label = "owned land value"
    documentation = "Total value of all land-only plots owned by the household"
    unit = GBP
    definition_period = YEAR
    value_type = float
    quantity_type = STOCK
    uprating = "gov.economic_assumptions.indices.obr.per_capita.gdp"
