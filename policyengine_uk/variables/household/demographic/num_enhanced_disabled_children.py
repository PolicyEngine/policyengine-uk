from policyengine_uk.model_api import *


class num_enhanced_disabled_children(Variable):
    value_type = int
    entity = BenUnit
    label = "Enhanced-disabled benefit-unit members under 18 (deprecated)"
    documentation = (
        "Deprecated: an age cut-off with no legal basis, kept only for "
        "downstream compatibility with its original formula. Nothing in "
        "policyengine-uk uses it. Use a count over the programme's own child definition instead."
    )
    definition_period = YEAR

    def formula(benunit, period, parameters):
        child = benunit.members("is_child", period)
        enhanced_disabled = benunit.members("is_enhanced_disabled_for_benefits", period)
        return benunit.sum(child & enhanced_disabled)
