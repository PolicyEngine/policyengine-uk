from policyengine_uk.model_api import *


class cotswold_council_tax_reduction_source_protected_group(Variable):
    value_type = bool
    entity = BenUnit
    label = "Cotswold Council Tax Support source protected group flag"
    documentation = "Source input for protected-group conditions not otherwise separately exposed in PolicyEngine UK, such as disabled child premiums or Schedule 2(15) pensions."
    definition_period = YEAR
    reference = "https://cotswold.gov.uk/media/k04l1hc2/cdc-cts-scheme-2026-27.pdf"
    default_value = False
