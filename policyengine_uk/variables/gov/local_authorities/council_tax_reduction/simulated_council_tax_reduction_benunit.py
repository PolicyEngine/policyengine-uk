from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.config import (
    CAPITAL_LIMIT_GBP,
    CLASSIC_WITHDRAWAL_RATE,
    maximum_support_rate,
)


class simulated_council_tax_reduction_benunit(Variable):
    value_type = float
    entity = BenUnit
    label = "Simulated Council Tax Reduction"
    definition_period = YEAR
    unit = GBP

    def formula(benunit, period, parameters):
        supported = benunit.household("council_tax_reduction_scheme_supported", period)
        is_household_head_benunit = benunit("benunit_contains_household_head", period)
        would_claim = benunit("would_claim_council_tax_reduction", period)
        local_authority = benunit.household("local_authority", period)
        country = benunit.household("country", period)
        has_pensioner = benunit.household(
            "council_tax_reduction_household_has_pensioner", period
        )

        max_support = maximum_support_rate(
            local_authority, country, has_pensioner
        )
        liability = benunit.household(
            "council_tax_reduction_maximum_eligible_liability", period
        )
        applicable_amount = benunit("council_tax_reduction_applicable_amount", period)
        applicable_income = benunit("council_tax_reduction_applicable_income", period)
        non_dep_deductions = benunit(
            "council_tax_reduction_non_dep_deductions", period
        )
        excess_income = max_(0, applicable_income - applicable_amount)
        preliminary_award = max_(
            0,
            liability * max_support
            - excess_income * CLASSIC_WITHDRAWAL_RATE
            - non_dep_deductions,
        )
        capital_eligible = benunit.household("savings", period) <= CAPITAL_LIMIT_GBP
        return (
            supported
            * is_household_head_benunit
            * would_claim
            * capital_eligible
            * preliminary_award
        )
