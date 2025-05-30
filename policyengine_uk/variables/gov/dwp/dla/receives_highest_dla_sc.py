from policyengine_uk.model_api import *


class receives_highest_dla_sc(Variable):
    label = "Receives the highest DLA (self-care) category"
    entity = Person
    definition_period = YEAR
    value_type = bool

    def formula(person, period, parameters):
        category = person("dla_sc_category", period)
        return category == category.possible_values.HIGHER
