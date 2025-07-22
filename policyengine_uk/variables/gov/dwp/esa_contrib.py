from policyengine_uk.model_api import *


class esa_contrib(Variable):
    value_type = float
    entity = Person
    label = "ESA (contribution-based)"
    definition_period = YEAR
    unit = GBP

    adds = ["esa_contrib_reported"]
