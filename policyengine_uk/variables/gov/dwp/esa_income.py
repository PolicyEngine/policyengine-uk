from policyengine_uk.model_api import *


class esa_income(Variable):
    value_type = float
    entity = BenUnit
    label = "ESA (income-based)"
    documentation = "Employment and Support Allowance"
    definition_period = YEAR
    unit = GBP

    adds = ["esa_income_reported"]
