from policyengine_uk.model_api import *


class num_severely_disabled_adults(Variable):
    value_type = int
    entity = BenUnit
    label = "Severely disabled benefit-unit members aged 18 or over (deprecated)"
    documentation = (
        "Deprecated: an age cut-off with no legal basis, kept only for "
        "downstream compatibility with its original formula. Nothing in "
        "policyengine-uk uses it. Use a count over is_claimant_or_partner instead."
    )
    definition_period = YEAR

    def formula(benunit, period, parameters):
        adult = benunit.members("is_adult", period)
        severely_disabled = benunit.members("is_severely_disabled_for_benefits", period)
        return benunit.sum(adult & severely_disabled)
