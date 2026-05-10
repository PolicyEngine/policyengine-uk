from policyengine_uk.model_api import *


class hertsmere_council_tax_reduction_uc_relevant_period_pensioner(Variable):
    value_type = bool
    entity = BenUnit
    label = "Whether Hertsmere's Universal Credit relevant-period pensioner exception applies"
    definition_period = YEAR
    reference = "https://www.hertsmere.gov.uk/asset-library/cts-scheme-2026-27.pdf"
    default_value = False
