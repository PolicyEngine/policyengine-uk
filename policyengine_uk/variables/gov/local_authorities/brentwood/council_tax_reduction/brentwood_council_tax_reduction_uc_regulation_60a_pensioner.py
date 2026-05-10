from policyengine_uk.model_api import *


class brentwood_council_tax_reduction_uc_regulation_60a_pensioner(Variable):
    value_type = bool
    entity = BenUnit
    label = "Whether Brentwood disregards a pension-age UC award under regulation 60A"
    documentation = "Brentwood paragraph 5.2 disregards a pension-age UC award where regulation 60A of the Universal Credit (Transitional Provisions) Regulations 2014 applies. When set, a pension-age UC claimant remains in the national pensioner CTR scheme rather than the Brentwood working-age scheme."
    definition_period = YEAR
    reference = "https://www.brentwood.gov.uk/sites/default/files/2026-03/Council%20Tax%20reduction%20scheme%20S13A%202026-27%20FINAL.pdf"
    default_value = False
