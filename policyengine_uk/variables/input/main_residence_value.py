from policyengine_uk.model_api import *


class main_residence_value(Variable):
    label = "main residence value"
    documentation = "Total value of the main residence"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
    quantity_type = STOCK
    uprating = "gov.economic_assumptions.indices.obr.per_capita.gdp"
