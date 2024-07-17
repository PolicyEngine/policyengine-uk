from policyengine_uk.model_api import *


class received_personal_allowance_savings(Variable):
    value_type = float
    entity = Person
    label = "The portion of the Personal Allowance calculated after earned taxable income, but before dividends. This is applied to savings interest income."
    unit = GBP
    definition_period = YEAR
    reference = "Income Tax Act 2007 s. 35"

    def formula(person, period, parameters):
        pa_max_value = person("personal_allowance", period)
        pa_earned_income = person(
            "received_personal_allowance_earned_income", period
        )
        pa_remaining = pa_max_value - pa_earned_income

        savings_income = person("taxable_savings_interest_income", period)
        is_income_lesser = savings_income < pa_remaining

        return where(
            is_income_lesser, max_(0, savings_income), max_(0, pa_remaining)
        )
