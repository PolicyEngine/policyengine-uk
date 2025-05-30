from policyengine_uk.model_api import *


class person_benunit_role(Variable):
    value_type = str
    label = "Role (adult/child)"
    entity = Person
    definition_period = YEAR
