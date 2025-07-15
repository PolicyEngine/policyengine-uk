from policyengine_uk.model_api import *


class num_children(Variable):
    value_type = int
    entity = BenUnit
    label = "The number of children in the family"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        return benunit.sum(benunit.members("is_child", period))
