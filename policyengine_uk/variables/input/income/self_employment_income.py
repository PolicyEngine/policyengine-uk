from policyengine_uk.model_api import *


class self_employment_income(Variable):
    label = "self-employment income"
    documentation = "Income from business profits, net of business expenses."
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP
    quantity_type = FLOW
