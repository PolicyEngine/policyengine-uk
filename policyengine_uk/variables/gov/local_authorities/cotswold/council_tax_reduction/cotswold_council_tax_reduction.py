from policyengine_uk.model_api import *


class cotswold_council_tax_reduction(Variable):
    value_type = float
    entity = BenUnit
    label = "Cotswold Council Tax Support"
    definition_period = YEAR
    unit = GBP
    reference = "https://cotswold.gov.uk/media/k04l1hc2/cdc-cts-scheme-2026-27.pdf"

    def formula(benunit, period, parameters):
        ctr = parameters(period).gov.local_authorities.cotswold.council_tax_reduction
        local_scheme = benunit("cotswold_council_tax_reduction_is_local_scheme", period)
        liability = benunit.household(
            "cotswold_council_tax_reduction_maximum_eligible_liability", period
        )
        non_dep_deductions = benunit(
            "cotswold_council_tax_reduction_non_dep_deductions", period
        )
        eligible_liability = max_(0, liability - non_dep_deductions)
        support_rate = benunit("cotswold_council_tax_reduction_support_rate", period)
        banded_award = eligible_liability * support_rate
        uc_award_before_deductions = max_(
            benunit("universal_credit_pre_benefit_cap", period),
            benunit("universal_credit", period),
        )
        has_uc_award = uc_award_before_deductions > 0
        applicable_amount = where(
            has_uc_award,
            benunit("uc_maximum_amount", period),
            benunit("council_tax_reduction_applicable_amount", period),
        )
        annual_income = (
            benunit("cotswold_council_tax_reduction_weekly_income", period)
            * WEEKS_IN_YEAR
        )
        excess_income = max_(0, annual_income - applicable_amount)
        protected_award = max_(
            0,
            eligible_liability - excess_income * ctr.means_test.withdrawal_rate,
        )
        protected = benunit("cotswold_council_tax_reduction_protected_group", period)
        award = where(protected, protected_award, banded_award)
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
