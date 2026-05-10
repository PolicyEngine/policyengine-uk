from policyengine_uk.model_api import *


class hertsmere_council_tax_reduction(Variable):
    value_type = float
    entity = BenUnit
    label = "Hertsmere Council Tax Reduction"
    definition_period = YEAR
    unit = GBP
    reference = "https://www.hertsmere.gov.uk/asset-library/cts-scheme-2026-27.pdf"

    def formula(benunit, period, parameters):
        ctr = parameters(period).gov.local_authorities.hertsmere.council_tax_reduction
        local_scheme = benunit(
            "hertsmere_council_tax_reduction_is_local_scheme", period
        )
        uc_scheme = benunit("hertsmere_council_tax_reduction_is_uc_scheme", period)
        protected = benunit("hertsmere_council_tax_reduction_protected_group", period)
        liability = benunit.household(
            "hertsmere_council_tax_reduction_maximum_eligible_liability", period
        )
        non_dep_deductions = benunit(
            "hertsmere_council_tax_reduction_non_dep_deductions", period
        )
        non_uc_maximum_support_rate = where(protected, 1, ctr.maximum_support_rate)
        applicable_amount = benunit("council_tax_reduction_applicable_amount", period)
        applicable_income = benunit("council_tax_reduction_applicable_income", period)
        relevant_income_based_benefit = benunit(
            "council_tax_reduction_relevant_income_based_benefit", period
        )
        excess_income = max_(0, applicable_income - applicable_amount)
        excess_income = where(relevant_income_based_benefit, 0, excess_income)
        non_uc_award = max_(
            0,
            liability * non_uc_maximum_support_rate
            - excess_income * ctr.means_test.withdrawal_rate
            - non_dep_deductions,
        )
        uc_support_rate = benunit(
            "hertsmere_council_tax_reduction_uc_support_rate", period
        )
        uc_award = max_(0, liability * uc_support_rate - non_dep_deductions)
        non_uc_capital_eligible = (
            benunit.household("savings", period) <= ctr.means_test.capital_limit
        )
        uc_capital_eligible = (
            benunit("uc_assessable_capital", period) <= ctr.means_test.capital_limit
        )
        capital_eligible = where(
            uc_scheme, uc_capital_eligible, non_uc_capital_eligible
        )
        return (
            local_scheme
            * benunit("benunit_contains_household_head", period)
            * benunit("would_claim_council_tax_reduction", period)
            * capital_eligible
            * where(uc_scheme, uc_award, non_uc_award)
        )
