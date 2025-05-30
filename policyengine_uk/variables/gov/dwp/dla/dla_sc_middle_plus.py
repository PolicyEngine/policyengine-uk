from policyengine_uk.model_api import *
from policyengine_uk.variables.misc.categories.lower_middle_or_higher import (

class dla_sc_middle_plus(Variable):
    value_type = bool
    entity = Person
    label = "Receives at least middle-rate DLA (self-care)"
    definition_period = YEAR

    def formula(person, period, parameters):
        return is_in(
            person("dla_sc_category", period),
            [LowerMiddleOrHigher.MIDDLE, LowerMiddleOrHigher.HIGHER],
        )
