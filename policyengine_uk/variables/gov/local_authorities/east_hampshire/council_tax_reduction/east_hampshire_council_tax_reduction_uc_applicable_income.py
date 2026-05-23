from policyengine_uk.model_api import *


class east_hampshire_council_tax_reduction_uc_applicable_income(Variable):
    value_type = float
    entity = BenUnit
    label = "East Hampshire Universal Credit applicable income for Council Tax Support"
    definition_period = YEAR
    unit = GBP
    reference = "https://www.easthants.gov.uk/sites/default/files/2026-03/Council%20tax%20support%20scheme%202026-27.pdf"

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
