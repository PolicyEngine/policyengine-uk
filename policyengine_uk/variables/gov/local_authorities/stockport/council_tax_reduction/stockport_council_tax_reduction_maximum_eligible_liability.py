from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.config import (
    english_council_tax_band_ratio,
    is_stockport_working_age,
)


class stockport_council_tax_reduction_maximum_eligible_liability(Variable):
    value_type = float
    entity = Household
    label = "Stockport maximum Council Tax liability eligible for CTR"
    definition_period = YEAR
    unit = GBP

    def formula(household, period, parameters):
        england_council_tax = parameters(
            period
        ).gov.local_authorities.england.council_tax
        ctr = parameters(period).gov.local_authorities.stockport.council_tax_reduction
        council_tax = household("council_tax", period)
        band_ratio = english_council_tax_band_ratio(
            household("council_tax_band", period),
            england_council_tax.band_ratio,
        )
        lha_allowed_bedrooms = household.max(
            household.members.benunit("LHA_allowed_bedrooms", period)
        )
        cap_band_ratio = where(
            lha_allowed_bedrooms >= 3,
            ctr.maximum_liability.three_bedroom_cap_band_ratio,
            ctr.maximum_liability.standard_cap_band_ratio,
        )
        capped_liability = council_tax * cap_band_ratio / band_ratio
        working_age = is_stockport_working_age(
            household("local_authority", period),
            household("country", period),
            household("council_tax_reduction_household_has_pensioner", period),
        )
        disabled_persons_relief = household(
            "stockport_council_tax_reduction_disabled_persons_relief", period
        )
        capped = working_age & ~disabled_persons_relief & (band_ratio > cap_band_ratio)
        return where(capped, capped_liability, council_tax)
