from policyengine_uk.model_api import *


class cotswold_council_tax_reduction_source_disregarded_income(Variable):
    value_type = float
    entity = BenUnit
    label = "Cotswold Council Tax Support source-disregarded annual income"
    documentation = "Source-listed income disregards not otherwise separately exposed in PolicyEngine UK, such as war pensions or specified compensation payments."
    definition_period = YEAR
    unit = GBP
    reference = "https://cotswold.gov.uk/media/k04l1hc2/cdc-cts-scheme-2026-27.pdf"
    default_value = 0
