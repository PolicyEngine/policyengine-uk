from policyengine_uk.model_api import *


class raw_person_weight(Variable):
    value_type = float
    entity = Person
    label = "Weight factor"
    documentation = "Used to translate from survey respondents to UK residents"
    definition_period = YEAR
    default_value = 1
