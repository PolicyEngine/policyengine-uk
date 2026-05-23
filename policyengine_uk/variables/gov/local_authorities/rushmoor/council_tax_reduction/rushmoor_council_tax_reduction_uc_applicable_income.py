from policyengine_uk.model_api import *


class rushmoor_council_tax_reduction_uc_applicable_income(Variable):
    value_type = float
    entity = BenUnit
    label = "Rushmoor Universal Credit applicable income for Council Tax Reduction"
    definition_period = YEAR
    unit = GBP
    reference = "https://www.rushmoor.gov.uk/media/qvmlpekv/rushmoor-s13a-scheme-202627-final.pdf"

    def formula(benunit, period, parameters):
        uc_award_before_deductions = max_(
            benunit("universal_credit_pre_benefit_cap", period),
            benunit("universal_credit", period),
        )
        has_uc_award = uc_award_before_deductions > 0
        uc_income = benunit("uc_earned_income", period) + benunit(
            "uc_unearned_income", period
        )
        return has_uc_award * (uc_income + benunit("universal_credit", period))
