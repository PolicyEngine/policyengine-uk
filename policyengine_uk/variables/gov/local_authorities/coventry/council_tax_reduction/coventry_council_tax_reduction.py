from policyengine_uk.model_api import *


class coventry_council_tax_reduction(Variable):
    value_type = float
    entity = BenUnit
    label = "Coventry Council Tax Reduction"
    definition_period = YEAR
    unit = GBP
    reference = "https://www.coventry.gov.uk/downloads/file/46761/council-tax-support-scheme-2026-to-2027"

    def formula(benunit, period, parameters):
        ctr = parameters(period).gov.local_authorities.coventry.council_tax_reduction
        local_scheme = benunit("coventry_council_tax_reduction_is_local_scheme", period)
        has_uc_award = (
            max_(
                benunit("universal_credit_pre_benefit_cap", period),
                benunit("universal_credit", period),
            )
            > 0
        )
        support_rate = benunit("coventry_council_tax_reduction_support_rate", period)
        liability = benunit.household("council_tax", period)
        non_dep_deductions = benunit(
            "coventry_council_tax_reduction_non_dep_deductions", period
        )
        award = max_(0, liability * support_rate - non_dep_deductions)
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
