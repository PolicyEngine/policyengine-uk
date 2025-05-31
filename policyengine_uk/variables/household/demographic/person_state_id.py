from policyengine_uk.model_api import *


class person_state_id(Variable):
    label = "State ID"
    documentation = "Identity of the state"
    entity = Person
    definition_period = YEAR
    value_type = int
