from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.config import (
    english_council_tax_band_ratio,
    is_hillingdon_working_age,
)


class hillingdon_council_tax_reduction_maximum_eligible_liability(Variable):
    value_type = float
    entity = Household
    label = "Hillingdon maximum Council Tax liability eligible for CTR"
    definition_period = YEAR
    unit = GBP

    def formula(household, period, parameters):
        england_council_tax = parameters(
            period
        ).gov.local_authorities.england.council_tax
        ctr = parameters(period).gov.local_authorities.hillingdon.council_tax_reduction
        council_tax = household("council_tax", period)
        band_ratio = english_council_tax_band_ratio(
            household("council_tax_band", period),
            england_council_tax.band_ratio,
        )
        cap_band_ratio = ctr.maximum_liability.cap_band_ratio
        capped_liability = council_tax * cap_band_ratio / band_ratio
        working_age = is_hillingdon_working_age(
            household("local_authority", period),
            household("country", period),
            household("council_tax_reduction_household_has_pensioner", period),
        )
        band_2 = (
            household.max(
                household.members.benunit(
                    "hillingdon_council_tax_reduction_band_2", period
                )
            )
            > 0
        )
        capped = working_age & ~band_2 & (band_ratio > cap_band_ratio)
        return where(capped, capped_liability, council_tax)
