from policyengine_uk.model_api import *


class private_pension_income(Variable):
    label = "private pension income"
    documentation = "Income from personal or occupational pensions (not including the State Pension)."
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP
    quantity_type = FLOW
