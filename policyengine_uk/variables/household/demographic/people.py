from policyengine_uk.model_api import *


class people(Variable):
    value_type = float
    entity = Person
    label = "Variable holding people"
    definition_period = YEAR
    default_value = 1
