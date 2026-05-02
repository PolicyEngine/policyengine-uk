from policyengine_uk.model_api import *


class buckinghamshire_council_tax_reduction(Variable):
    value_type = float
    entity = BenUnit
    label = "Buckinghamshire Council Tax Reduction"
    definition_period = YEAR
    unit = GBP

    def formula(benunit, period, parameters):
        ctr = parameters(
            period
        ).gov.local_authorities.buckinghamshire.council_tax_reduction
        local_scheme = benunit(
            "buckinghamshire_council_tax_reduction_is_local_scheme", period
        )
        weekly_income = benunit(
            "buckinghamshire_council_tax_reduction_weekly_income", period
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
        passported = benunit(
            "council_tax_reduction_relevant_income_based_benefit", period
        )
        support_rate = where(passported, 1, banded_support_rate)
        liability = benunit.household("council_tax", period)
        non_dep_deductions = benunit(
            "buckinghamshire_council_tax_reduction_non_dep_deductions", period
        )
        eligible_liability = max_(0, liability - non_dep_deductions)
        has_uc_award = benunit("universal_credit", period) > 0
        non_uc_capital_eligible = (
            benunit.household("savings", period) < ctr.means_test.capital_limit
        )
        uc_capital_eligible = (
            benunit("uc_assessable_capital", period) < ctr.means_test.capital_limit
        )
        capital_eligible = where(
            has_uc_award, uc_capital_eligible, non_uc_capital_eligible
        )
        return (
            local_scheme
            * benunit("benunit_contains_household_head", period)
            * benunit("would_claim_council_tax_reduction", period)
            * capital_eligible
            * eligible_liability
            * support_rate
        )
