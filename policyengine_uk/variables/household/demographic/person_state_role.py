from policyengine_uk.model_api import *


class person_state_role(Variable):
    label = "State role"
    entity = Person
    definition_period = YEAR
    value_type = str
