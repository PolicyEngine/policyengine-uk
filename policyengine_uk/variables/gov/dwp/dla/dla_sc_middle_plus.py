from policyengine_uk.model_api import *


class dla_sc_middle_plus(Variable):
    value_type = bool
    entity = Person
    label = "Receives at least middle-rate DLA (self-care)"
    definition_period = YEAR

    def formula(person, period, parameters):
        category = person("dla_sc_category", period)
        categories = category.possible_values
        return is_in(
            category,
            [categories.MIDDLE, categories.HIGHER],
        )
