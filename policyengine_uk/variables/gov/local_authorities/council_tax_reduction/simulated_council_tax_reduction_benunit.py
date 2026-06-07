from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.config import (
    is_england_pensioner_scheme,
    is_scotland_scheme,
    is_wales_scheme,
)

LOCAL_COUNCIL_TAX_REDUCTION_VARIABLES = ["merton_council_tax_reduction"]


class simulated_council_tax_reduction_benunit(Variable):
    value_type = float
    entity = BenUnit
    label = "Simulated Council Tax Reduction"
    definition_period = YEAR
    unit = GBP

    def formula(benunit, period, parameters):
        local_authority_parameters = parameters(period).gov.local_authorities
        england_pensioners_ctr = (
            local_authority_parameters.england.council_tax_reduction.pensioners
        )
        scotland_ctr = local_authority_parameters.scotland.council_tax_reduction
        wales_ctr = local_authority_parameters.wales.council_tax_reduction

        country = benunit.household("country", period)
        has_pensioner = benunit.household(
            "council_tax_reduction_household_has_pensioner", period
        )
        england_pensioners = is_england_pensioner_scheme(country, has_pensioner)
        scotland = is_scotland_scheme(country)
        wales = is_wales_scheme(country)
        national_scheme = england_pensioners | scotland | wales

        is_household_head_benunit = benunit("benunit_contains_household_head", period)
        would_claim = benunit("would_claim_council_tax_reduction", period)
        liability = benunit.household(
            "council_tax_reduction_maximum_eligible_liability", period
        )
        applicable_amount = benunit("council_tax_reduction_applicable_amount", period)
        applicable_income = benunit("council_tax_reduction_applicable_income", period)
        non_dep_deductions = benunit("council_tax_reduction_non_dep_deductions", period)

        max_support = select(
            [england_pensioners, scotland, wales],
            [
                england_pensioners_ctr.maximum_support_rate,
                scotland_ctr.maximum_support_rate,
                wales_ctr.maximum_support_rate,
            ],
            default=0.0,
        )
        withdrawal_rate = select(
            [england_pensioners, scotland, wales],
            [
                england_pensioners_ctr.means_test.withdrawal_rate,
                scotland_ctr.means_test.withdrawal_rate,
                wales_ctr.means_test.withdrawal_rate,
            ],
            default=0.0,
        )
        capital_limit = select(
            [england_pensioners, scotland, wales],
            [
                england_pensioners_ctr.means_test.capital_limit,
                scotland_ctr.means_test.capital_limit,
                wales_ctr.means_test.capital_limit,
            ],
            default=0.0,
        )

        excess_income = max_(0, applicable_income - applicable_amount)
        preliminary_award = max_(
            0,
            liability * max_support
            - excess_income * withdrawal_rate
            - non_dep_deductions,
        )
        capital_eligible = benunit.household("savings", period) <= capital_limit
        national_ctr = (
            national_scheme
            * is_household_head_benunit
            * would_claim
            * capital_eligible
            * preliminary_award
        )
        local_ctr = add(benunit, period, LOCAL_COUNCIL_TAX_REDUCTION_VARIABLES)
        return national_ctr + local_ctr
