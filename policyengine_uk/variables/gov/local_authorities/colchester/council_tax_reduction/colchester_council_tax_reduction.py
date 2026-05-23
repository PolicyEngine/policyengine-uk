from policyengine_uk.model_api import *


class colchester_council_tax_reduction(Variable):
    value_type = float
    entity = BenUnit
    label = "Colchester Council Tax Reduction"
    definition_period = YEAR
    unit = GBP

    def formula(benunit, period, parameters):
        ctr = parameters(period).gov.local_authorities.colchester.council_tax_reduction
        local_scheme = benunit(
            "colchester_council_tax_reduction_is_local_scheme", period
        )
        support_rate = benunit("colchester_council_tax_reduction_support_rate", period)
        liability = benunit.household(
            "colchester_council_tax_reduction_maximum_eligible_liability", period
        )
        has_uc_award = benunit("universal_credit", period) > 0
        non_uc_capital_eligible = (
            benunit("colchester_council_tax_reduction_assessable_capital", period)
            < ctr.means_test.capital_limit
        )
        uc_capital_eligible = (
            benunit("uc_assessable_capital", period) < ctr.means_test.capital_limit
        )
        capital_eligible = where(
            has_uc_award, uc_capital_eligible, non_uc_capital_eligible
        )
        return (
            local_scheme
            * benunit("benunit_contains_household_head", period)
            * benunit("would_claim_council_tax_reduction", period)
            * capital_eligible
            * liability
            * support_rate
        )
