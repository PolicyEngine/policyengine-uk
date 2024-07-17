from policyengine_uk.model_api import *


class received_dividend_allowance(Variable):
    value_type = float
    entity = Person
    label = "Total Dividend Allowance received by individual, after Personal Allowance"
    definition_period = YEAR
    reference = "Income Tax Act 2007 s. 13A"
    unit = GBP

    def formula(person, period, parameters):
        dividend_income = person("taxable_dividend_income", period)
        max_dividend_allowance = person("dividend_allowance", period)
        personal_allowance_dividends = person(
            "received_personal_allowance_dividends", period
        )

        remaining_taxable_dividends = (
            dividend_income - personal_allowance_dividends
        )

        return where(
            remaining_taxable_dividends > max_dividend_allowance,
            max_dividend_allowance,
            remaining_taxable_dividends,
        )
