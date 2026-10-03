from policyengine_uk.model_api import *


class num_disabled_children(Variable):
    value_type = int
    entity = BenUnit
    label = "Disabled benefit-unit members under 18 (deprecated)"
    documentation = (
        "Deprecated: an age cut-off with no legal basis, kept only for "
        "downstream compatibility with its original formula. Nothing in "
        "policyengine-uk uses it. Use a count over the programme's own child definition instead."
    )
    definition_period = YEAR

    def formula(benunit, period, parameters):
        child = benunit.members("is_child", period)
        disabled = benunit.members("is_disabled_for_benefits", period)
        return benunit.sum(child & disabled)
