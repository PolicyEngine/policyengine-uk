from policyengine_uk.model_api import *
from policyengine_uk.variables.input.council_tax_band import CouncilTaxBand
from policyengine_uk.variables.household.demographic.tenure_type import TenureType


class brentwood_council_tax_reduction_band_fgh_owner_excluded(Variable):
    value_type = bool
    entity = BenUnit
    label = (
        "Whether Brentwood's section 6.1 Band F/G/H owner-occupier exclusion applies"
    )
    documentation = "Brentwood paragraph 6.1: working-age applicants who reside in a property in Council Tax Band F, G or H and are defined within the Housing Benefit regulations as an owner receive 0 percent support."
    definition_period = YEAR
    reference = "https://www.brentwood.gov.uk/sites/default/files/2026-03/Council%20Tax%20reduction%20scheme%20S13A%202026-27%20FINAL.pdf"

    def formula(benunit, period, parameters):
        household = benunit.household
        band = household("council_tax_band", period)
        tenure = household("tenure_type", period)
        is_band_fgh = (
            (band == CouncilTaxBand.F)
            | (band == CouncilTaxBand.G)
            | (band == CouncilTaxBand.H)
        )
        is_owner = (tenure == TenureType.OWNED_OUTRIGHT) | (
            tenure == TenureType.OWNED_WITH_MORTGAGE
        )
        return is_band_fgh & is_owner
