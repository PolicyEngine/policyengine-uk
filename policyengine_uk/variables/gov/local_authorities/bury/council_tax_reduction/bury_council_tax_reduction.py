from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.config import (
    is_bury_working_age,
)


class bury_council_tax_reduction(Variable):
    value_type = float
    entity = BenUnit
    label = "Bury Council Tax Reduction"
    definition_period = YEAR
    unit = GBP

    def formula(benunit, period, parameters):
        ctr = parameters(period).gov.local_authorities.bury.council_tax_reduction
        local_authority = benunit.household("local_authority", period)
        country = benunit.household("country", period)
        has_pensioner = benunit.household(
            "council_tax_reduction_household_has_pensioner", period
        )
        working_age = is_bury_working_age(local_authority, country, has_pensioner)
        gross_earned_income = add(
            benunit,
            period,
            [
                "employment_income",
                "self_employment_income",
            ],
        )
        non_uc_deductions = (
            add(
                benunit,
                period,
                [
                    "income_tax",
                    "national_insurance",
                ],
            )
            + add(benunit, period, ["pension_contributions"]) * 0.5
        )
        non_uc_earnings = max_(0, gross_earned_income - non_uc_deductions)
        uc_gross_earned_income = add(benunit, period, ["uc_mif_capped_earned_income"])
        uc_deductions = add(
            benunit,
            period,
            [
                "income_tax",
                "national_insurance",
                "pension_contributions",
            ],
        )
        uc_earnings = max_(0, uc_gross_earned_income - uc_deductions)
        has_uc_award = benunit("universal_credit", period) > 0
        annual_earnings = where(has_uc_award, uc_earnings, non_uc_earnings)
        monthly_earnings = annual_earnings / MONTHS_IN_YEAR
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
                income_bands.single_two_or_more_children.calc(monthly_earnings),
                income_bands.single_one_child.calc(monthly_earnings),
                income_bands.couple_two_or_more_children.calc(monthly_earnings),
                income_bands.couple_one_child.calc(monthly_earnings),
                income_bands.couple.calc(monthly_earnings),
            ],
            default=income_bands.single.calc(monthly_earnings),
        )
        liability = benunit.household(
            "bury_council_tax_reduction_maximum_eligible_liability", period
        )
        non_dep_deductions = benunit(
            "bury_council_tax_reduction_non_dep_deductions", period
        )
        award = max_(0, liability * support_rate - non_dep_deductions)
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
