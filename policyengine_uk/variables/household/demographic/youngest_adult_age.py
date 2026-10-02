from policyengine_uk.model_api import *


class youngest_adult_age(Variable):
    value_type = float
    entity = BenUnit
    label = "Age of the youngest benefit-unit member aged 18 or over (deprecated)"
    documentation = (
        "Deprecated: an age cut-off with no legal basis, kept only for "
        "downstream compatibility with its original formula. Nothing in "
        "policyengine-uk uses it. Use youngest_claimant_or_partner_age instead."
    )
    definition_period = YEAR

    def formula(benunit, period, parameters):
        return benunit.min(
            where(
                benunit.members("is_adult", period),
                benunit.members("age", period),
                np.inf,
            )
        )
