from policyengine_uk.model_api import *


class person_benunit_id(Variable):
    value_type = float
    label = "Person's benefit unit ID"
    entity = Person
    definition_period = YEAR
