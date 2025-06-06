from policyengine_uk.model_api import *


class mortgage(Variable):
    value_type = float
    entity = Household
    label = "total mortgage payments"
    documentation: str = "Total amount spent on mortgage payments"
    definition_period = YEAR
    unit = GBP
    adds = [
        "mortgage_interest_repayment",
        "mortgage_capital_repayment",
    ]
