from policyengine_uk.model_api import *


class total_pension_income(Variable):
    label = "Total pension income"
    documentation = "Private, personal and State Pension income"
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP

    adds = ["private_pension_income", "state_pension"]
