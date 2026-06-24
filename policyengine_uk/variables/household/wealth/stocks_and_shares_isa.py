from policyengine_uk.model_api import *


class stocks_and_shares_isa(Variable):
    label = "stocks and shares ISA holdings"
    documentation = (
        "Amount held in stocks and shares (investment) Individual Savings "
        "Accounts"
    )
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
    uprating = "gov.economic_assumptions.indices.obr.per_capita.gdp"
    quantity_type = STOCK
