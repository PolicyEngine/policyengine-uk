from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.config import (
    english_council_tax_band_ratio,
    is_warrington_working_age,
    is_dudley_working_age,
)


class council_tax_reduction_maximum_eligible_liability(Variable):
    value_type = float
    entity = Household
    label = "Maximum Council Tax liability eligible for CTR"
    definition_period = YEAR
    unit = GBP

    def formula(household, period, parameters):
        england_council_tax = parameters(period).gov.local_authorities.england.council_tax
        dudley_ctr = parameters(
            period
        ).gov.local_authorities.dudley.council_tax_reduction
        warrington_ctr = parameters(
            period
        ).gov.local_authorities.warrington.council_tax_reduction
        council_tax = household("council_tax", period)
        local_authority = household("local_authority", period)
        country = household("country", period)
        council_tax_band = household("council_tax_band", period)
        has_pensioner = household(
            "council_tax_reduction_household_has_pensioner", period
        )
        person = household.members
        claimant_benunit = person.benunit("benunit_contains_household_head", period)
        claimant_income_below_applicable_amount = household.any(
            claimant_benunit
            & person.benunit(
                "council_tax_reduction_income_below_applicable_amount",
                period,
            )
        )

        band_ratio = english_council_tax_band_ratio(
            council_tax_band,
            england_council_tax.band_ratio,
        )
        dudley_cap_band_ratio = dudley_ctr.maximum_liability.cap_band_ratio
        warrington_cap_band_ratio = warrington_ctr.maximum_liability.cap_band_ratio
        band_c_liability = council_tax * dudley_cap_band_ratio / band_ratio
        band_a_liability = council_tax * warrington_cap_band_ratio / band_ratio
        dudley_working_age = is_dudley_working_age(
            local_authority,
            country,
            has_pensioner,
        )
        warrington_working_age = is_warrington_working_age(
            local_authority,
            country,
            has_pensioner,
        )
        dudley_capped = dudley_working_age & (band_ratio > dudley_cap_band_ratio)
        warrington_capped = (
            warrington_working_age
            & ~claimant_income_below_applicable_amount
            & (band_ratio > warrington_cap_band_ratio)
        )
        capped_liability = where(dudley_capped, band_c_liability, council_tax)
        return where(warrington_capped, band_a_liability, capped_liability)
