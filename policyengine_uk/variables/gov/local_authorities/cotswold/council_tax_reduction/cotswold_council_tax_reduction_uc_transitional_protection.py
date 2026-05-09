from policyengine_uk.model_api import *


class cotswold_council_tax_reduction_uc_transitional_protection(Variable):
    value_type = float
    entity = BenUnit
    label = "Cotswold Council Tax Support Universal Credit transitional protection"
    documentation = "Source input for the Universal Credit transitional protection payment disregarded from Cotswold Council Tax Support income."
    definition_period = YEAR
    unit = GBP
    reference = "https://cotswold.gov.uk/media/k04l1hc2/cdc-cts-scheme-2026-27.pdf"
    default_value = 0
