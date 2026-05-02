from policyengine_uk.model_api import *


class somerset_council_tax_reduction(Variable):
    value_type = float
    entity = BenUnit
    label = "Somerset Council Tax Reduction"
    definition_period = YEAR
    unit = GBP

    def formula(benunit, period, parameters):
        ctr = parameters(period).gov.local_authorities.somerset.council_tax_reduction
        local_scheme = benunit("somerset_council_tax_reduction_is_local_scheme", period)
        weekly_income = benunit("somerset_council_tax_reduction_weekly_income", period)
        person = benunit.members
        num_children = benunit.sum(
            person("is_child_or_qualifying_young_person_for_child_benefit", period)
        )
        is_couple = benunit("is_couple", period)
        income_bands = ctr.income_band
        weekly_income_for_band = weekly_income + 1e-9
        banded_support_rate = select(
            [
                is_couple & (num_children >= 2),
                is_couple & (num_children == 1),
                (~is_couple) & (num_children >= 2),
                (~is_couple) & (num_children == 1),
                is_couple,
            ],
            [
                income_bands.couple_two_or_more_children.calc(weekly_income_for_band),
                income_bands.couple_one_child.calc(weekly_income_for_band),
                income_bands.single_two_or_more_children.calc(weekly_income_for_band),
                income_bands.single_one_child.calc(weekly_income_for_band),
                income_bands.couple.calc(weekly_income_for_band),
            ],
            default=income_bands.single.calc(weekly_income_for_band),
        )
        relevant_income_based_benefit = benunit(
            "council_tax_reduction_relevant_income_based_benefit", period
        )
        support_rate = where(relevant_income_based_benefit, 1, banded_support_rate)
        liability = benunit.household(
            "somerset_council_tax_reduction_maximum_eligible_liability", period
        )
        non_dep_deductions = benunit(
            "somerset_council_tax_reduction_non_dep_deductions", period
        )
        award = max_(0, liability * support_rate - non_dep_deductions)
        has_uc_award = benunit("universal_credit", period) > 0
        ordinary_capital_eligible = (
            benunit.household("savings", period) <= ctr.means_test.capital_limit
        )
        passported_capital_eligible = (
            benunit.household("savings", period)
            <= ctr.means_test.passported_capital_limit
        )
        non_uc_capital_eligible = where(
            relevant_income_based_benefit,
            passported_capital_eligible,
            ordinary_capital_eligible,
        )
        uc_capital_eligible = (
            benunit("uc_assessable_capital", period) <= ctr.means_test.capital_limit
        )
        capital_eligible = where(
            has_uc_award,
            uc_capital_eligible,
            non_uc_capital_eligible,
        )
        return (
            local_scheme
            * benunit("benunit_contains_household_head", period)
            * benunit("would_claim_council_tax_reduction", period)
            * capital_eligible
            * award
        )
