from policyengine_uk.model_api import *


class north_yorkshire_council_tax_reduction(Variable):
    value_type = float
    entity = BenUnit
    label = "North Yorkshire Council Tax Reduction"
    definition_period = YEAR
    unit = GBP

    def formula(benunit, period, parameters):
        ctr = parameters(
            period
        ).gov.local_authorities.north_yorkshire.council_tax_reduction
        local_scheme = benunit(
            "north_yorkshire_council_tax_reduction_is_local_scheme", period
        )
        weekly_income = benunit(
            "north_yorkshire_council_tax_reduction_weekly_income", period
        )
        person = benunit.members
        child_or_young_person = person(
            "is_child_or_qualifying_young_person_for_child_benefit", period
        )
        num_children = benunit.sum(child_or_young_person)
        is_couple = benunit("is_couple", period)
        income_bands = ctr.income_band
        weekly_income_for_band = weekly_income + 1e-9
        banded_support_rate = select(
            [
                num_children >= 2,
                num_children == 1,
                is_couple,
            ],
            [
                income_bands.family_two_or_more_children.calc(weekly_income_for_band),
                income_bands.family_one_child.calc(weekly_income_for_band),
                income_bands.couple.calc(weekly_income_for_band),
            ],
            default=income_bands.single.calc(weekly_income_for_band),
        )
        relevant_income_based_benefit = benunit(
            "council_tax_reduction_relevant_income_based_benefit", period
        )
        support_rate = where(relevant_income_based_benefit, 1, banded_support_rate)
        liability = benunit.household("council_tax", period)
        has_uc_award = benunit("universal_credit", period) > 0
        non_uc_capital = benunit.household("savings", period)
        uc_capital = benunit("uc_assessable_capital", period)
        ordinary_capital_eligible = non_uc_capital < ctr.means_test.capital_limit
        passported_capital_eligible = (
            non_uc_capital <= ctr.means_test.passported_capital_limit
        )
        non_uc_capital_eligible = where(
            relevant_income_based_benefit,
            passported_capital_eligible,
            ordinary_capital_eligible,
        )
        uc_capital_eligible = uc_capital < ctr.means_test.capital_limit
        capital_eligible = where(
            has_uc_award, uc_capital_eligible, non_uc_capital_eligible
        )
        return (
            local_scheme
            * benunit("benunit_contains_household_head", period)
            * benunit("would_claim_council_tax_reduction", period)
            * capital_eligible
            * liability
            * support_rate
        )
