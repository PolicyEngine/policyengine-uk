from policyengine_uk.model_api import *


class financial_wealth(Variable):
    label = "financial wealth"
    documentation = "Value of all financial wealth owned by the household."
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP
    quantity_type = STOCK
    adds = [
        "financial_savings",
    ]
    subtracts = [
        "mortgage_debt",
        "other_debt",
    ]

class mortgage_debt(Variable):
    label = "mortgage debt"
    documentation = "Outstanding mortgage debt."
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP
    quantity_type = STOCK

class other_debt(Variable):
    label = "non-mortgage debt"
    documentation = "Non-mortgage debt."
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP
    quantity_type = STOCK

class financial_savings_and_investments(Variable):
    label = "financial savings and investments"
    documentation = "Bank or building society current or savings accounts, ISAs, endowments, stocks and shares, and informal savings. Excludes ownership of business assets where this person is self-employed, a director or partner."
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP
    quantity_type = FLOW

