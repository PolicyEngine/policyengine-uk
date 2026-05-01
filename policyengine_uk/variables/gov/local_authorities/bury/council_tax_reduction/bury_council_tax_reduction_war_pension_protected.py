from policyengine_uk.model_api import *


class bury_council_tax_reduction_war_pension_protected(Variable):
    value_type = bool
    entity = BenUnit
    label = "Bury CTR claimant or partner receives a war pension protected by the local scheme"
    definition_period = YEAR
    reference = (
        "https://www.bury.gov.uk/asset-library/bury-cts-scheme-policy-2026-27.pdf"
    )
