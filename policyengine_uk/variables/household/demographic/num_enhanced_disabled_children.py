from policyengine_uk.model_api import *


class num_enhanced_disabled_children(Variable):
    value_type = int
    entity = BenUnit
    label = "Number of enhanced disabled children"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        child = benunit.members("is_child_or_QYP", period)
        enhanced_disabled = benunit.members(
            "is_enhanced_disabled_for_benefits", period
        )
        return benunit.sum(child & enhanced_disabled)
