from policyengine_uk.model_api import *


class chelmsford_council_tax_reduction_source_special_earnings_disregard(Variable):
    value_type = bool
    entity = BenUnit
    label = (
        "Chelmsford LCTS source-defined special occupation earnings disregard trigger"
    )
    documentation = "Covers source-listed part-time firefighter, coastguard, lifeboat, and reserve forces earnings disregard triggers not otherwise represented in PolicyEngine UK."
    definition_period = YEAR
    reference = "https://www.chelmsford.gov.uk/media/kmml3jha/chelmsford-s13a-scheme-202526.pdf?alId=1227933"
    default_value = False
