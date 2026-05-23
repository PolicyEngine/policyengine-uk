from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.config import (
    english_council_tax_band_ratio,
)


class west_berkshire_council_tax_reduction_maximum_eligible_liability(Variable):
    value_type = float
    entity = BenUnit
    label = "West Berkshire maximum Council Tax liability eligible for Council Tax Reduction"
    documentation = "Paragraph 29A caps the assessed liability of non-vulnerable working-age Class D or E claimants at the Band C amount within the same parish. Vulnerable Class E1 claimants and pension-age applicants use the full council tax for the dwelling."
    definition_period = YEAR
    unit = GBP
    reference = "https://www.westberks.gov.uk/media/66425/Council-Tax-Reduction-Scheme-2026-27/pdf/The_Council_Tax_Reduction_Scheme_as_amended_by_West_Berkshire_Council_2026.pdf"

    def formula(benunit, period, parameters):
        ctr = parameters(
            period
        ).gov.local_authorities.west_berkshire.council_tax_reduction
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
        local_scheme = benunit(
            "west_berkshire_council_tax_reduction_is_local_scheme", period
        )
        vulnerable = benunit(
            "west_berkshire_council_tax_reduction_vulnerable_group", period
        )
        # Class D/E non-vulnerable working-age applicants have liability capped at Band C.
        capped = local_scheme & ~vulnerable & (band_ratio > cap_band_ratio)
        return where(capped, capped_liability, council_tax)
