from policyengine_uk.model_api import *


class num_adults(Variable):
    value_type = int
    entity = BenUnit
    label = "Members aged 18 or over in the benefit unit (deprecated)"
    documentation = (
        "Deprecated: an age cut-off with no legal basis, kept only for "
        "downstream compatibility with its original formula. Nothing in "
        "policyengine-uk uses it. Use a count of is_claimant_or_partner, or of is_hbai_adult for HBAI statistics instead."
    )
    definition_period = YEAR

    def formula(benunit, period, parameters):
        return benunit.sum(benunit.members("is_adult", period))
