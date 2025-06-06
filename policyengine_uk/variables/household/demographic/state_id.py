from policyengine_uk.model_api import *


class state_id(Variable):
    label = "State ID"
    documentation = "Identity of the state"
    entity = State
    definition_period = YEAR
    value_type = int
