from policyengine_uk.model_api import *


class tendring_council_tax_reduction(Variable):
    value_type = float
    entity = BenUnit
    label = "Tendring Council Tax Reduction"
    definition_period = YEAR
    unit = GBP
    reference = "https://legacy.tendringdc.gov.uk/sites/default/files/documents/Council_Tax/Tendring%20S13A%20202627%20Scheme%20Final.pdf"

    def formula(benunit, period, parameters):
        ctr = parameters(period).gov.local_authorities.tendring.council_tax_reduction
        local_scheme = benunit("tendring_council_tax_reduction_is_local_scheme", period)
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
            benunit("tendring_council_tax_reduction_uc_applicable_income", period),
            benunit("tendring_council_tax_reduction_applicable_income", period),
        )
        relevant_income_based_benefit = benunit(
            "council_tax_reduction_relevant_income_based_benefit", period
        )
        excess_income = max_(0, applicable_income - applicable_amount)
        excess_income = where(
            relevant_income_based_benefit & ~has_uc_award, 0, excess_income
        )
        liability = benunit.household("council_tax", period)
        maximum_support_rate = where(
            benunit("tendring_council_tax_reduction_jsa_three_years", period),
            0.6,
            ctr.maximum_support_rate,
        )
        non_dep_deductions = benunit(
            "tendring_council_tax_reduction_non_dep_deductions", period
        )
        award = max_(
            0,
            liability * maximum_support_rate
            - excess_income * ctr.means_test.withdrawal_rate
            - non_dep_deductions,
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
