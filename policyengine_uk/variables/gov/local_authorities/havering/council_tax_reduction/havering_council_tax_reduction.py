from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.config import (
    is_havering_working_age,
)


class havering_council_tax_reduction(Variable):
    value_type = float
    entity = BenUnit
    label = "Havering Council Tax Support"
    definition_period = YEAR
    unit = GBP

    def formula(benunit, period, parameters):
        ctr = parameters(period).gov.local_authorities.havering.council_tax_reduction
        local_authority = benunit.household("local_authority", period)
        country = benunit.household("country", period)
        has_pensioner = benunit.household(
            "council_tax_reduction_household_has_pensioner", period
        )
        working_age = is_havering_working_age(local_authority, country, has_pensioner)
        full_support = benunit(
            "havering_council_tax_reduction_full_support_group", period
        )
        disabled = benunit("havering_council_tax_reduction_disabled", period)
        support_rate = select(
            [
                full_support,
                disabled,
            ],
            [
                ctr.maximum_support_rate.full,
                ctr.maximum_support_rate.disabled,
            ],
            default=ctr.maximum_support_rate.standard,
        )
        capped_liability = benunit.household(
            "havering_council_tax_reduction_maximum_eligible_liability", period
        )
        liability = where(
            full_support,
            benunit.household("council_tax", period),
            capped_liability,
        )
        has_uc_award = benunit("universal_credit", period) > 0
        applicable_amount = where(
            has_uc_award,
            benunit("uc_maximum_amount", period),
            benunit("council_tax_reduction_applicable_amount", period),
        )
        non_uc_applicable_income = benunit(
            "council_tax_reduction_applicable_income", period
        )
        uc_applicable_income = benunit(
            "havering_council_tax_reduction_uc_applicable_income", period
        )
        applicable_income = where(
            has_uc_award, uc_applicable_income, non_uc_applicable_income
        )
        relevant_income_based_benefit = benunit(
            "council_tax_reduction_relevant_income_based_benefit", period
        )
        excess_income = max_(0, applicable_income - applicable_amount)
        excess_income = where(relevant_income_based_benefit, 0, excess_income)
        non_dep_deductions = benunit(
            "havering_council_tax_reduction_non_dep_deductions", period
        )
        award = max_(
            0,
            liability * support_rate
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
        capital_eligible = capital_eligible | relevant_income_based_benefit
        return (
            working_age
            * benunit("benunit_contains_household_head", period)
            * benunit("would_claim_council_tax_reduction", period)
            * capital_eligible
            * award
        )
