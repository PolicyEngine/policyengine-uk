from policyengine_uk.model_api import *


class role(Variable):
    value_type = str
    label = "Role (adult/child)"
    entity = Person
    definition_period = YEAR
