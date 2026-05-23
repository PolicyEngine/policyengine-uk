from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.config import (
    english_council_tax_band_ratio,
)


class cheshire_west_and_chester_council_tax_reduction_maximum_eligible_liability(
    Variable
):
    value_type = float
    entity = Household
    label = "Cheshire West and Chester maximum Council Tax liability eligible for Council Tax Reduction"
    definition_period = YEAR
    unit = GBP
    reference = "https://www.cheshirewestandchester.gov.uk/asset-library/council-tax-reduction-summary-2026-2027-annex-a-part-2.pdf"

    def formula(household, period, parameters):
        local_authorities = parameters(period).gov.local_authorities
        council_tax = household("council_tax", period)
        household_person = household.members
        claimant_benunit = household_person.benunit(
            "benunit_contains_household_head", period
        )
        war_pensioner = household.any(
            claimant_benunit
            & household_person.benunit(
                "cheshire_west_and_chester_council_tax_reduction_war_pensioner",
                period,
            )
        )
        band_ratio = english_council_tax_band_ratio(
            household("council_tax_band", period),
            local_authorities.england.council_tax.band_ratio,
        )
        cap_band_ratio = local_authorities.cheshire_west_and_chester.council_tax_reduction.maximum_liability.cap_band_ratio
        capped_liability = council_tax * cap_band_ratio / band_ratio
        liability = where(band_ratio > cap_band_ratio, capped_liability, council_tax)
        return where(war_pensioner, council_tax, liability)
