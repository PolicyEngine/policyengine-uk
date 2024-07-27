from policyengine_uk.model_api import *


class received_allowances_dividend_income(Variable):
    value_type = float
    entity = Person
    label = "The portion of all allowances (excluding those for a particular income type) calculated last, applied to dividends."
    unit = GBP
    definition_period = YEAR
    reference = "Income Tax Act 2007 s. 35"

    def formula(person, period, parameters):
        all_allowances = person("allowances", period)
        received_allowances_earned_income = person(
            "received_allowances_earned_income", period
        )
        received_allowances_savings_income = person(
            "received_allowances_savings_income", period
        )
        remaining_allowance = (
            all_allowances
            - received_allowances_earned_income
            - received_allowances_savings_income
        )

        dividend_income = person("taxable_dividend_income", period)

        return where(
            dividend_income < remaining_allowance,
            max_(0, dividend_income),
            max_(0, remaining_allowance),
        )
