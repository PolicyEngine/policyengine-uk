from policyengine_uk.model_api import *


class is_single_person(Variable):
    value_type = bool
    entity = BenUnit
    label = "Whether the family is a single person"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        family_type = benunit("family_type", period)
        families = family_type.possible_values
        return family_type == families.SINGLE
