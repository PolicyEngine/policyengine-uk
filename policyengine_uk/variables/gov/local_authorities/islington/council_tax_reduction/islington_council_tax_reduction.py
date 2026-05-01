from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.config import (
    is_islington_working_age,
)


class islington_council_tax_reduction(Variable):
    value_type = float
    entity = BenUnit
    label = "Islington Council Tax Support"
    definition_period = YEAR
    unit = GBP

    def formula(benunit, period, parameters):
        ctr = parameters(period).gov.local_authorities.islington.council_tax_reduction
        local_authority = benunit.household("local_authority", period)
        country = benunit.household("country", period)
        has_pensioner = benunit.household(
            "council_tax_reduction_household_has_pensioner", period
        )
        working_age = is_islington_working_age(local_authority, country, has_pensioner)
        weekly_net_earnings = benunit(
            "islington_council_tax_reduction_weekly_net_earnings", period
        )
        person = benunit.members
        num_children = benunit.sum(
            person("is_child_or_qualifying_young_person_for_child_benefit", period)
        )
        is_couple = benunit("is_couple", period)
        income_bands = ctr.income_band
        working_support_rate = select(
            [
                is_couple & (num_children >= 2),
                ((~is_couple) & (num_children >= 2))
                | (is_couple & (num_children == 1)),
                ((~is_couple) & (num_children == 1))
                | (is_couple & (num_children == 0)),
            ],
            [
                income_bands.couple_two_or_more_children.calc(weekly_net_earnings),
                income_bands.single_two_or_more_children_or_couple_one_child.calc(
                    weekly_net_earnings
                ),
                income_bands.single_one_child_or_couple_no_children.calc(
                    weekly_net_earnings
                ),
            ],
            default=income_bands.single_no_children.calc(weekly_net_earnings),
        )
        non_working_protected = benunit(
            "islington_council_tax_reduction_non_working_protected", period
        )
        non_working_support_rate = where(
            non_working_protected,
            ctr.non_working.protected_support_rate,
            ctr.non_working.default_support_rate,
        )
        support_rate = where(
            weekly_net_earnings <= 0,
            non_working_support_rate,
            working_support_rate,
        )
        liability = benunit.household("council_tax", period)
        non_dep_deductions = benunit(
            "islington_council_tax_reduction_non_dep_deductions", period
        )
        award = max_(0, liability * support_rate - non_dep_deductions)
        capital_eligible = (
            benunit.household("savings", period) < ctr.means_test.capital_limit
        )
        return (
            working_age
            * benunit("benunit_contains_household_head", period)
            * benunit("would_claim_council_tax_reduction", period)
            * capital_eligible
            * award
        )
