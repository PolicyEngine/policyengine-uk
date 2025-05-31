from policyengine_uk.model_api import *


class jsa_contrib(Variable):
    value_type = float
    entity = Person
    label = "JSA (contribution-based)"
    definition_period = YEAR
    unit = GBP

    adds = ["jsa_contrib_reported"]
