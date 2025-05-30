from policyengine_uk.model_api import *


class other_deductions(Variable):
    value_type = float
    entity = Person
    label = "All other tax deductions"
    definition_period = YEAR
    unit = GBP
