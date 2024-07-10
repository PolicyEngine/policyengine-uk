from policyengine_uk.model_api import *


class employment_deductions(Variable):
    value_type = float
    entity = Person
    label = "Deductions from employment income"
    definition_period = YEAR
    reference = "Income Tax Act (Earnings and Pensions) Act 2003 s. 327"
    unit = GBP

    adds = ["employment_expenses"]
