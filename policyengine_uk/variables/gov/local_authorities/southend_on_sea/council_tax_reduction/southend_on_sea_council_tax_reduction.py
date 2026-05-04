from policyengine_uk.model_api import *


class southend_on_sea_council_tax_reduction(Variable):
    value_type = float
    entity = BenUnit
    label = "Southend-on-Sea Council Tax Reduction"
    definition_period = YEAR
    unit = GBP

    def formula(benunit, period, parameters):
        ctr = parameters(
            period
        ).gov.local_authorities.southend_on_sea.council_tax_reduction
        local_scheme = benunit(
            "southend_on_sea_council_tax_reduction_is_local_scheme", period
        )
        support_rate = benunit(
            "southend_on_sea_council_tax_reduction_support_rate", period
        )
        liability = benunit.household("council_tax", period)
        uc_award_before_deductions = max_(
            benunit("universal_credit_pre_benefit_cap", period),
            benunit("universal_credit", period),
        )
        has_uc_award = uc_award_before_deductions > 0
        non_uc_capital_eligible = (
            benunit.household("savings", period) < ctr.means_test.capital_limit
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
