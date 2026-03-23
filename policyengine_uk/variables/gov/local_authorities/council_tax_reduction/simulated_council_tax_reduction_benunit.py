from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.config import (
    is_chesterfield_working_age,
    is_east_hertfordshire_working_age,
    is_england_pensioner_scheme,
    is_dudley_working_age,
    is_scotland_scheme,
    is_stevenage_working_age,
    is_stroud_working_age,
    is_warrington_working_age,
    is_wales_scheme,
)
from policyengine_uk.variables.input.council_tax_band import CouncilTaxBand


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
        wales_ctr = local_authority_parameters.wales.council_tax_reduction
        scotland_ctr = local_authority_parameters.scotland.council_tax_reduction
        chesterfield_ctr = local_authority_parameters.chesterfield.council_tax_reduction
        east_herts_ctr = (
            local_authority_parameters.east_hertfordshire.council_tax_reduction
        )
        stevenage_ctr = local_authority_parameters.stevenage.council_tax_reduction
        stroud_ctr = local_authority_parameters.stroud.council_tax_reduction
        warrington_ctr = local_authority_parameters.warrington.council_tax_reduction
        dudley_ctr = local_authority_parameters.dudley.council_tax_reduction
        supported = benunit.household("council_tax_reduction_scheme_supported", period)
        is_household_head_benunit = benunit("benunit_contains_household_head", period)
        would_claim = benunit("would_claim_council_tax_reduction", period)
        local_authority = benunit.household("local_authority", period)
        country = benunit.household("country", period)
        council_tax_band = benunit.household("council_tax_band", period)
        has_pensioner = benunit.household(
            "council_tax_reduction_household_has_pensioner", period
        )
        applicable_amount = benunit("council_tax_reduction_applicable_amount", period)
        applicable_income = benunit("council_tax_reduction_applicable_income", period)
        income_below_applicable_amount = benunit(
            "council_tax_reduction_income_below_applicable_amount",
            period,
        )

        england_pensioners = is_england_pensioner_scheme(country, has_pensioner)
        wales = is_wales_scheme(country)
        scotland = is_scotland_scheme(country)
        chesterfield_working_age = is_chesterfield_working_age(
            local_authority,
            country,
            has_pensioner,
        )
        east_herts_working_age = is_east_hertfordshire_working_age(
            local_authority,
            country,
            has_pensioner,
        )
        stevenage_working_age = is_stevenage_working_age(
            local_authority,
            country,
            has_pensioner,
        )
        stroud_working_age = is_stroud_working_age(
            local_authority,
            country,
            has_pensioner,
        )
        warrington_working_age = is_warrington_working_age(
            local_authority,
            country,
            has_pensioner,
        )
        dudley_working_age = is_dudley_working_age(
            local_authority,
            country,
            has_pensioner,
        )
        warrington_band_a = council_tax_band == CouncilTaxBand.A
        warrington_class_d = warrington_working_age & income_below_applicable_amount
        warrington_max_support = select(
            [
                warrington_class_d & warrington_band_a,
                warrington_class_d,
            ],
            [
                warrington_ctr.maximum_support_rate.class_d.band_a,
                warrington_ctr.maximum_support_rate.class_d.other_bands,
            ],
            default=warrington_ctr.maximum_support_rate.class_e,
        )
        max_support = select(
            [
                england_pensioners,
                wales,
                scotland,
                chesterfield_working_age,
                east_herts_working_age,
                stevenage_working_age,
                stroud_working_age,
                warrington_working_age,
                dudley_working_age,
            ],
            [
                england_pensioners_ctr.maximum_support_rate,
                wales_ctr.maximum_support_rate,
                scotland_ctr.maximum_support_rate,
                chesterfield_ctr.maximum_support_rate,
                east_herts_ctr.maximum_support_rate,
                stevenage_ctr.maximum_support_rate,
                stroud_ctr.maximum_support_rate,
                warrington_max_support,
                dudley_ctr.maximum_support_rate,
            ],
            default=0.0,
        )
        liability = benunit.household(
            "council_tax_reduction_maximum_eligible_liability", period
        )
        non_dep_deductions = benunit("council_tax_reduction_non_dep_deductions", period)
        withdrawal_rate = select(
            [
                england_pensioners,
                wales,
                scotland,
                chesterfield_working_age,
                east_herts_working_age,
                stevenage_working_age,
                stroud_working_age,
                warrington_working_age,
                dudley_working_age,
            ],
            [
                england_pensioners_ctr.means_test.withdrawal_rate,
                wales_ctr.means_test.withdrawal_rate,
                scotland_ctr.means_test.withdrawal_rate,
                chesterfield_ctr.means_test.withdrawal_rate,
                east_herts_ctr.means_test.withdrawal_rate,
                stevenage_ctr.means_test.withdrawal_rate,
                stroud_ctr.means_test.withdrawal_rate,
                warrington_ctr.means_test.withdrawal_rate,
                dudley_ctr.means_test.withdrawal_rate,
            ],
            default=0.0,
        )
        capital_limit = select(
            [
                england_pensioners,
                wales,
                scotland,
                chesterfield_working_age,
                east_herts_working_age,
                stevenage_working_age,
                stroud_working_age,
                warrington_working_age,
                dudley_working_age,
            ],
            [
                england_pensioners_ctr.means_test.capital_limit,
                wales_ctr.means_test.capital_limit,
                scotland_ctr.means_test.capital_limit,
                chesterfield_ctr.means_test.capital_limit,
                east_herts_ctr.means_test.capital_limit,
                stevenage_ctr.means_test.capital_limit,
                stroud_ctr.means_test.capital_limit,
                warrington_ctr.means_test.capital_limit,
                dudley_ctr.means_test.capital_limit,
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
        return (
            supported
            * is_household_head_benunit
            * would_claim
            * capital_eligible
            * preliminary_award
        )
