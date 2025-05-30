from policyengine_uk.model_api import *


class num_adults(Variable):
    value_type = int
    entity = BenUnit
    label = "The number of adults in the family"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        return benunit.sum(benunit.members("is_adult", period))
