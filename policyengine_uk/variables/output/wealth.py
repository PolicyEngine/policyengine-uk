from policyengine_uk.model_api import *


class wealth(Variable):
    label = "wealth"
    documentation = "Wealth before taxes."
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP
    quantity_type = STOCK
    adds = [
        "financial_wealth",
        "property_wealth",
        "pension_wealth",
        "business_wealth",
        "physical_wealth",
    ]


class wealth_taxes(Variable):
    label = "wealth taxes"
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP
    quantity_type = FLOW


class property_wealth(Variable):
    label = "property wealth"
    documentation = "Value of all property."
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP
    quantity_type = STOCK
    adds = [
        "primary_residence_value",
        "other_residential_property_value",
        "land_only_wealth",
    ]


class financial_wealth(Variable):
    label = "financial wealth"
    documentation = "Value of all financial wealth owned by the household."
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP
    quantity_type = STOCK
    adds = [
        "financial_savings_and_investments",
    ]
    subtracts = [
        "mortgage_debt",
        "other_debt",
    ]


class savings(Variable):
    label = "savings"
    documentation = "Savings made this year."
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP
    quantity_type = FLOW
    adds = [
        "net_income",
    ]
    subtracts = [
        "net_consumption",
        "wealth_taxes",
        "employee_pension_contributions",
        "private_pension_contributions",
        "mortgage_capital_repayments",
    ]

class net_wealth(Variable):
    label = "net wealth"
    documentation = "Wealth after taxes."
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP
    quantity_type = STOCK
    adds = [
        "wealth",
    ]
    subtracts = [
        "wealth_taxes",
    ]