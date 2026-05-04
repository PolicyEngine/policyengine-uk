from policyengine_uk.model_api import *


class cheshire_west_and_chester_council_tax_reduction(Variable):
    value_type = float
    entity = BenUnit
    label = "Cheshire West and Chester Council Tax Reduction"
    definition_period = YEAR
    unit = GBP

    def formula(benunit, period, parameters):
        ctr = parameters(
            period
        ).gov.local_authorities.cheshire_west_and_chester.council_tax_reduction
        local_scheme = benunit(
            "cheshire_west_and_chester_council_tax_reduction_is_local_scheme", period
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
        non_uc_applicable_income = benunit(
            "cheshire_west_and_chester_council_tax_reduction_applicable_income", period
        )
        uc_applicable_income = benunit(
            "cheshire_west_and_chester_council_tax_reduction_uc_applicable_income",
            period,
        )
        applicable_income = where(
            has_uc_award, uc_applicable_income, non_uc_applicable_income
        )
        relevant_income_based_benefit = benunit(
            "council_tax_reduction_relevant_income_based_benefit", period
        )
        excess_income = max_(0, applicable_income - applicable_amount)
        excess_income = where(relevant_income_based_benefit, 0, excess_income)
        protected = benunit(
            "cheshire_west_and_chester_council_tax_reduction_protected_group", period
        )
        war_pensioner = benunit(
            "cheshire_west_and_chester_council_tax_reduction_war_pensioner", period
        )
        support_rate = select(
            [war_pensioner, protected],
            [
                ctr.maximum_support_rate.war_pensioner,
                ctr.maximum_support_rate.protected,
            ],
            default=ctr.maximum_support_rate.standard,
        )
        liability = benunit.household(
            "cheshire_west_and_chester_council_tax_reduction_maximum_eligible_liability",
            period,
        )
        non_dep_deductions = benunit(
            "cheshire_west_and_chester_council_tax_reduction_non_dep_deductions",
            period,
        )
        award = max_(
            0,
            liability * support_rate
            - excess_income * ctr.means_test.withdrawal_rate
            - non_dep_deductions,
        )
        capital = where(
            has_uc_award,
            benunit("uc_assessable_capital", period),
            benunit.household("savings", period),
        )
        capital_limit = where(
            war_pensioner,
            ctr.means_test.war_pensioner_capital_limit,
            ctr.means_test.capital_limit,
        )
        capital_eligible = capital <= capital_limit
        return (
            local_scheme
            * benunit("benunit_contains_household_head", period)
            * benunit("would_claim_council_tax_reduction", period)
            * capital_eligible
            * award
        )
