from policyengine_uk.model_api import *


class person_household_id(Variable):
    value_type = int
    label = "Person's household ID"
    entity = Person
    definition_period = YEAR
