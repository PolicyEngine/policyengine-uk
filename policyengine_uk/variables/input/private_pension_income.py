from policyengine_uk.model_api import *


class private_pension_income(Variable):
    value_type = float
    entity = Person
    label = "pension income"
    documentation = "Income from private or occupational pensions (not including the State Pension)"
    definition_period = YEAR
    unit = GBP
    reference = "Income Tax (Earnings and Pensions) Act 2003 s. 1(1)(b)"
    quantity_type = FLOW
    uprating = "gov.economic_assumptions.indices.obr.private_pension_index"
