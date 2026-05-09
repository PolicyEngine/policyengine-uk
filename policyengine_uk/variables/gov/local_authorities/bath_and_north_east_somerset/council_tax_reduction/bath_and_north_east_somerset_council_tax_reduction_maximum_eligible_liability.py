from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.config import (
    english_council_tax_band_ratio,
)


class bath_and_north_east_somerset_council_tax_reduction_maximum_eligible_liability(
    Variable
):
    value_type = float
    entity = Household
    label = "Bath and North East Somerset maximum Council Tax liability eligible for Council Tax Reduction"
    definition_period = YEAR
    unit = GBP
    reference = "https://www.bathnes.gov.uk/sites/default/files/2026-01/Council_Tax_reduction_scheme_April_1_2026_to_March_31_2027.pdf"

    def formula(household, period, parameters):
        local_authorities = parameters(period).gov.local_authorities
        council_tax = household("council_tax", period)
        band_ratio = english_council_tax_band_ratio(
            household("council_tax_band", period),
            local_authorities.england.council_tax.band_ratio,
        )
        ctr = local_authorities.bath_and_north_east_somerset.council_tax_reduction
        cap_band_ratio = ctr.maximum_liability.cap_band_ratio
        capped_liability = council_tax * cap_band_ratio / band_ratio
        person = household.members
        claimant_benunit = person.benunit("benunit_contains_household_head", period)
        protected = household.any(
            claimant_benunit
            & person.benunit(
                "bath_and_north_east_somerset_council_tax_reduction_protected_group",
                period,
            )
        )
        capped = ~protected & (band_ratio > cap_band_ratio)
        return where(capped, capped_liability, council_tax)
