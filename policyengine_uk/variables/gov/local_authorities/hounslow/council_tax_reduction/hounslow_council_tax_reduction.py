from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.config import (
    is_hounslow_working_age,
)


class hounslow_council_tax_reduction(Variable):
    value_type = float
    entity = BenUnit
    label = "Hounslow Council Tax Support"
    definition_period = YEAR
    unit = GBP

    def formula(benunit, period, parameters):
        ctr = parameters(period).gov.local_authorities.hounslow.council_tax_reduction
        local_authority = benunit.household("local_authority", period)
        country = benunit.household("country", period)
        has_pensioner = benunit.household(
            "council_tax_reduction_household_has_pensioner", period
        )
        working_age = is_hounslow_working_age(local_authority, country, has_pensioner)
        weekly_net_earnings = benunit(
            "hounslow_council_tax_reduction_weekly_net_earnings", period
        )
        person = benunit.members
        child_or_young_person = person(
            "is_child_or_qualifying_young_person_for_child_benefit", period
        )
        num_children = benunit.sum(child_or_young_person)
        is_couple = benunit("is_couple", period)
        is_lone_parent = benunit("is_lone_parent", period)
        income_bands = ctr.income_band
        banded_support_rate = select(
            [
                is_lone_parent & (num_children >= 2),
                is_lone_parent & (num_children == 1),
                is_couple & (num_children >= 2),
                is_couple & (num_children == 1),
                is_couple,
            ],
            [
                income_bands.single_two_or_more_children.calc(weekly_net_earnings),
                income_bands.single_one_child.calc(weekly_net_earnings),
                income_bands.couple_two_or_more_children.calc(weekly_net_earnings),
                income_bands.couple_one_child.calc(weekly_net_earnings),
                income_bands.couple.calc(weekly_net_earnings),
            ],
            default=income_bands.single.calc(weekly_net_earnings),
        )
        carer = benunit("hounslow_council_tax_reduction_carer", period)
        support_rate = where(carer, ctr.carer_support_rate, banded_support_rate)
        liability = benunit.household("council_tax", period)
        non_dep_deductions = benunit(
            "hounslow_council_tax_reduction_non_dep_deductions", period
        )
        award = max_(0, liability * support_rate - non_dep_deductions)
        capital_eligible = (
            benunit("hounslow_council_tax_reduction_assessable_capital", period)
            <= ctr.means_test.capital_limit
        )
        return (
            working_age
            * benunit("benunit_contains_household_head", period)
            * benunit("would_claim_council_tax_reduction", period)
            * capital_eligible
            * award
        )
