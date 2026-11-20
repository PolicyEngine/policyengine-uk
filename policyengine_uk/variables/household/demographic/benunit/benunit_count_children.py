from policyengine_uk.model_api import *


class benunit_count_children(Variable):
    value_type = int
    entity = BenUnit
    label = "Members aged under 18 in the benefit unit (deprecated)"
    documentation = (
        "Deprecated: an age cut-off with no legal basis, kept only for "
        "downstream compatibility with its original formula. Nothing in "
        "policyengine-uk uses it. Use a count of the programme's own child definition, or of is_hbai_dependent_child for HBAI statistics instead."
    )
    definition_period = YEAR

    def formula(benunit, period, parameters):
        return add(benunit, period, ["is_child"])
