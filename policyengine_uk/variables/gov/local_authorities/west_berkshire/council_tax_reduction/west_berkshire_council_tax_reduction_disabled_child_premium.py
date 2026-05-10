from policyengine_uk.model_api import *


class west_berkshire_council_tax_reduction_disabled_child_premium(Variable):
    value_type = bool
    entity = BenUnit
    label = "West Berkshire CTR source input - claimant or partner is entitled to a Disabled Child Premium"
    documentation = "Paragraph 29D places a claimant or partner entitled to a Disabled Child Premium (Schedule 3 paragraph 13 of the West Berkshire scheme, mirroring the prescribed Default Scheme) in the protected vulnerable category. PolicyEngine UK does not currently expose a benunit-level Disabled Child Premium variable, so this jurisdiction-scoped source input lets a household assert entitlement for the vulnerable-category test. Default False."
    definition_period = YEAR
    reference = "https://www.westberks.gov.uk/media/66425/Council-Tax-Reduction-Scheme-2026-27/pdf/The_Council_Tax_Reduction_Scheme_as_amended_by_West_Berkshire_Council_2026.pdf"
    default_value = False
