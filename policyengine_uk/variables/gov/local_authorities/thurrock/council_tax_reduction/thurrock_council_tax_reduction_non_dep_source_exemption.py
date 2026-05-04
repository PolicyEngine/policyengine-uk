from policyengine_uk.model_api import *


class thurrock_council_tax_reduction_non_dep_source_exemption(Variable):
    value_type = bool
    entity = Person
    label = "Whether a Thurrock CTR non-dependant has a section 58.7 or 58.8 deduction exemption not otherwise modeled"
    documentation = "Covers source-listed non-dependant exemptions not otherwise represented in PolicyEngine UK, such as normal home elsewhere, long-term patient status, armed forces away, or Schedule 1 discount-disregarded cases."
    definition_period = YEAR
    reference = "https://thurrock.moderngov.co.uk/documents/s51034/Enc.%201%20for%20Local%20Council%20Tax%20Support%20Scheme%202026-27.pdf"
    default_value = False
