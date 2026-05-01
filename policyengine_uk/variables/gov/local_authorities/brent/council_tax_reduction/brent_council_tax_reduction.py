from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.config import (
    is_brent_working_age,
)


class brent_council_tax_reduction(Variable):
    value_type = float
    entity = BenUnit
    label = "Brent Council Tax Support"
    definition_period = YEAR
    unit = GBP

    def formula(benunit, period, parameters):
        ctr = parameters(period).gov.local_authorities.brent.council_tax_reduction
        local_authority = benunit.household("local_authority", period)
        country = benunit.household("country", period)
        has_pensioner = benunit.household(
            "council_tax_reduction_household_has_pensioner", period
        )
        working_age = is_brent_working_age(local_authority, country, has_pensioner)
        weekly_earnings = benunit("brent_council_tax_reduction_weekly_earnings", period)
        support_rate = ctr.income_band.support_rate.calc(weekly_earnings)
        liability = benunit.household("council_tax", period)
        non_dep_deductions = benunit(
            "brent_council_tax_reduction_non_dep_deductions", period
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
