from policyengine_uk.model_api import *


class families(Variable):
    value_type = float
    entity = BenUnit
    label = "Variable holding families"
    definition_period = YEAR
    default_value = 1
