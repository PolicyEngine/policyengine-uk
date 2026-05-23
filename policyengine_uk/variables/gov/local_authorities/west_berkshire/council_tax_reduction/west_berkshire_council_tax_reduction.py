from policyengine_uk.model_api import *


class west_berkshire_council_tax_reduction(Variable):
    value_type = float
    entity = BenUnit
    label = "West Berkshire Council Tax Reduction"
    documentation = "West Berkshire's local scheme applies six local amendments to the prescribed Default Scheme for non-vulnerable working-age Class D and E applicants: paragraph 29(1)A 6,000 pound capital cutoff, paragraph 29A Band C liability cap, paragraph 29B 70 per cent maximum support, paragraph 29C 10 pound weekly minimum award, paragraph 17 30 per cent Class E taper, and the removal of the working-age Class F second adult rebate. Paragraph 29D protects the vulnerable category from each of those amendments (and uses a 20 per cent Class E1 taper from paragraph 17A). Pensioners receive the prescribed pensioner scheme via simulated_council_tax_reduction_benunit."
    definition_period = YEAR
    unit = GBP
    reference = "https://www.westberks.gov.uk/media/66425/Council-Tax-Reduction-Scheme-2026-27/pdf/The_Council_Tax_Reduction_Scheme_as_amended_by_West_Berkshire_Council_2026.pdf"

    def formula(benunit, period, parameters):
        ctr = parameters(
            period
        ).gov.local_authorities.west_berkshire.council_tax_reduction
        local_scheme = benunit(
            "west_berkshire_council_tax_reduction_is_local_scheme", period
        )
        vulnerable = benunit(
            "west_berkshire_council_tax_reduction_vulnerable_group", period
        )
        applicable_amount = benunit("council_tax_reduction_applicable_amount", period)
        default_applicable_income = benunit(
            "council_tax_reduction_applicable_income", period
        )
        uc_award = max_(
            benunit("universal_credit_pre_benefit_cap", period),
            benunit("universal_credit", period),
        )
        has_uc_award = uc_award > 0
        uc_applicable_income = (
            benunit("uc_earned_income", period)
            + benunit("uc_unearned_income", period)
            + uc_award
        )
        applicable_income = where(
            has_uc_award, uc_applicable_income, default_applicable_income
        )
        relevant_income_based_benefit = benunit(
            "council_tax_reduction_relevant_income_based_benefit", period
        )
        # Income-based-benefit recipients are treated as Class D (income <= applicable amount).
        excess_income = max_(0, applicable_income - applicable_amount)
        excess_income = where(relevant_income_based_benefit, 0, excess_income)
        liability = benunit(
            "west_berkshire_council_tax_reduction_maximum_eligible_liability", period
        )
        non_dep_deductions = benunit(
            "west_berkshire_council_tax_reduction_non_dep_deductions", period
        )
        maximum_support_rate = where(
            vulnerable,
            1.0,
            ctr.maximum_support_rate,
        )
        withdrawal_rate = where(
            vulnerable,
            ctr.means_test.vulnerable_withdrawal_rate,
            ctr.means_test.withdrawal_rate,
        )
        award_before_minimum = max_(
            0,
            liability * maximum_support_rate
            - excess_income * withdrawal_rate
            - non_dep_deductions,
        )
        # Paragraph 29C minimum award only applies to non-vulnerable Class D/E.
        minimum_annual_award = ctr.means_test.minimum_weekly_award * WEEKS_IN_YEAR
        below_min = (
            ~vulnerable
            & (award_before_minimum > 0)
            & (award_before_minimum < minimum_annual_award)
        )
        award = where(below_min, 0, award_before_minimum)
        # Paragraph 29(1)A excludes non-vulnerable claimants whose capital is
        # equal to or greater than GBP 6,000; the vulnerable/default limit
        # excludes only capital above GBP 16,000.
        capital = where(
            has_uc_award,
            benunit("uc_assessable_capital", period),
            benunit.household("savings", period),
        )
        capital_limit = where(
            vulnerable,
            ctr.means_test.vulnerable_capital_limit,
            ctr.means_test.capital_limit,
        )
        capital_eligible = where(
            vulnerable, capital <= capital_limit, capital < capital_limit
        )
        return (
            local_scheme
            * benunit("benunit_contains_household_head", period)
            * benunit("would_claim_council_tax_reduction", period)
            * capital_eligible
            * award
        )
