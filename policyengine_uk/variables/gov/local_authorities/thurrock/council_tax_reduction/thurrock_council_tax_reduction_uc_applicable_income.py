from policyengine_uk.model_api import *


class thurrock_council_tax_reduction_uc_applicable_income(Variable):
    value_type = float
    entity = BenUnit
    label = "Thurrock Council Tax Reduction Universal Credit applicable income"
    definition_period = YEAR
    unit = GBP
    reference = "https://thurrock.moderngov.co.uk/documents/s51034/Enc.%201%20for%20Local%20Council%20Tax%20Support%20Scheme%202026-27.pdf"

    def formula(benunit, period, parameters):
        ctr = parameters(period).gov.local_authorities.thurrock.council_tax_reduction
        has_uc_award = benunit("universal_credit", period) > 0
        earned_income = max_(
            0,
            benunit("uc_earned_income", period)
            - ctr.earnings_disregard.amount * WEEKS_IN_YEAR,
        )
        unearned_income = max_(
            0,
            benunit("uc_unearned_income", period)
            - benunit(
                "thurrock_council_tax_reduction_source_disregarded_income", period
            ),
        )
        uc_award = benunit("universal_credit", period)
        return has_uc_award * (earned_income + unearned_income + uc_award)
