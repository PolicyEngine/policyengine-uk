from policyengine_uk.model_api import *


class benunit_count_adults(Variable):
    value_type = int
    entity = BenUnit
    label = "number of adults in the benefit unit"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        return add(benunit, period, ["is_adult"])
