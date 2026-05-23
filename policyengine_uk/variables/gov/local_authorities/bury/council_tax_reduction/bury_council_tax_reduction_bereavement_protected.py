from policyengine_uk.model_api import *


class bury_council_tax_reduction_bereavement_protected(Variable):
    value_type = bool
    entity = BenUnit
    label = "Bury CTR household has a recent bereavement protected-group marker"
    definition_period = YEAR
    reference = (
        "https://www.bury.gov.uk/asset-library/bury-cts-scheme-policy-2026-27.pdf"
    )
