from policyengine_uk.model_api import *


class taxable_self_employment_income(Variable):
    value_type = float
    entity = Person
    label = "Amount of trading income that is taxable"
    definition_period = YEAR
    reference = "Income Tax (Trading and Other Income) Act 2005 s. 5"
    unit = GBP

    def formula(person, period, parameters):
        self_employment_income = person("self_employment_income", period)
        DEDUCTIONS = ["loss_relief", "capital_allowances", "trading_allowance"]
        deductions = add(person, period, DEDUCTIONS)
        return max_(0, self_employment_income - deductions)
