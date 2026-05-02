from policyengine_uk.model_api import *


class babergh_council_tax_reduction(Variable):
    value_type = float
    entity = BenUnit
    label = "Babergh Council Tax Reduction"
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.babergh.gov.uk/documents/d/babergh/bdc-ctr-scheme-2026_27-v4-pdf"
    )

    def formula(benunit, period, parameters):
        ctr = parameters(period).gov.local_authorities.babergh.council_tax_reduction
        local_scheme = benunit("babergh_council_tax_reduction_is_local_scheme", period)
        has_uc_award = benunit("universal_credit", period) > 0
        liability = benunit.household("council_tax", period)
        non_dep_deductions = benunit(
            "babergh_council_tax_reduction_non_dep_deductions", period
        )
        eligible_liability = max_(0, liability - non_dep_deductions)

        applicable_amount = benunit("council_tax_reduction_applicable_amount", period)
        applicable_income = benunit(
            "council_tax_reduction_applicable_income", period
        ) + benunit("babergh_council_tax_reduction_tariff_income", period)
        relevant_income_based_benefit = benunit(
            "council_tax_reduction_relevant_income_based_benefit", period
        )
        excess_income = max_(0, applicable_income - applicable_amount)
        excess_income = where(relevant_income_based_benefit, 0, excess_income)
        non_uc_award = max_(
            0,
            eligible_liability * ctr.maximum_support_rate
            - excess_income * ctr.means_test.withdrawal_rate,
        )

        monthly_uc_earnings = benunit(
            "babergh_council_tax_reduction_uc_monthly_earnings", period
        )
        weekly_uc_contribution = benunit(
            "babergh_council_tax_reduction_uc_weekly_contribution", period
        )
        uc_award = max_(
            0,
            eligible_liability - weekly_uc_contribution * WEEKS_IN_YEAR,
        )
        uc_award = where(
            monthly_uc_earnings
            >= ctr.uc_earnings_contribution.no_entitlement_threshold,
            0,
            uc_award,
        )
        award = where(has_uc_award, uc_award, non_uc_award)
        annual_minimum_award = ctr.means_test.minimum_award * WEEKS_IN_YEAR
        award = where(award >= annual_minimum_award, award, 0)

        non_uc_capital_eligible = (
            benunit.household("savings", period) <= ctr.means_test.capital_limit
        )
        uc_capital_eligible = (
            benunit("uc_assessable_capital", period) <= ctr.means_test.capital_limit
        )
        capital_eligible = where(
            has_uc_award, uc_capital_eligible, non_uc_capital_eligible
        )
        return (
            local_scheme
            * benunit("benunit_contains_household_head", period)
            * benunit("would_claim_council_tax_reduction", period)
            * capital_eligible
            * award
        )
