from policyengine_uk.model_api import *


class st_helens_council_tax_reduction(Variable):
    value_type = float
    entity = BenUnit
    label = "St Helens Council Tax Reduction"
    documentation = "St Helens applies the prescribed Default Scheme with four local working-age amendments: paragraph 9 80 per cent maximum support, paragraph 9 Band D liability cap, paragraph 40 1 pound weekly minimum award, and paragraph 49 removal of all working-age non-dependant deductions. Pension-age applicants follow the prescribed pensioner scheme via simulated_council_tax_reduction_benunit unless they are on a working-age income-related benefit; footnote 1 preserves pensioner status for Universal Credit awards caused by Working Tax Credit closure."
    definition_period = YEAR
    unit = GBP
    reference = "https://www.sthelens.gov.uk/media/13997/St-Helens-CTR-scheme-2026/pdf/St_Helens_CTR_scheme_2026.pdf"

    def formula(benunit, period, parameters):
        ctr = parameters(period).gov.local_authorities.st_helens.council_tax_reduction
        local_scheme = benunit(
            "st_helens_council_tax_reduction_is_local_scheme", period
        )
        has_uc_award = (
            max_(
                benunit("universal_credit_pre_benefit_cap", period),
                benunit("universal_credit", period),
            )
            > 0
        )
        applicable_amount = where(
            has_uc_award,
            benunit("uc_maximum_amount", period),
            benunit("council_tax_reduction_applicable_amount", period),
        )
        applicable_income = where(
            has_uc_award,
            benunit("st_helens_council_tax_reduction_uc_applicable_income", period),
            benunit("council_tax_reduction_applicable_income", period),
        )
        relevant_income_based_benefit = benunit(
            "council_tax_reduction_relevant_income_based_benefit", period
        )
        excess_income = max_(0, applicable_income - applicable_amount)
        excess_income = where(
            relevant_income_based_benefit & ~has_uc_award, 0, excess_income
        )
        liability = benunit(
            "st_helens_council_tax_reduction_maximum_eligible_liability", period
        )
        # Paragraph 49 excludes working-age applicants from non-dependant deductions.
        award_before_minimum = max_(
            0,
            liability * ctr.maximum_support_rate
            - excess_income * ctr.means_test.withdrawal_rate,
        )
        # Paragraph 40 cancels working-age awards calculated at less than 1 pound per week.
        minimum_annual_award = ctr.means_test.minimum_weekly_award * WEEKS_IN_YEAR
        award = where(
            (award_before_minimum > 0) & (award_before_minimum < minimum_annual_award),
            0,
            award_before_minimum,
        )
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
