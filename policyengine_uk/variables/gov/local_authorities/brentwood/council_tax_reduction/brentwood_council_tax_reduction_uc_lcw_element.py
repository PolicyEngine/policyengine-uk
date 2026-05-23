from policyengine_uk.model_api import *


class brentwood_council_tax_reduction_uc_lcw_element(Variable):
    value_type = bool
    entity = BenUnit
    label = "Brentwood CTR source input - applicant, partner, or dependant gets the UC Limited Capability for Work element"
    documentation = "Brentwood Schedule 1 paragraph 3 uplifts the band discount to 100 percent where the applicant, partner, or any dependant gets Universal Credit with the Limited Capability for Work (LCW) element. The LCW element was abolished for most new claims from April 2017, but is still listed in the Brentwood scheme. PolicyEngine UK models the Limited Capability for Work-Related Activity (LCWRA) element directly via uc_LCWRA_element, but does not model the LCW element. This Brentwood-scoped source input lets a household assert LCW-element receipt for the protected-group test. Default False."
    definition_period = YEAR
    reference = "https://www.brentwood.gov.uk/sites/default/files/2026-03/Council%20Tax%20reduction%20scheme%20S13A%202026-27%20FINAL.pdf"
    default_value = False
