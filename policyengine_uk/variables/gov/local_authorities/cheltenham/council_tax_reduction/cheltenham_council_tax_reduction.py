from policyengine_uk.model_api import *


class cheltenham_council_tax_reduction(Variable):
    value_type = float
    entity = BenUnit
    label = "Cheltenham Council Tax Support"
    definition_period = YEAR
    unit = GBP
    reference = "https://democracy.cheltenham.gov.uk/documents/s53359/Appendix%209%20-%20Council%20270226%20Council%20Tax%20Support%20Scheme%20for%20Working%20Age%20Customers%202026-27%20Final.pdf"

    def formula(benunit, period, parameters):
        ctr = parameters(period).gov.local_authorities.cheltenham.council_tax_reduction
        local_scheme = benunit(
            "cheltenham_council_tax_reduction_is_local_scheme", period
        )
        liability = benunit.household(
            "cheltenham_council_tax_reduction_maximum_eligible_liability", period
        )
        non_dep_deductions = benunit(
            "cheltenham_council_tax_reduction_non_dep_deductions", period
        )
        eligible_liability = max_(0, liability - non_dep_deductions)
        support_rate = benunit("cheltenham_council_tax_reduction_support_rate", period)
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
            * eligible_liability
            * support_rate
        )
