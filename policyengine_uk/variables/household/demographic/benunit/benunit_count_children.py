from policyengine_uk.model_api import *


class benunit_count_children(Variable):
    value_type = int
    entity = BenUnit
    label = "number of children in the benefit unit"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        return add(benunit, period, ["is_child"])
