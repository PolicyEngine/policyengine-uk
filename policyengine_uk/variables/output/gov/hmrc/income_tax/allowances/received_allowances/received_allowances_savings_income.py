from policyengine_uk.model_api import *


class received_allowances_savings_income(Variable):
    value_type = float
    entity = Person
    label = "The portion of all allowances (minus those only applicable to one income type) calculated after earned taxable income, but before dividends. This is applied to savings interest income."
    unit = GBP
    definition_period = YEAR
    reference = "Income Tax Act 2007 s. 35"

    def formula(person, period, parameters):
        all_allowances = person("allowances", period)
        received_allowances_earned_income = person(
            "received_allowances_earned_income", period
        )
        remaining_allowance = (
            all_allowances - received_allowances_earned_income
        )

        savings_income = person("taxable_savings_interest_income", period)

        return where(
            savings_income < remaining_allowance,
            max_(0, savings_income),
            max_(0, remaining_allowance),
        )
