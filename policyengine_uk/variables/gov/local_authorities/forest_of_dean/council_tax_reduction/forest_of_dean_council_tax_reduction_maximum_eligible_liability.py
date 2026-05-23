from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.config import (
    english_council_tax_band_ratio,
)


class forest_of_dean_council_tax_reduction_maximum_eligible_liability(Variable):
    value_type = float
    entity = BenUnit
    label = (
        "Forest of Dean maximum Council Tax liability eligible for Council Tax Support"
    )
    documentation = "Paragraphs 57.1(a) and 57.6(a) cap working-age eligible liability at the Band E equivalent for the dwelling, regardless of Class A or Class B."
    definition_period = YEAR
    unit = GBP
    reference = "https://www.fdean.gov.uk/media/r4ff2lok/council-tax-support-scheme-for-working-age-customers-2026-to-2027.pdf"

    def formula(benunit, period, parameters):
        ctr = parameters(
            period
        ).gov.local_authorities.forest_of_dean.council_tax_reduction
        england_council_tax = parameters(
            period
        ).gov.local_authorities.england.council_tax
        household = benunit.household
        council_tax = household("council_tax", period)
        band_ratio = english_council_tax_band_ratio(
            household("council_tax_band", period),
            england_council_tax.band_ratio,
        )
        cap_band_ratio = ctr.maximum_liability.cap_band_ratio
        capped_liability = council_tax * cap_band_ratio / band_ratio
        capped = band_ratio > cap_band_ratio
        return where(capped, capped_liability, council_tax)
