from policyengine_uk.model_api import *


class buckinghamshire_council_tax_reduction_non_dep_source_exemption(Variable):
    value_type = bool
    entity = Person
    label = "Whether a Buckinghamshire CTR non-dependant has a source-defined deduction exemption not otherwise modeled"
    documentation = "Covers source-listed non-dependant exemptions not otherwise represented in PolicyEngine UK, such as normal home elsewhere, youth-training allowance, long-term patient status, armed forces away on operations, or Schedule 1 discount-disregarded cases."
    definition_period = YEAR
    reference = "https://buckinghamshire.moderngov.co.uk/documents/s115727/Appendix%204%20Council%20Tax%20Reduction%20Scheme%20Policy.pdf"
    default_value = False
