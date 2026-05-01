from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.config import (
    is_hillingdon_working_age,
)


class hillingdon_council_tax_reduction(Variable):
    value_type = float
    entity = BenUnit
    label = "Hillingdon Council Tax Reduction"
    definition_period = YEAR
    unit = GBP

    def formula(benunit, period, parameters):
        ctr = parameters(period).gov.local_authorities.hillingdon.council_tax_reduction
        local_authority = benunit.household("local_authority", period)
        country = benunit.household("country", period)
        has_pensioner = benunit.household(
            "council_tax_reduction_household_has_pensioner", period
        )
        working_age = is_hillingdon_working_age(
            local_authority,
            country,
            has_pensioner,
        )
        weekly_income = benunit(
            "hillingdon_council_tax_reduction_weekly_income", period
        )
        person = benunit.members
        num_children = benunit.sum(
            person("is_child_or_qualifying_young_person_for_child_benefit", period)
        )
        is_couple = benunit("is_couple", period)
        income_bands = ctr.income_band
        standard_support_rate = select(
            [
                num_children >= 2,
                num_children == 1,
                is_couple,
            ],
            [
                income_bands.family_two_or_more_children.calc(weekly_income),
                income_bands.family_one_child.calc(weekly_income),
                income_bands.couple.calc(weekly_income),
            ],
            default=income_bands.single.calc(weekly_income),
        )
        band_2 = benunit("hillingdon_council_tax_reduction_band_2", period)
        support_rate = where(band_2, 0.75, standard_support_rate)
        liability = benunit.household(
            "hillingdon_council_tax_reduction_maximum_eligible_liability", period
        )
        non_dep_deductions = benunit(
            "hillingdon_council_tax_reduction_non_dep_deductions", period
        )
        award = max_(0, liability * support_rate - non_dep_deductions)
        award = where(award < ctr.minimum_award * WEEKS_IN_YEAR, 0, award)
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
