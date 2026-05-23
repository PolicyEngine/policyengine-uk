from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.config import (
    is_haringey_working_age,
)


class haringey_council_tax_reduction(Variable):
    value_type = float
    entity = BenUnit
    label = "Haringey Council Tax Reduction"
    definition_period = YEAR
    unit = GBP

    def formula(benunit, period, parameters):
        ctr = parameters(period).gov.local_authorities.haringey.council_tax_reduction
        local_authority = benunit.household("local_authority", period)
        country = benunit.household("country", period)
        has_pensioner = benunit.household(
            "council_tax_reduction_household_has_pensioner", period
        )
        working_age = is_haringey_working_age(local_authority, country, has_pensioner)
        protected = benunit("haringey_council_tax_reduction_protected_group", period)
        has_uc_award = benunit("universal_credit", period) > 0
        support_rate = where(
            protected,
            ctr.maximum_support_rate.protected,
            ctr.maximum_support_rate.non_protected,
        )
        applicable_amount = where(
            has_uc_award,
            benunit("uc_maximum_amount", period),
            benunit("council_tax_reduction_applicable_amount", period),
        )
        non_uc_applicable_income = benunit(
            "haringey_council_tax_reduction_applicable_income", period
        ) + benunit("haringey_council_tax_reduction_tariff_income", period)
        applicable_income = where(
            has_uc_award,
            benunit("haringey_council_tax_reduction_uc_applicable_income", period),
            non_uc_applicable_income,
        )
        relevant_income_based_benefit = benunit(
            "council_tax_reduction_relevant_income_based_benefit", period
        )
        excess_income = max_(0, applicable_income - applicable_amount)
        excess_income = where(relevant_income_based_benefit, 0, excess_income)
        non_dep_deductions = benunit(
            "haringey_council_tax_reduction_non_dep_deductions", period
        )
        liability = benunit.household("council_tax", period)
        award = max_(
            0,
            liability * support_rate
            - excess_income * ctr.means_test.withdrawal_rate
            - non_dep_deductions,
        )
        award = where(award < ctr.minimum_award * WEEKS_IN_YEAR, 0, award)
        non_uc_capital = benunit.household("savings", period)
        uc_capital = benunit("uc_assessable_capital", period)
        capital = where(has_uc_award, uc_capital, non_uc_capital)
        capital_eligible = capital <= ctr.means_test.capital_limit
        return (
            working_age
            * benunit("benunit_contains_household_head", period)
            * benunit("would_claim_council_tax_reduction", period)
            * capital_eligible
            * award
        )
