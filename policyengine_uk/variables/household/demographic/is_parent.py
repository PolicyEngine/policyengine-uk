from policyengine_uk.model_api import *


class is_parent(Variable):
    value_type = bool
    entity = Person
    label = "Whether this person is a parent in their benefit unit"
    definition_period = YEAR
    default_value = False
