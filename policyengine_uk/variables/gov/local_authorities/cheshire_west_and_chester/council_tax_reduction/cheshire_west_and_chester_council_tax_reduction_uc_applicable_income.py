from policyengine_uk.model_api import *


class cheshire_west_and_chester_council_tax_reduction_uc_applicable_income(Variable):
    value_type = float
    entity = BenUnit
    label = "Cheshire West and Chester Council Tax Reduction Universal Credit applicable income"
    definition_period = YEAR
    unit = GBP
    reference = "https://www.cheshirewestandchester.gov.uk/asset-library/council-tax-reduction-summary-2026-2027-annex-a-part-1.pdf"

    def formula(benunit, period, parameters):
        ctr = parameters(
            period
        ).gov.local_authorities.cheshire_west_and_chester.council_tax_reduction
        has_uc_award = (
            max_(
                benunit("universal_credit_pre_benefit_cap", period),
                benunit("universal_credit", period),
            )
            > 0
        )
        source_disregarded_income = benunit(
            "cheshire_west_and_chester_council_tax_reduction_source_disregarded_income",
            period,
        )
        earned_income = max_(
            0,
            benunit("uc_earned_income", period)
            - ctr.earnings_disregard.amount * WEEKS_IN_YEAR,
        )
        unearned_income = max_(
            0,
            benunit("uc_unearned_income", period) - source_disregarded_income,
        )
        return has_uc_award * (
            earned_income + unearned_income + benunit("universal_credit", period)
        )
