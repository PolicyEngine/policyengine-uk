from policyengine_uk.model_api import *


class is_single(Variable):
    value_type = bool
    entity = BenUnit
    label = "Claimant has no partner"
    documentation = "Whether the claimant is not a member of a couple."
    definition_period = YEAR

    def formula(benunit, period, parameters):
        relation_type = benunit("relation_type", period)
        relations = relation_type.possible_values
        return relation_type == relations.SINGLE
