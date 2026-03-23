from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.config import (
    english_council_tax_band_ratio,
    is_dudley_working_age,
)


class council_tax_reduction_maximum_eligible_liability(Variable):
    value_type = float
    entity = Household
    label = "Maximum Council Tax liability eligible for CTR"
    definition_period = YEAR
    unit = GBP

    def formula(household, period, parameters):
        dudley_council_tax = parameters(period).gov.local_authorities.dudley.council_tax
        dudley_ctr = parameters(
            period
        ).gov.local_authorities.dudley.council_tax_reduction
        council_tax = household("council_tax", period)
        local_authority = household("local_authority", period)
        country = household("country", period)
        council_tax_band = household("council_tax_band", period)
        has_pensioner = household(
            "council_tax_reduction_household_has_pensioner", period
        )

        band_ratio = english_council_tax_band_ratio(
            council_tax_band,
            dudley_council_tax.band_ratio,
        )
        cap_band_ratio = dudley_ctr.maximum_liability.cap_band_ratio
        band_c_liability = council_tax * cap_band_ratio / band_ratio
        dudley_working_age = is_dudley_working_age(
            local_authority,
            country,
            has_pensioner,
        )
        capped = dudley_working_age & (band_ratio > cap_band_ratio)
        return where(capped, band_c_liability, council_tax)
