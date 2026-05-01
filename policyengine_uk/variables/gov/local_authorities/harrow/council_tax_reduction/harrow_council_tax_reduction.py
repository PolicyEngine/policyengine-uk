from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.config import (
    is_harrow_working_age,
)


class harrow_council_tax_reduction(Variable):
    value_type = float
    entity = BenUnit
    label = "Harrow Council Tax Support"
    definition_period = YEAR
    unit = GBP

    def formula(benunit, period, parameters):
        ctr = parameters(period).gov.local_authorities.harrow.council_tax_reduction
        local_authority = benunit.household("local_authority", period)
        country = benunit.household("country", period)
        has_pensioner = benunit.household(
            "council_tax_reduction_household_has_pensioner", period
        )
        working_age = is_harrow_working_age(local_authority, country, has_pensioner)
        has_uc_award = benunit("universal_credit", period) > 0
        disabled = benunit("harrow_council_tax_reduction_disabled", period)
        support_rate = where(
            has_uc_award,
            benunit("harrow_council_tax_reduction_uc_support_rate", period),
            where(
                disabled,
                ctr.maximum_support_rate.disabled,
                ctr.maximum_support_rate.standard,
            ),
        )
        capped_liability = benunit.household(
            "harrow_council_tax_reduction_maximum_eligible_liability", period
        )
        liability = where(
            disabled,
            benunit.household("council_tax", period),
            capped_liability,
        )
        non_dep_deductions = benunit(
            "harrow_council_tax_reduction_non_dep_deductions", period
        )
        applicable_amount = benunit("council_tax_reduction_applicable_amount", period)
        applicable_income = benunit("council_tax_reduction_applicable_income", period)
        relevant_income_based_benefit = benunit(
            "council_tax_reduction_relevant_income_based_benefit", period
        )
        excess_income = max_(0, applicable_income - applicable_amount)
        excess_income = where(relevant_income_based_benefit, 0, excess_income)
        non_uc_award = (
            liability * support_rate
            - excess_income * ctr.means_test.withdrawal_rate
            - non_dep_deductions
        )
        uc_award = liability * support_rate - non_dep_deductions
        award = max_(0, where(has_uc_award, uc_award, non_uc_award))
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
            working_age
            * benunit("benunit_contains_household_head", period)
            * benunit("would_claim_council_tax_reduction", period)
            * capital_eligible
            * award
        )
