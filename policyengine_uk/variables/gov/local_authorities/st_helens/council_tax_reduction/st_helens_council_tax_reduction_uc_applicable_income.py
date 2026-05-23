from policyengine_uk.model_api import *


class st_helens_council_tax_reduction_uc_applicable_income(Variable):
    value_type = float
    entity = BenUnit
    label = "St Helens Universal Credit applicable income for Council Tax Reduction"
    documentation = "Paragraph 63 takes the DWP-assessed Universal Credit income (earnings and other income) and adds the actual award of Universal Credit."
    definition_period = YEAR
    unit = GBP
    reference = "https://www.sthelens.gov.uk/media/13997/St-Helens-CTR-scheme-2026/pdf/St_Helens_CTR_scheme_2026.pdf"

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
        return has_uc_award * (uc_income + benunit("universal_credit", period))
