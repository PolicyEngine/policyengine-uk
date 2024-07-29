from policyengine_uk.model_api import *


class received_allowances_earned_income(Variable):
    value_type = float
    entity = Person
    label = "The portion of all allowances (minus those only applicable to certain types of income) that is applied to earned income"
    unit = GBP
    definition_period = YEAR
    reference = "Income Tax Act 2007 s. 35"

    def formula(person, period, parameters):
        # This portion of all allowances, applied first, excludes savings and dividends

        all_allowances = person("allowances", period)

        all_income = person("adjusted_net_income", period)
        excluded_income = person(
            "taxable_savings_interest_income", period
        ) + person("taxable_dividend_income", period)
        earned_income = all_income - excluded_income

        return where(
            earned_income < all_allowances,
            max_(0, earned_income),
            all_allowances,
        )
