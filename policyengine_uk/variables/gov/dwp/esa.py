from policyengine_uk.model_api import *


class esa(Variable):
    label = "ESA"
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP
    adds = ["esa_contrib", "esa_income"]
