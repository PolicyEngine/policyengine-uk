from policyengine_uk.model_api import *


class is_blind(Variable):
    label = "Blind"
    documentation = "Certified as blind or severely sight impaired by a consultant ophthalmologist"
    entity = Person
    definition_period = YEAR
    value_type = bool
