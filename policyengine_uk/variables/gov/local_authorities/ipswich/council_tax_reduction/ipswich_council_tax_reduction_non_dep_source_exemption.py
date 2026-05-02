from policyengine_uk.model_api import *


class ipswich_council_tax_reduction_non_dep_source_exemption(Variable):
    value_type = bool
    entity = Person
    label = "Ipswich CTR source-defined non-dependant exemption"
    documentation = "Covers source-listed non-dependant exemptions not otherwise represented in PolicyEngine UK."
    definition_period = YEAR
    default_value = False
    reference = "https://www.ipswich.gov.uk/sites/ipswich/files/2026-03/Council%20Tax%20Reduction%20scheme%202026_0.pdf"
