from policyengine_uk.model_api import *


class cotswold_council_tax_reduction_source_additional_earnings_disregard(Variable):
    value_type = bool
    entity = BenUnit
    label = "Cotswold Council Tax Support source additional earnings disregard flag"
    documentation = "Source input for the Schedule 1 additional earnings disregard conditions that are not otherwise separately exposed in PolicyEngine UK."
    definition_period = YEAR
    reference = "https://cotswold.gov.uk/media/k04l1hc2/cdc-cts-scheme-2026-27.pdf"
    default_value = False
