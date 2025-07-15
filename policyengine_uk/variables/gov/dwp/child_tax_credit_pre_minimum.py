from policyengine_uk.model_api import *


class child_tax_credit_pre_minimum(Variable):
    value_type = float
    entity = BenUnit
    label = "Child Tax Credit pre-minimum"
    documentation = (
        "Child Tax Credit amount before the minimum tax credit is applied"
    )
    defined_for = "would_claim_ctc"
    definition_period = YEAR
    unit = GBP

    def formula(benunit, period, parameters):
        reduction_left = max_(
            0,
            benunit("tax_credits_reduction", period)
            - benunit("wtc_maximum_rate", period),
        )
        return max_(
            0,
            benunit("ctc_maximum_rate", period) - reduction_left,
        )
