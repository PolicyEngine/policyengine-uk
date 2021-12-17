from openfisca_uk.model_api import *


class state_id(Variable):
    label = "State ID"
    documentation = "Identity of the state"
    entity = State
    definition_period = ETERNITY
    value_type = int


class state_weight(Variable):
    label = "State weight"
    documentation = "Weight value"
    entity = State
    definition_period = ETERNITY
    value_type = float
