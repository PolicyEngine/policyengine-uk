from policyengine_uk.model_api import *


class cotswold_council_tax_reduction_non_dep_source_exemption(Variable):
    value_type = bool
    entity = Person
    label = "Cotswold Council Tax Support source non-dependant exemption"
    documentation = "Source input for non-dependant exemptions not otherwise separately exposed in PolicyEngine UK, such as patients in hospital for more than 52 weeks or trainees."
    definition_period = YEAR
    reference = "https://cotswold.gov.uk/media/k04l1hc2/cdc-cts-scheme-2026-27.pdf"
    default_value = False
