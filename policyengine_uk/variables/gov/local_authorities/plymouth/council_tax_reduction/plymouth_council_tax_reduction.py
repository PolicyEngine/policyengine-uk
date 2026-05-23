from policyengine_uk.model_api import *


class plymouth_council_tax_reduction(Variable):
    value_type = float
    entity = BenUnit
    label = "Plymouth Council Tax Support"
    definition_period = YEAR
    unit = GBP

    def formula(benunit, period, parameters):
        ctr = parameters(period).gov.local_authorities.plymouth.council_tax_reduction
        local_scheme = benunit("plymouth_council_tax_reduction_is_local_scheme", period)
        support_rate = benunit("plymouth_council_tax_reduction_support_rate", period)
        liability = benunit.household(
            "plymouth_council_tax_reduction_maximum_eligible_liability", period
        )
        non_dep_deductions = benunit(
            "plymouth_council_tax_reduction_non_dep_deductions", period
        )
        award = max_(0, liability * support_rate - non_dep_deductions)
        uc_award_before_deductions = max_(
            benunit("universal_credit_pre_benefit_cap", period),
            benunit("universal_credit", period),
        )
        has_uc_award = uc_award_before_deductions > 0
        non_uc_capital_eligible = (
            benunit.household("savings", period) <= ctr.means_test.capital_limit
        )
        uc_capital_eligible = (
            benunit("uc_assessable_capital", period) <= ctr.means_test.capital_limit
        )
        capital_eligible = where(
            has_uc_award, uc_capital_eligible, non_uc_capital_eligible
        )
        return (
            local_scheme
            * benunit("benunit_contains_household_head", period)
            * benunit("would_claim_council_tax_reduction", period)
            * capital_eligible
            * award
        )
