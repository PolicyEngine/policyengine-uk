from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.config import (
    is_lambeth_working_age,
)


class lambeth_council_tax_reduction(Variable):
    value_type = float
    entity = BenUnit
    label = "Lambeth Council Tax Reduction"
    definition_period = YEAR
    unit = GBP

    def formula(benunit, period, parameters):
        ctr = parameters(period).gov.local_authorities.lambeth.council_tax_reduction
        local_authority = benunit.household("local_authority", period)
        country = benunit.household("country", period)
        has_pensioner = benunit.household(
            "council_tax_reduction_household_has_pensioner", period
        )
        working_age = is_lambeth_working_age(local_authority, country, has_pensioner)
        person = benunit.members
        claimant_or_partner = person("is_adult", period)
        gross_earned_income = benunit.sum(
            claimant_or_partner
            * (
                person("employment_income", period)
                + person("self_employment_income", period)
            )
        )
        earnings_deductions = benunit.sum(
            claimant_or_partner
            * (
                person("income_tax", period)
                + person("national_insurance", period)
                + person("pension_contributions", period) * 0.5
            )
        )
        weekly_net_earnings = (
            max_(0, gross_earned_income - earnings_deductions) / WEEKS_IN_YEAR
        )
        num_children = benunit("num_children", period)
        income_bands = ctr.income_band
        support_rate = select(
            [
                num_children >= 5,
                num_children == 4,
                num_children == 3,
                num_children == 2,
                num_children == 1,
            ],
            [
                income_bands.five_or_more_children.calc(weekly_net_earnings),
                income_bands.four_children.calc(weekly_net_earnings),
                income_bands.three_children.calc(weekly_net_earnings),
                income_bands.two_children.calc(weekly_net_earnings),
                income_bands.one_child.calc(weekly_net_earnings),
            ],
            default=income_bands.no_children.calc(weekly_net_earnings),
        )
        liability = benunit.household("council_tax", period)
        non_dep_deductions = benunit(
            "lambeth_council_tax_reduction_non_dep_deductions", period
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
