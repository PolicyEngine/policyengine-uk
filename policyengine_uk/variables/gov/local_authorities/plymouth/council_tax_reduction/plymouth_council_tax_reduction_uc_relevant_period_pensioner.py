from policyengine_uk.model_api import *


class plymouth_council_tax_reduction_uc_relevant_period_pensioner(Variable):
    value_type = bool
    entity = BenUnit
    label = "Whether a Plymouth pension-age Universal Credit award remains in the prescribed pensioner CTR scheme during the source relevant period"
    documentation = "Covers the source transitional protection where a Universal Credit award is disregarded for pensioner-status classification."
    definition_period = YEAR
    reference = "https://www.plymouth.gov.uk/sites/default/files/2026-03/Plymouth-CTR-Scheme-2026-2027.pdf"
    default_value = False
