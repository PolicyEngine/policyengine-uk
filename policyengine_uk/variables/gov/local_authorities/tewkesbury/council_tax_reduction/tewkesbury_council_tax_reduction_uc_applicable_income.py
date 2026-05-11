from policyengine_uk.model_api import *


class tewkesbury_council_tax_reduction_uc_applicable_income(Variable):
    value_type = float
    entity = BenUnit
    label = "Tewkesbury Universal Credit applicable income for Council Tax Reduction"
    documentation = "Tewkesbury follows the Default Scheme paragraphs 28 and 37, which take the DWP-assessed Universal Credit earned and unearned income and add the actual award of Universal Credit."
    definition_period = YEAR
    unit = GBP
    reference = "https://www.legislation.gov.uk/uksi/2012/2886/schedule/paragraph/37"

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
