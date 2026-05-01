from policyengine_uk.model_api import *


class herefordshire_council_tax_reduction_claimant_source_non_dep_exemption(Variable):
    value_type = bool
    entity = Person
    label = "Whether a Herefordshire CTR claimant has a section 58.6 non-dependant deduction exemption not otherwise modeled"
    documentation = "Covers source-listed claimant exemptions not otherwise represented in PolicyEngine UK, such as suspended entitlement to disability benefits."
    definition_period = YEAR
    reference = "https://councillors.herefordshire.gov.uk/documents/s50131582/Approved%20202526%20Council%20Tax%20Reduction%20Scheme.pdf"
    default_value = False
