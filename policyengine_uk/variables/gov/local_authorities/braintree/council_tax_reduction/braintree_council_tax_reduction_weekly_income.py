from policyengine_uk.model_api import *


class braintree_council_tax_reduction_weekly_income(Variable):
    value_type = float
    entity = BenUnit
    label = "Braintree Council Tax Reduction assessed weekly income"
    documentation = "Weekly net income of the claimant and partner used to look up the Schedule 1 entitlement bands. Paragraph 12.2-12.4 takes the DWP-assessed Universal Credit income (multiplied by 12 and divided by 52) and adds the actual award where the applicant has a UC award. Non-UC cases use the prescribed Schedule 2/4 disregards, which PolicyEngine UK exposes via council_tax_reduction_applicable_income."
    definition_period = YEAR
    unit = GBP
    reference = "https://www.braintree.gov.uk/downloads/file/4374/council-tax-reduction-scheme-2026-27"

    def formula(benunit, period, parameters):
        has_uc_award = (
            max_(
                benunit("universal_credit_pre_benefit_cap", period),
                benunit("universal_credit", period),
            )
            > 0
        )
        uc_income = (
            benunit("uc_earned_income", period)
            + benunit("uc_unearned_income", period)
            + benunit("universal_credit", period)
        )
        weekly_income = where(
            has_uc_award,
            uc_income / WEEKS_IN_YEAR,
            benunit("council_tax_reduction_applicable_income", period) / WEEKS_IN_YEAR,
        )
        return weekly_income
