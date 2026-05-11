from policyengine_uk.model_api import *


class tewkesbury_council_tax_reduction(Variable):
    value_type = float
    entity = BenUnit
    label = "Tewkesbury Council Tax Reduction"
    documentation = "Tewkesbury Borough Council has remained on the prescribed Default Scheme since 1 April 2013, so its working-age scheme is the Default Scheme as enacted by the Council Tax Reduction Schemes (Default Scheme) (England) Regulations 2012 with no local amendments. The Cabinet's Council Tax Reduction Scheme Report dated January 2026 confirms there are no proposed changes for 2026/27."
    definition_period = YEAR
    unit = GBP
    reference = "https://minutes.tewkesbury.gov.uk/documents/s71351/Council%20Tax%20Reduction%20Scheme%20Report.pdf"

    def formula(benunit, period, parameters):
        ctr = parameters(period).gov.local_authorities.tewkesbury.council_tax_reduction
        local_scheme = benunit(
            "tewkesbury_council_tax_reduction_is_local_scheme", period
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
            benunit("tewkesbury_council_tax_reduction_uc_applicable_income", period),
            benunit("council_tax_reduction_applicable_income", period),
        )
        relevant_income_based_benefit = benunit(
            "council_tax_reduction_relevant_income_based_benefit", period
        )
        excess_income = max_(0, applicable_income - applicable_amount)
        excess_income = where(
            relevant_income_based_benefit & ~has_uc_award, 0, excess_income
        )
        liability = benunit.household("council_tax", period)
        non_dep_deductions = benunit(
            "tewkesbury_council_tax_reduction_non_dep_deductions", period
        )
        award = max_(
            0,
            liability * ctr.maximum_support_rate
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
