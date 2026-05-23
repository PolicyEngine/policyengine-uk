from policyengine_uk.model_api import *


class arun_council_tax_reduction(Variable):
    value_type = float
    entity = BenUnit
    label = "Arun Council Tax Reduction"
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.arun.gov.uk/download.cfm?doc=docm93jijm4n20657.pdf&ver=27819"
    )

    def formula(benunit, period, parameters):
        ctr = parameters(period).gov.local_authorities.arun.council_tax_reduction
        local_scheme = benunit("arun_council_tax_reduction_is_local_scheme", period)
        liability = benunit.household("council_tax", period)
        non_dep_deductions = benunit(
            "arun_council_tax_reduction_non_dep_deductions", period
        )
        eligible_liability = max_(0, liability - non_dep_deductions)
        support_rate = benunit("arun_council_tax_reduction_support_rate", period)
        preliminary_award = eligible_liability * support_rate
        annual_minimum_award = ctr.means_test.minimum_award * WEEKS_IN_YEAR
        award = where(preliminary_award >= annual_minimum_award, preliminary_award, 0)
        has_uc_award = benunit("universal_credit", period) > 0
        capital = where(
            has_uc_award,
            benunit("uc_assessable_capital", period),
            benunit.household("savings", period),
        )
        relevant_income_based_benefit = benunit(
            "council_tax_reduction_relevant_income_based_benefit", period
        )
        capital_eligible = relevant_income_based_benefit | (
            capital <= ctr.means_test.capital_limit
        )
        return (
            local_scheme
            * benunit("benunit_contains_household_head", period)
            * benunit("would_claim_council_tax_reduction", period)
            * capital_eligible
            * max_(0, award)
        )
