from policyengine_uk.model_api import *


class west_berkshire_council_tax_reduction_war_pension(Variable):
    value_type = bool
    entity = BenUnit
    label = "West Berkshire CTR source input - claimant or partner is in receipt of any War Pension"
    documentation = "Paragraph 29D places a claimant or partner in receipt of any amount of War Pension in the protected vulnerable category. PolicyEngine UK does not have a single 'war pension' variable covering the schemes referenced by West Berkshire (War Disablement Pension, War Widow(er)'s Pension, analogous payments), so this jurisdiction-scoped source input lets a household assert receipt for the vulnerable-category test. Default False."
    definition_period = YEAR
    reference = "https://www.westberks.gov.uk/media/66425/Council-Tax-Reduction-Scheme-2026-27/pdf/The_Council_Tax_Reduction_Scheme_as_amended_by_West_Berkshire_Council_2026.pdf"
    default_value = False
