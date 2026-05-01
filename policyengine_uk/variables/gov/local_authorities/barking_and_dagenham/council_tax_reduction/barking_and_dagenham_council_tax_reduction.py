from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.config import (
    is_barking_and_dagenham_working_age,
)


class barking_and_dagenham_council_tax_reduction(Variable):
    value_type = float
    entity = BenUnit
    label = "Barking and Dagenham Council Tax Support"
    definition_period = YEAR
    unit = GBP

    def formula(benunit, period, parameters):
        ctr = parameters(
            period
        ).gov.local_authorities.barking_and_dagenham.council_tax_reduction
        local_authority = benunit.household("local_authority", period)
        country = benunit.household("country", period)
        has_pensioner = benunit.household(
            "council_tax_reduction_household_has_pensioner", period
        )
        working_age = is_barking_and_dagenham_working_age(
            local_authority,
            country,
            has_pensioner,
        )
        weekly_income = benunit(
            "barking_and_dagenham_council_tax_reduction_weekly_income", period
        )
        person = benunit.members
        num_children = benunit.sum(
            person("is_child_or_qualifying_young_person_for_child_benefit", period)
        )
        is_couple = benunit("is_couple", period)
        income_bands = ctr.income_band
        support_rate = select(
            [
                is_couple & (num_children >= 2),
                is_couple & (num_children == 1),
                (~is_couple) & (num_children >= 2),
                (~is_couple) & (num_children == 1),
                is_couple,
            ],
            [
                income_bands.couple_two_or_more_children.calc(weekly_income),
                income_bands.couple_one_child.calc(weekly_income),
                income_bands.single_two_or_more_children.calc(weekly_income),
                income_bands.single_one_child.calc(weekly_income),
                income_bands.couple.calc(weekly_income),
            ],
            default=income_bands.single.calc(weekly_income),
        )
        liability = benunit.household("council_tax", period)
        non_dep_deductions = benunit(
            "barking_and_dagenham_council_tax_reduction_non_dep_deductions", period
        )
        eligible_liability = max_(0, liability - non_dep_deductions)
        award = eligible_liability * support_rate
        capital_eligible = (
            benunit.household("savings", period) <= ctr.means_test.capital_limit
        )
        return (
            working_age
            * benunit("benunit_contains_household_head", period)
            * benunit("would_claim_council_tax_reduction", period)
            * capital_eligible
            * award
        )
