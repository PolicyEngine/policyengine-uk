from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.config import (
    english_council_tax_band_ratio,
)


class st_helens_council_tax_reduction_maximum_eligible_liability(Variable):
    value_type = float
    entity = BenUnit
    label = "St Helens maximum Council Tax liability eligible for Council Tax Reduction"
    documentation = "Paragraph 9 caps the assessed liability of working-age applicants in Band F, G or H at the equivalent Band D amount for the dwelling."
    definition_period = YEAR
    unit = GBP
    reference = "https://www.sthelens.gov.uk/media/13997/St-Helens-CTR-scheme-2026/pdf/St_Helens_CTR_scheme_2026.pdf"

    def formula(benunit, period, parameters):
        ctr = parameters(period).gov.local_authorities.st_helens.council_tax_reduction
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
