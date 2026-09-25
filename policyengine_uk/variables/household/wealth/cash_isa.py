from policyengine_uk.model_api import *


class cash_isa(Variable):
    label = "cash ISA holdings"
    documentation = "Amount held in cash Individual Savings Accounts"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
    uprating = "gov.economic_assumptions.indices.obr.per_capita.gdp"
    quantity_type = STOCK
