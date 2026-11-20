from policyengine_uk.model_api import *


class youngest_child_age(Variable):
    value_type = float
    entity = BenUnit
    label = "Age of the youngest benefit-unit member under 18 (deprecated)"
    documentation = (
        "Deprecated: an age cut-off with no legal basis, kept only for "
        "downstream compatibility with its original formula. Nothing in "
        "policyengine-uk uses it. Use the programme's own child definition instead."
    )
    definition_period = YEAR

    def formula(benunit, period, parameters):
        return benunit.min(
            where(
                benunit.members("is_child", period),
                benunit.members("age", period),
                np.inf,
            )
        )
