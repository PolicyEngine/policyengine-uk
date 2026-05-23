from policyengine_uk.model_api import *


class bassetlaw_council_tax_reduction(Variable):
    value_type = float
    entity = BenUnit
    label = "Bassetlaw Council Tax Reduction"
    definition_period = YEAR
    unit = GBP
    reference = "https://www.bassetlaw.gov.uk/media/15ehht0s/council-tax-reduction-scheme-working-age-2026-2027.pdf"

    def formula(benunit, period, parameters):
        ctr = parameters(period).gov.local_authorities.bassetlaw.council_tax_reduction
        local_scheme = benunit(
            "bassetlaw_council_tax_reduction_is_local_scheme", period
        )
        liability = benunit.household(
            "bassetlaw_council_tax_reduction_maximum_eligible_liability", period
        )
        non_dep_deductions = benunit(
            "bassetlaw_council_tax_reduction_non_dep_deductions", period
        )
        support_rate = benunit("bassetlaw_council_tax_reduction_support_rate", period)
        has_uc_award = (
            max_(
                benunit("universal_credit_pre_benefit_cap", period),
                benunit("universal_credit", period),
            )
            > 0
        )
        capital = where(
            has_uc_award,
            benunit("uc_assessable_capital", period),
            benunit.household("savings", period),
        )
        capital_eligible = capital <= ctr.means_test.capital_limit
        award = max_(0, liability - non_dep_deductions) * support_rate
        return (
            local_scheme
            * benunit("benunit_contains_household_head", period)
            * benunit("would_claim_council_tax_reduction", period)
            * capital_eligible
            * award
        )
