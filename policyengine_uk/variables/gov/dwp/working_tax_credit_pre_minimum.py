from policyengine_uk.model_api import *


class working_tax_credit_pre_minimum(Variable):
    value_type = float
    entity = BenUnit
    label = "Working Tax Credit pre-minimum"
    documentation = (
        "Working Tax Credit amount before the minimum tax credit is applied"
    )
    defined_for = "would_claim_WTC"
    definition_period = YEAR
    unit = GBP

    def formula(benunit, period, parameters):
        return max_(
            0,
            benunit("WTC_maximum_rate", period)
            - benunit("tax_credits_reduction", period),
        )
