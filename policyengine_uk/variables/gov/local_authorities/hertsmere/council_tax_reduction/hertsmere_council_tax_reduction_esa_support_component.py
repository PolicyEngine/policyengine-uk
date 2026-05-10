from policyengine_uk.model_api import *


class hertsmere_council_tax_reduction_esa_support_component(Variable):
    value_type = float
    entity = BenUnit
    label = "ESA support component counted for Hertsmere Council Tax Reduction protected status"
    definition_period = YEAR
    unit = GBP
    reference = "https://www.hertsmere.gov.uk/asset-library/cts-scheme-2026-27.pdf"
    default_value = 0
