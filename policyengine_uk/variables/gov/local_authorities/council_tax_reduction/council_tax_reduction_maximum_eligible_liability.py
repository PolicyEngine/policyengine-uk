from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.config import (
    ENGLISH_BAND_C_RATIO,
    english_council_tax_band_ratio,
    is_dudley,
)
from policyengine_uk.variables.household.demographic.country import Country


class council_tax_reduction_maximum_eligible_liability(Variable):
    value_type = float
    entity = Household
    label = "Maximum Council Tax liability eligible for CTR"
    definition_period = YEAR
    unit = GBP

    def formula(household, period, parameters):
        council_tax = household("council_tax", period)
        local_authority = household("local_authority", period)
        country = household("country", period)
        council_tax_band = household("council_tax_band", period)
        has_pensioner = household(
            "council_tax_reduction_household_has_pensioner", period
        )

        band_ratio = english_council_tax_band_ratio(council_tax_band)
        band_c_liability = council_tax * ENGLISH_BAND_C_RATIO / band_ratio
        dudley_working_age = (
            (country == Country.ENGLAND)
            & ~has_pensioner
            & is_dudley(local_authority)
        )
        capped = dudley_working_age & (band_ratio > ENGLISH_BAND_C_RATIO)
        return where(capped, band_c_liability, council_tax)
