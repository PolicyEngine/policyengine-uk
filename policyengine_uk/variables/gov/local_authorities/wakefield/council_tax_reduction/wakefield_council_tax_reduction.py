from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.config import (
    is_wakefield_working_age,
)


class wakefield_council_tax_reduction(Variable):
    value_type = float
    entity = BenUnit
    label = "Wakefield Council Tax Support"
    definition_period = YEAR
    unit = GBP

    def formula(benunit, period, parameters):
        ctr = parameters(period).gov.local_authorities.wakefield.council_tax_reduction
        local_authority = benunit.household("local_authority", period)
        country = benunit.household("country", period)
        has_pensioner = benunit.household(
            "council_tax_reduction_household_has_pensioner", period
        )
        working_age = is_wakefield_working_age(local_authority, country, has_pensioner)
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
        other_non_dwp_income = add(
            benunit,
            period,
            [
                "property_income",
                "private_pension_income",
                "savings_interest_income",
                "dividend_income",
            ],
        )
        non_dwp_income = max_(0, earned_income - earnings_deductions)
        non_dwp_income += other_non_dwp_income
        weekly_income = non_dwp_income / WEEKS_IN_YEAR
        support_rate = ctr.income_band.maximum_support_rate.calc(weekly_income)
        liability = benunit.household("council_tax", period)
        non_dep_deductions = benunit(
            "wakefield_council_tax_reduction_non_dep_deductions", period
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
