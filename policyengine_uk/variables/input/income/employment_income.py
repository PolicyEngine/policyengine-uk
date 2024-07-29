from policyengine_uk.model_api import *


class employment_income(Variable):
    label = "employment income"
    documentation = "Gross pay from employment, before any deductions."
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP
    quantity_type = FLOW
