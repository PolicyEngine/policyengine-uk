from policyengine_uk.model_api import *


class slough_council_tax_reduction(Variable):
    value_type = float
    entity = BenUnit
    label = "Slough Council Tax Support"
    definition_period = YEAR
    unit = GBP
    reference = "https://www.slough.gov.uk/downloads/file/5730/council-tax-support-scheme-2026-27"

    def formula(benunit, period, parameters):
        ctr = parameters(period).gov.local_authorities.slough.council_tax_reduction
        local_scheme = benunit("slough_council_tax_reduction_is_local_scheme", period)
        support_rate = benunit("slough_council_tax_reduction_support_rate", period)
        liability = benunit.household(
            "slough_council_tax_reduction_maximum_eligible_liability", period
        )
        non_dep_deductions = benunit(
            "slough_council_tax_reduction_non_dep_deductions", period
        )
        award = max_(0, liability * support_rate - non_dep_deductions)
        annual_minimum_award = ctr.means_test.minimum_award * WEEKS_IN_YEAR
        award = where(award >= annual_minimum_award, award, 0)
        capital_eligible = (
            benunit.household("savings", period) <= ctr.means_test.capital_limit
        )
        return (
            local_scheme
            * benunit("benunit_contains_household_head", period)
            * benunit("would_claim_council_tax_reduction", period)
            * capital_eligible
            * award
        )
