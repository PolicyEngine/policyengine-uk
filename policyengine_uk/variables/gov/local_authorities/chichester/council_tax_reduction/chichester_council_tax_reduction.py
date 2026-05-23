from policyengine_uk.model_api import *
import numpy as np


class chichester_council_tax_reduction(Variable):
    value_type = float
    entity = BenUnit
    label = "Chichester Council Tax Reduction"
    definition_period = YEAR
    unit = GBP

    def formula(benunit, period, parameters):
        ctr = parameters(period).gov.local_authorities.chichester.council_tax_reduction
        local_scheme = benunit(
            "chichester_council_tax_reduction_is_local_scheme", period
        )
        uc_award_before_deductions = max_(
            benunit("universal_credit_pre_benefit_cap", period),
            benunit("universal_credit", period),
        )
        has_uc_award = uc_award_before_deductions > 0
        non_uc_applicable_amount = benunit(
            "council_tax_reduction_applicable_amount", period
        )
        non_uc_applicable_income = benunit(
            "council_tax_reduction_applicable_income", period
        ) + benunit("chichester_council_tax_reduction_tariff_income", period)
        relevant_income_based_benefit = benunit(
            "council_tax_reduction_relevant_income_based_benefit", period
        )
        non_uc_excess_income = max_(
            0, non_uc_applicable_income - non_uc_applicable_amount
        )
        non_uc_excess_income = where(
            relevant_income_based_benefit, 0, non_uc_excess_income
        )

        weekly_uc_income = (
            benunit("chichester_council_tax_reduction_uc_applicable_income", period)
            / WEEKS_IN_YEAR
        )
        person = benunit.members
        num_children = benunit.sum(
            person(
                "is_child_or_qualifying_young_person_for_child_benefit",
                period,
            )
        )
        is_couple = benunit("is_couple", period)
        weekly_uc_income_for_band = np.round(weekly_uc_income, 2)
        income_bands = ctr.income_band
        uc_support_rate = select(
            [
                num_children >= 2,
                num_children == 1,
                is_couple,
            ],
            [
                income_bands.two_or_more_children.calc(weekly_uc_income_for_band),
                income_bands.one_child.calc(weekly_uc_income_for_band),
                income_bands.couple.calc(weekly_uc_income_for_band),
            ],
            default=income_bands.single.calc(weekly_uc_income_for_band),
        )

        liability = benunit.household("council_tax", period)
        non_dep_deductions = benunit(
            "chichester_council_tax_reduction_non_dep_deductions", period
        )
        non_uc_award = max_(
            0,
            liability * ctr.maximum_support_rate
            - non_uc_excess_income * ctr.means_test.withdrawal_rate
            - non_dep_deductions,
        )
        uc_award = max_(0, liability * uc_support_rate - non_dep_deductions)
        award = where(has_uc_award, uc_award, non_uc_award)

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
