from policyengine_uk.model_api import *


class west_berkshire_council_tax_reduction_uc_lcw_element(Variable):
    value_type = bool
    entity = BenUnit
    label = "West Berkshire CTR source input - claimant or partner gets the UC Limited Capability for Work element"
    documentation = "Paragraph 29D places a claimant or partner in receipt of the Universal Credit Limited Capability for Work (LCW) component in the protected vulnerable category. PolicyEngine UK models the LCWRA element via uc_LCWRA_element but does not separately model the LCW element (abolished for most new claims from April 2017). This jurisdiction-scoped source input lets a household assert LCW-element receipt for the vulnerable-category test. Default False."
    definition_period = YEAR
    reference = "https://www.westberks.gov.uk/media/66425/Council-Tax-Reduction-Scheme-2026-27/pdf/The_Council_Tax_Reduction_Scheme_as_amended_by_West_Berkshire_Council_2026.pdf"
    default_value = False
