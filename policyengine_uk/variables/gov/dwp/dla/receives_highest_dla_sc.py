from policyengine_uk.model_api import *
from policyengine_uk.variables.misc.categories.lower_middle_or_higher import (

class receives_highest_dla_sc(Variable):
    label = "Receives the highest DLA (self-care) category"
    entity = Person
    definition_period = YEAR
    value_type = bool

    def formula(person, period, parameters):
        return person("dla_sc_category", period) == LowerMiddleOrHigher.HIGHER
