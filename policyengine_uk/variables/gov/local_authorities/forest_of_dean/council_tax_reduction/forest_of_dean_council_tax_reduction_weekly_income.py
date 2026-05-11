from policyengine_uk.model_api import *


class forest_of_dean_council_tax_reduction_weekly_income(Variable):
    value_type = float
    entity = BenUnit
    label = "Forest of Dean Council Tax Support assessed weekly income"
    documentation = "Weekly net income of the claimant and partner used to look up the section 59 entitlement bands. Non-UC cases use the prescribed Default Scheme applicable income divided by 52 after the scheme's Schedule 3 and 4 disregards. Income Support, income-based JSA and income-related ESA cases are placed in the top band under Class A/Class B criterion (g). UC cases use section 15A: DWP-assessed UC income plus the UC award."
    definition_period = YEAR
    unit = GBP
    reference = "https://www.fdean.gov.uk/media/r4ff2lok/council-tax-support-scheme-for-working-age-customers-2026-to-2027.pdf"

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
        relevant_income_based_benefit = benunit(
            "council_tax_reduction_relevant_income_based_benefit", period
        )
        return where(relevant_income_based_benefit & ~has_uc_award, 0, weekly_income)
