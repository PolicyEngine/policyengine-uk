from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.config import (
    is_croydon_working_age,
)


class croydon_council_tax_reduction(Variable):
    value_type = float
    entity = BenUnit
    label = "Croydon Council Tax Support"
    definition_period = YEAR
    unit = GBP

    def formula(benunit, period, parameters):
        ctr = parameters(period).gov.local_authorities.croydon.council_tax_reduction
        local_authority = benunit.household("local_authority", period)
        country = benunit.household("country", period)
        has_pensioner = benunit.household(
            "council_tax_reduction_household_has_pensioner", period
        )
        working_age = is_croydon_working_age(local_authority, country, has_pensioner)
        weekly_income = benunit("croydon_council_tax_reduction_weekly_income", period)
        disabled_not_working = benunit(
            "croydon_council_tax_reduction_disabled_not_working", period
        )
        lone_parent_child_under_5 = benunit(
            "croydon_council_tax_reduction_lone_parent_child_under_5", period
        )
        support_rate = select(
            [
                disabled_not_working,
                lone_parent_child_under_5,
            ],
            [
                ctr.income_band.disabled_not_working.calc(weekly_income),
                ctr.income_band.lone_parent_child_under_5.calc(weekly_income),
            ],
            default=ctr.income_band.standard.calc(weekly_income),
        )
        liability = benunit.household(
            "croydon_council_tax_reduction_maximum_eligible_liability", period
        )
        non_dep_deductions = benunit(
            "croydon_council_tax_reduction_non_dep_deductions", period
        )
        award = max_(0, liability * support_rate - non_dep_deductions)
        capital = benunit("croydon_council_tax_reduction_assessable_capital", period)
        capital_limit = where(
            disabled_not_working,
            ctr.means_test.capital_limit.disabled_not_working,
            ctr.means_test.capital_limit.standard,
        )
        capital_eligible = capital < capital_limit
        return (
            working_age
            * benunit("benunit_contains_household_head", period)
            * benunit("would_claim_council_tax_reduction", period)
            * capital_eligible
            * award
        )
