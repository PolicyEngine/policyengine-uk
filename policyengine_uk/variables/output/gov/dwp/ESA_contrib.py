from policyengine_uk.model_api import *


class ESA_contrib(Variable):
    value_type = float
    entity = Person
    label = "ESA (contribution-based)"
    definition_period = YEAR
    unit = GBP

    adds = ["ESA_contrib_reported"]


class ESA_contrib_reported(Variable):
    value_type = float
    entity = Person
    label = "Employment and Support Allowance (contribution-based) (reported)"
    definition_period = YEAR
    unit = GBP
