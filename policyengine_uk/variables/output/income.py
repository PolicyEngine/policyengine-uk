from policyengine_uk.model_api import *


class market_income(Variable):
    label = "market income"
    documentation = "Gross income from non-government sources."
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP
    quantity_type = FLOW
    adds = [
        "employment_income",
        "self_employment_income",
        "private_pension_income",
        "rental_income",
        "dividend_income",
        "interest_income",
        "other_income",
        "employer_pension_contributions",
    ]


class income_taxes(Variable):
    label = "income taxes"
    documentation = "Taxes levied on income."
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP
    quantity_type = FLOW


class net_income(Variable):
    label = "net income"
    documentation = "Market income plus government benefits, less taxes."
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP
    quantity_type = FLOW
    adds = [
        "market_income",
    ]
    subtracts = [
        "income_taxes",
    ]
