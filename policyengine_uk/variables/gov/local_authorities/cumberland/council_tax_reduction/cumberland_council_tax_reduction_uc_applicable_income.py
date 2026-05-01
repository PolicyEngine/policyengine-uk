from policyengine_uk.model_api import *


class cumberland_council_tax_reduction_uc_applicable_income(Variable):
    value_type = float
    entity = BenUnit
    label = "Cumberland Council Tax Reduction Universal Credit applicable income"
    definition_period = YEAR
    unit = GBP
    reference = "https://www.cumberland.gov.uk/sites/default/files/2026-04/cumberland_council_final_council_tax_reduction_ctr_scheme_for_2026_to_2027.pdf"

    def formula(benunit, period, parameters):
        has_uc_award = benunit("universal_credit", period) > 0
        uc_income = benunit("uc_earned_income", period) + benunit(
            "uc_unearned_income", period
        )
        uc_award = benunit("universal_credit", period)
        return has_uc_award * (uc_income + uc_award)
