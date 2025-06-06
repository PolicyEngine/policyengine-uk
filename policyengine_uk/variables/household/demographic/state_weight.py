from policyengine_uk.model_api import *


class state_weight(Variable):
    label = "State weight"
    documentation = "Weight value"
    entity = State
    definition_period = YEAR
    value_type = float
