from policyengine_uk.model_api import *


class chelmsford_council_tax_reduction_claimant_source_non_dep_exemption(Variable):
    value_type = bool
    entity = Person
    label = "Whether a Chelmsford LCTS claimant has a section 58.6 non-dependant deduction exemption not otherwise modeled"
    documentation = "Covers source-listed claimant exemptions not otherwise represented in PolicyEngine UK, such as suspended entitlement to disability benefits."
    definition_period = YEAR
    reference = "https://www.chelmsford.gov.uk/media/kmml3jha/chelmsford-s13a-scheme-202526.pdf?alId=1227933"
    default_value = False
