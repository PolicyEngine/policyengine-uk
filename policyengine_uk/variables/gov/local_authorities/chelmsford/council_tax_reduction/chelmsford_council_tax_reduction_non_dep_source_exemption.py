from policyengine_uk.model_api import *


class chelmsford_council_tax_reduction_non_dep_source_exemption(Variable):
    value_type = bool
    entity = Person
    label = "Whether a Chelmsford LCTS non-dependant has a section 58.7 deduction exemption not otherwise modeled"
    documentation = "Covers source-listed non-dependant exemptions not otherwise represented in PolicyEngine UK, such as normal home elsewhere, youth training, long-term patient status, or armed forces away."
    definition_period = YEAR
    reference = "https://www.chelmsford.gov.uk/media/kmml3jha/chelmsford-s13a-scheme-202526.pdf?alId=1227933"
    default_value = False
