from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.config import (
    is_camden_working_age,
)


class camden_council_tax_reduction(Variable):
    value_type = float
    entity = BenUnit
    label = "Camden Council Tax Support"
    definition_period = YEAR
    unit = GBP

    def formula(benunit, period, parameters):
        ctr = parameters(period).gov.local_authorities.camden.council_tax_reduction
        local_authority = benunit.household("local_authority", period)
        country = benunit.household("country", period)
        has_pensioner = benunit.household(
            "council_tax_reduction_household_has_pensioner", period
        )
        working_age = is_camden_working_age(local_authority, country, has_pensioner)
        person = benunit.members
        claimant_or_partner = person("is_adult", period)
        gross_earnings = benunit.sum(
            claimant_or_partner
            * (
                person("employment_income", period)
                + person("self_employment_income", period)
            )
        )
        childcare_deduction = benunit(
            "camden_council_tax_reduction_childcare_deduction", period
        )
        weekly_gross_earnings = (
            max_(0, gross_earnings - childcare_deduction) / WEEKS_IN_YEAR
        )
        income_bands = ctr.income_band
        has_children = benunit("num_children", period) > 0
        protected_group = benunit(
            "camden_council_tax_reduction_protected_group", period
        )
        support_rate = select(
            [
                protected_group,
                has_children,
            ],
            [
                income_bands.disabled_or_carer.calc(weekly_gross_earnings),
                income_bands.with_children.calc(weekly_gross_earnings),
            ],
            default=income_bands.no_children.calc(weekly_gross_earnings),
        )
        liability = benunit.household("council_tax", period)
        non_dep_deductions = benunit(
            "camden_council_tax_reduction_non_dep_deductions", period
        )
        award = max_(0, liability * support_rate - non_dep_deductions)
        capital = benunit("camden_council_tax_reduction_assessable_capital", period)
        capital_eligible = capital < ctr.means_test.capital_limit
        return (
            working_age
            * benunit("benunit_contains_household_head", period)
            * benunit("would_claim_council_tax_reduction", period)
            * capital_eligible
            * award
        )
