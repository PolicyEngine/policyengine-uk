from policyengine_uk.model_api import *


class received_personal_allowance_earned_income(Variable):
    value_type = float
    entity = Person
    label = "The portion of the Personal Allowance calculatd first, which is applied to earned taxable income, not savings or dividends"
    unit = GBP
    definition_period = YEAR
    reference = "Income Tax Act 2007 s. 35"

    def formula(person, period, parameters):
        # This portion of the Personal Allowance, applied first, excludes savings and dividends
        # earned_taxable_income subtracts calculated allowances, hence why this variable
        # instead uses adjusted_net_income, then subtracts savings and dividends
        max_pa = person("personal_allowance", period)

        all_income = person("adjusted_net_income", period)
        excluded_income = person(
            "taxable_savings_interest_income", period
        ) + person("taxable_dividend_income", period)
        earned_income = all_income - excluded_income

        return where(earned_income < max_pa, earned_income, max_pa)
