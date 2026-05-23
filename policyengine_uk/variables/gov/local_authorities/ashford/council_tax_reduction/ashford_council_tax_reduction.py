from policyengine_uk.model_api import *


class ashford_council_tax_reduction(Variable):
    value_type = float
    entity = BenUnit
    label = "Ashford Council Tax Reduction"
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.ashford.gov.uk/media/0n4nud13/ashford-ctr-scheme-2026-final.pdf"
    )

    def formula(benunit, period, parameters):
        ctr = parameters(period).gov.local_authorities.ashford.council_tax_reduction
        local_scheme = benunit("ashford_council_tax_reduction_is_local_scheme", period)
        liability = benunit.household(
            "ashford_council_tax_reduction_maximum_eligible_liability", period
        )
        non_dep_deductions = benunit(
            "ashford_council_tax_reduction_non_dep_deductions", period
        )
        support_rate = benunit("ashford_council_tax_reduction_support_rate", period)
        has_uc_award = benunit("universal_credit", period) > 0
        capital = where(
            has_uc_award,
            benunit("uc_assessable_capital", period),
            benunit.household("savings", period),
        )
        capital_eligible = capital <= ctr.means_test.capital_limit
        award = max_(0, liability * support_rate - non_dep_deductions)
        return (
            local_scheme
            * benunit("benunit_contains_household_head", period)
            * benunit("would_claim_council_tax_reduction", period)
            * capital_eligible
            * award
        )
