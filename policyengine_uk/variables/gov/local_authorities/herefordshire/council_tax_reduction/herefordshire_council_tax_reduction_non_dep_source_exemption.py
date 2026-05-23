from policyengine_uk.model_api import *


class herefordshire_council_tax_reduction_non_dep_source_exemption(Variable):
    value_type = bool
    entity = Person
    label = "Whether a Herefordshire CTR non-dependant has a section 58.7 or 58.8 deduction exemption not otherwise modeled"
    documentation = "Covers source-listed non-dependant exemptions not otherwise represented in PolicyEngine UK, such as normal home elsewhere, long-term patient status, armed forces away, or Schedule 1 discount-disregarded cases."
    definition_period = YEAR
    reference = "https://councillors.herefordshire.gov.uk/documents/s50131582/Approved%20202526%20Council%20Tax%20Reduction%20Scheme.pdf"
    default_value = False
