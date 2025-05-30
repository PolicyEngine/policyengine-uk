from policyengine_uk.model_api import *


class num_severely_disabled_children(Variable):
    value_type = int
    entity = BenUnit
    label = "Number of severely disabled children"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        child = benunit.members("is_child_or_QYP", period)
        severely_disabled = benunit.members(
            "is_severely_disabled_for_benefits", period
        )
        return benunit.sum(child & severely_disabled)
