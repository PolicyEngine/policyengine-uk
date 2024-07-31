from policyengine_uk.model_api import *


class mortgage_debt(Variable):
    label = "mortgage debt"
    documentation = "Outstanding mortgage debt."
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP
    quantity_type = STOCK

    def formula(person, period, parameters):
        if person.has_any_input("mortgage_debt"):
            debt_last_year = person("mortgage_debt", period.last_year)
            repayment_last_year = person(
                "mortgage_capital_repayments", period.last_year
            )
            return debt_last_year - repayment_last_year


class mortgage_capital_repayments(Variable):
    label = "mortgage capital repayments"
    documentation = "Payments made to reduce the outstanding mortgage debt."
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP
    quantity_type = FLOW


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
    quantity_type = STOCK

    def formula(person, period, parameters):
        if period.start > person.simulation.start_instant:
            return person("financial_savings_and_investments", period.last_year) + person("savings", period.last_year)