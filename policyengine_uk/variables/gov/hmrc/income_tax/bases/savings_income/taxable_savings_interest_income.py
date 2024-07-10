from policyengine_uk.model_api import *


class taxable_savings_interest_income(Variable):
    value_type = float
    entity = Person
    label = "Amount of savings interest which is taxable"
    definition_period = YEAR
    reference = "Income Tax Act (Trading and Other Income) 2005 s. 369"
    unit = GBP

    def formula(person, period, parameters):
        total_interest = person("savings_interest_income", period)
        exempt_interest = person("tax_free_savings_income", period)
        return max_(0, total_interest - exempt_interest)
