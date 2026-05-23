from policyengine_uk.model_api import *


class dartford_council_tax_reduction(Variable):
    value_type = float
    entity = BenUnit
    label = "Dartford Council Tax Reduction"
    definition_period = YEAR
    unit = GBP
    reference = "https://www.dartford.gov.uk/downloads/file/2814/local-council-tax-reduction-scheme-dbc-2026-2027"

    def formula(benunit, period, parameters):
        ctr = parameters(period).gov.local_authorities.dartford.council_tax_reduction
        local_scheme = benunit("dartford_council_tax_reduction_is_local_scheme", period)
        liability = benunit.household("council_tax", period)
        non_dep_deductions = benunit(
            "dartford_council_tax_reduction_non_dep_deductions", period
        )
        support_rate = benunit("dartford_council_tax_reduction_support_rate", period)
        eligible_liability = max_(0, liability - non_dep_deductions)
        preliminary_award = eligible_liability * support_rate
        annual_minimum_award = ctr.means_test.minimum_award * WEEKS_IN_YEAR
        award = where(preliminary_award >= annual_minimum_award, preliminary_award, 0)
        has_uc_award = benunit("universal_credit", period) > 0
        capital = where(
            has_uc_award,
            benunit("uc_assessable_capital", period),
            benunit.household("savings", period),
        )
        capital_eligible = capital <= ctr.means_test.capital_limit
        return (
            local_scheme
            * benunit("benunit_contains_household_head", period)
            * benunit("would_claim_council_tax_reduction", period)
            * capital_eligible
            * award
        )
