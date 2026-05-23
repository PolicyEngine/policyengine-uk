from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.config import (
    is_ealing_working_age,
)


class ealing_council_tax_reduction(Variable):
    value_type = float
    entity = BenUnit
    label = "Ealing Council Tax Reduction"
    definition_period = YEAR
    unit = GBP

    def formula(benunit, period, parameters):
        ctr = parameters(period).gov.local_authorities.ealing.council_tax_reduction
        local_authority = benunit.household("local_authority", period)
        country = benunit.household("country", period)
        has_pensioner = benunit.household(
            "council_tax_reduction_household_has_pensioner", period
        )
        working_age = is_ealing_working_age(local_authority, country, has_pensioner)
        weekly_income = benunit("ealing_council_tax_reduction_weekly_income", period)
        protected = benunit("ealing_council_tax_reduction_protected", period)
        support_rate = where(
            protected,
            ctr.income_band.protected.calc(weekly_income),
            ctr.income_band.non_protected.calc(weekly_income),
        )
        liability = benunit.household("council_tax", period)
        non_dep_deductions = benunit(
            "ealing_council_tax_reduction_non_dep_deductions", period
        )
        award = max_(0, liability * support_rate - non_dep_deductions)
        award = where(award < ctr.minimum_award * WEEKS_IN_YEAR, 0, award)
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
