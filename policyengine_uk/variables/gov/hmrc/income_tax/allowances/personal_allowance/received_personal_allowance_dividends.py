from policyengine_uk.model_api import *


class received_personal_allowance_dividends(Variable):
    value_type = float
    entity = Person
    label = "The portion of the Personal Allowance calculated last, applied to dividends."
    unit = GBP
    definition_period = YEAR
    reference = "Income Tax Act 2007 s. 35"

    def formula(person, period, parameters):
        pa_max_value = person("personal_allowance", period)
        pa_earned_income = person(
            "received_personal_allowance_earned_income", period
        )
        pa_savings_income = person("received_personal_allowance_savings", period)
        pa_remaining = pa_max_value - pa_earned_income - pa_savings_income

        dividend_income = person("taxable_dividend_income", period)
        is_income_lesser = dividend_income < pa_remaining

        return where(
            is_income_lesser, max_(0, dividend_income), max_(0, pa_remaining)
        )