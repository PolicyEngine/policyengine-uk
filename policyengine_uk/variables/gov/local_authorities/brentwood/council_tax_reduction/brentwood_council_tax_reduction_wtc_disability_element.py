from policyengine_uk.model_api import *


class brentwood_council_tax_reduction_wtc_disability_element(Variable):
    value_type = bool
    entity = BenUnit
    label = "Brentwood CTR source input - applicant, partner, or dependant gets the WTC disability element"
    documentation = "Brentwood Schedule 1 paragraph 3 uplifts the band discount to 100 percent where the applicant, partner, or any dependant gets Working Tax Credit with the disability element. PolicyEngine UK models Working Tax Credit but not the disability element specifically, so this Brentwood-scoped source input lets a household assert receipt for the protected-group test. Default False."
    definition_period = YEAR
    reference = "https://www.brentwood.gov.uk/sites/default/files/2026-03/Council%20Tax%20reduction%20scheme%20S13A%202026-27%20FINAL.pdf"
    default_value = False
