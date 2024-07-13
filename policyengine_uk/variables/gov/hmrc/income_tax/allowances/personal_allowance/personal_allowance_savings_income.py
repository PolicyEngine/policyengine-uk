from policyengine_uk.model_api import *


class personal_allowance_savings_income(Variable):
    value_type = float
    entity = Person
    label = "The portion of the Personal Allowance calculated after earned taxable income, but before dividends. This is applied to savings interest income."
    unit = GBP
    definition_period = YEAR
    reference = "Income Tax Act 2007 s. 35"

    def formula(person, period, parameters):
        max_pa = person("personal_allowance_earned_taxable_income", period)

        income = person("taxable_savings_interest_income", period)

        return max_(0, max_pa - income)
