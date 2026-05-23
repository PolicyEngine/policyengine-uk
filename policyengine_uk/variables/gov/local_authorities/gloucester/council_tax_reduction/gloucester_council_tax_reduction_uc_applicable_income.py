from policyengine_uk.model_api import *


class gloucester_council_tax_reduction_uc_applicable_income(Variable):
    value_type = float
    entity = BenUnit
    label = "Gloucester Council Tax Support Universal Credit applicable income"
    definition_period = YEAR
    unit = GBP
    reference = "https://www.gloucester.gov.uk/media/ruwinppa/local-council-tax-support-policy-2026-v2.pdf"

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
        return has_uc_award * (uc_income + uc_award)
