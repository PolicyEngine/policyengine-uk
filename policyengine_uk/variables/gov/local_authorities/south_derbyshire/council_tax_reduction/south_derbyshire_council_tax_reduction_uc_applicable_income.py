from policyengine_uk.model_api import *


class south_derbyshire_council_tax_reduction_uc_applicable_income(Variable):
    value_type = float
    entity = BenUnit
    label = "South Derbyshire Council Tax Reduction Universal Credit applicable income"
    definition_period = YEAR
    unit = GBP
    reference = "https://www.southderbyshire.gov.uk/assets/attach/15700/South-Derbyshire-CTR-scheme-2026-2027.pdf"

    def formula(benunit, period, parameters):
        uc_award_before_deductions = max_(
            benunit("universal_credit_pre_benefit_cap", period),
            benunit("universal_credit", period),
        )
        has_uc_award = uc_award_before_deductions > 0
        uc_income = benunit("uc_earned_income", period) + benunit(
            "uc_unearned_income", period
        )
        return has_uc_award * max_(0, uc_income + uc_award_before_deductions)
