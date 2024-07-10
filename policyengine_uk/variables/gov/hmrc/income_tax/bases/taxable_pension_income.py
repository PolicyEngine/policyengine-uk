from policyengine_uk.model_api import *


class taxable_pension_income(Variable):
    value_type = float
    entity = Person
    label = "Amount of pension income that is taxable"
    definition_period = YEAR
    reference = "Income Tax (Earnings and Pensions) Act 2003 s. 567"
    unit = GBP

    adds = ["pension_income"]
