from policyengine_uk.model_api import *


class state_id(Variable):
    label = "State ID"
    documentation = "Identity of the state"
    entity = State
    definition_period = YEAR
    value_type = int


class person_state_id(Variable):
    label = "State ID"
    documentation = "Identity of the state"
    entity = Person
    definition_period = YEAR
    value_type = int


class person_state_role(Variable):
    label = "State role"
    entity = Person
    definition_period = YEAR
    value_type = str


class state_weight(Variable):
    label = "State weight"
    documentation = "Weight value"
    entity = State
    definition_period = YEAR
    value_type = float
