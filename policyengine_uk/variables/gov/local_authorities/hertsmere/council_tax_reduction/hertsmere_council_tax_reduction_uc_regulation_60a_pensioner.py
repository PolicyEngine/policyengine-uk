from policyengine_uk.model_api import *


class hertsmere_council_tax_reduction_uc_regulation_60a_pensioner(Variable):
    value_type = bool
    entity = BenUnit
    label = "Whether Hertsmere's Universal Credit regulation 60A pensioner exception applies"
    definition_period = YEAR
    reference = "https://www.hertsmere.gov.uk/asset-library/cts-scheme-2026-27.pdf"
    default_value = False
