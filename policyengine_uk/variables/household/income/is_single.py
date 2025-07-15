from policyengine_uk.model_api import *


class is_single(Variable):
    value_type = bool
    entity = BenUnit
    label = "Whether this benefit unit contains a single claimant for benefits"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        relation_type = benunit("relation_type", period)
        relations = relation_type.possible_values
        return relation_type == relations.SINGLE
