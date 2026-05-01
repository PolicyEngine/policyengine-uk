from policyengine_uk.model_api import *


class havering_council_tax_reduction_uc_applicable_income(Variable):
    value_type = float
    entity = BenUnit
    label = "Havering CTS Universal Credit applicable income"
    definition_period = YEAR
    unit = GBP
    reference = "https://www.havering.gov.uk/downloads/file/6930/council-tax-support-scheme-2025-2026"

    def formula(benunit, period, parameters):
        has_uc_award = benunit("universal_credit", period) > 0
        uc_income = benunit("uc_earned_income", period) + benunit(
            "uc_unearned_income", period
        )
        uc_award = benunit("universal_credit", period)
        return has_uc_award * (uc_income + uc_award)
