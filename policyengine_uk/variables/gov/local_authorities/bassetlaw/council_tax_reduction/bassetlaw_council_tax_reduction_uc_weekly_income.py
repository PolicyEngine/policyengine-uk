from policyengine_uk.model_api import *


class bassetlaw_council_tax_reduction_uc_weekly_income(Variable):
    value_type = float
    entity = BenUnit
    label = "Bassetlaw Council Tax Reduction weekly Universal Credit income"
    definition_period = YEAR
    unit = GBP
    reference = "https://www.bassetlaw.gov.uk/media/15ehht0s/council-tax-reduction-scheme-working-age-2026-2027.pdf"

    def formula(benunit, period, parameters):
        has_uc_award = (
            max_(
                benunit("universal_credit_pre_benefit_cap", period),
                benunit("universal_credit", period),
            )
            > 0
        )
        uc_income = benunit("uc_earned_income", period) + benunit(
            "uc_unearned_income", period
        )
        uc_award = benunit("universal_credit", period)
        return has_uc_award * max_(0, uc_income + uc_award) / WEEKS_IN_YEAR
