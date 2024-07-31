from policyengine_uk.model_api import *


class other_income(Variable):
    label = "other income"
    documentation = "Income not elsewhere classified."
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP
    quantity_type = FLOW
