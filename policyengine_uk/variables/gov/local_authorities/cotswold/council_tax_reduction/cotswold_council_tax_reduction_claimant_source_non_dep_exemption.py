from policyengine_uk.model_api import *


class cotswold_council_tax_reduction_claimant_source_non_dep_exemption(Variable):
    value_type = bool
    entity = Person
    label = "Cotswold Council Tax Support claimant source non-dependant exemption"
    documentation = "Source input for claimant or partner non-dependant deduction exemptions not otherwise separately exposed in PolicyEngine UK."
    definition_period = YEAR
    reference = "https://cotswold.gov.uk/media/k04l1hc2/cdc-cts-scheme-2026-27.pdf"
    default_value = False
