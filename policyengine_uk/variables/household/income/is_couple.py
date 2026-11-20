from policyengine_uk.model_api import *


class is_couple(Variable):
    value_type = bool
    entity = BenUnit
    label = "Claimant has a partner"
    documentation = "Whether the claimant is a member of a couple."
    definition_period = YEAR

    def formula(benunit, period, parameters):
        relation_type = benunit("relation_type", period)
        relations = relation_type.possible_values
        return relation_type == relations.COUPLE
