from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.config import (
    is_tameside_working_age,
)


class tameside_council_tax_reduction(Variable):
    value_type = float
    entity = BenUnit
    label = "Tameside Council Tax Reduction"
    definition_period = YEAR
    unit = GBP

    def formula(benunit, period, parameters):
        ctr = parameters(period).gov.local_authorities.tameside.council_tax_reduction
        local_authority = benunit.household("local_authority", period)
        country = benunit.household("country", period)
        has_pensioner = benunit.household(
            "council_tax_reduction_household_has_pensioner", period
        )
        working_age = is_tameside_working_age(local_authority, country, has_pensioner)
        earned_income = add(
            benunit,
            period,
            [
                "employment_income",
                "self_employment_income",
            ],
        )
        earnings_deductions = add(
            benunit,
            period,
            [
                "income_tax",
                "national_insurance",
                "pension_contributions",
            ],
        )
        other_income = add(
            benunit,
            period,
            [
                "property_income",
                "private_pension_income",
                "savings_interest_income",
                "dividend_income",
            ],
        )
        weekly_income = max_(0, earned_income - earnings_deductions) + other_income
        weekly_income /= WEEKS_IN_YEAR
        num_children = benunit("num_children", period)
        is_couple = benunit("is_couple", period)
        is_lone_parent = benunit("is_lone_parent", period)
        income_bands = ctr.income_band
        support_rate = select(
            [
                is_lone_parent & (num_children >= 2),
                is_lone_parent & (num_children == 1),
                is_couple & (num_children >= 2),
                is_couple & (num_children == 1),
                is_couple,
            ],
            [
                income_bands.lone_parent_two_or_more_children.calc(weekly_income),
                income_bands.lone_parent_one_child.calc(weekly_income),
                income_bands.couple_two_or_more_children.calc(weekly_income),
                income_bands.couple_one_child.calc(weekly_income),
                income_bands.couple.calc(weekly_income),
            ],
            default=income_bands.single.calc(weekly_income),
        )
        relevant_income_based_benefit = benunit(
            "council_tax_reduction_relevant_income_based_benefit",
            period,
        )
        support_rate = where(
            relevant_income_based_benefit,
            income_bands.single.calc(0),
            support_rate,
        )
        liability = benunit.household(
            "tameside_council_tax_reduction_maximum_eligible_liability", period
        )
        award = liability * support_rate
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
