from policyengine_uk.model_api import *


class south_derbyshire_council_tax_reduction(Variable):
    value_type = float
    entity = BenUnit
    label = "South Derbyshire Council Tax Reduction"
    definition_period = YEAR
    unit = GBP
    reference = "https://www.southderbyshire.gov.uk/assets/attach/15700/South-Derbyshire-CTR-scheme-2026-2027.pdf"

    def formula(benunit, period, parameters):
        ctr = parameters(
            period
        ).gov.local_authorities.south_derbyshire.council_tax_reduction
        local_scheme = benunit(
            "south_derbyshire_council_tax_reduction_is_local_scheme", period
        )
        has_uc_award = (
            max_(
                benunit("universal_credit_pre_benefit_cap", period),
                benunit("universal_credit", period),
            )
            > 0
        )
        support_rate = benunit(
            "south_derbyshire_council_tax_reduction_support_rate", period
        )
        liability = benunit.household("council_tax", period)
        non_dep_deductions = benunit(
            "south_derbyshire_council_tax_reduction_non_dep_deductions",
            period,
        )
        award = max_(0, liability - non_dep_deductions) * support_rate
        annual_minimum_award = ctr.means_test.minimum_award * WEEKS_IN_YEAR
        award = where(award >= annual_minimum_award, award, 0)
        relevant_income_based_benefit = benunit(
            "council_tax_reduction_relevant_income_based_benefit",
            period,
        )
        non_uc_capital_eligible = (
            benunit("south_derbyshire_council_tax_reduction_assessable_capital", period)
            <= ctr.means_test.capital_limit
        ) | relevant_income_based_benefit
        uc_capital_eligible = (
            benunit("uc_assessable_capital", period) <= ctr.means_test.capital_limit
        )
        capital_eligible = where(
            has_uc_award,
            uc_capital_eligible,
            non_uc_capital_eligible,
        )
        return (
            local_scheme
            * benunit("benunit_contains_household_head", period)
            * benunit("would_claim_council_tax_reduction", period)
            * capital_eligible
            * award
        )
