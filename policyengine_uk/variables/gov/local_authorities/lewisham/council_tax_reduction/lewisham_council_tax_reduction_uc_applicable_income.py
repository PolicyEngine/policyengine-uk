from policyengine_uk.model_api import *


class lewisham_council_tax_reduction_uc_applicable_income(Variable):
    value_type = float
    entity = BenUnit
    label = "Lewisham Council Tax Reduction Universal Credit applicable income"
    definition_period = YEAR
    unit = GBP
    reference = "https://lewisham.gov.uk/-/media/services/council-tax/lewisham-council-tax-reduction-scheme-2024-2025.pdf"

    def formula(benunit, period, parameters):
        ctr = parameters(period).gov.local_authorities.lewisham.council_tax_reduction
        has_uc_case = benunit("universal_credit", period) > 0
        earnings_disregard = ctr.universal_credit.weekly_earnings_disregard
        earned_income = max_(
            0,
            benunit("uc_earned_income", period) - earnings_disregard * WEEKS_IN_YEAR,
        )
        uc_income = earned_income + benunit("uc_unearned_income", period)
        uc_award = benunit("universal_credit", period)
        return has_uc_case * (uc_income + uc_award)
