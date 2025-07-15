from policyengine_uk.model_api import *


class is_lone_parent(Variable):
    value_type = bool
    entity = BenUnit
    label = "Whether the family is a lone parent family"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        family_type = benunit("family_type", period)
        families = family_type.possible_values
        return family_type == families.LONE_PARENT
