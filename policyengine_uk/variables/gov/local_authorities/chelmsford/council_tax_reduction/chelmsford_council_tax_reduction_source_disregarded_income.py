from policyengine_uk.model_api import *


class chelmsford_council_tax_reduction_source_disregarded_income(Variable):
    value_type = float
    entity = BenUnit
    label = "Chelmsford LCTS source-disregarded annual income"
    documentation = "Use this input for source-listed Schedule 3 or Schedule 4 income disregards not otherwise represented in PolicyEngine UK."
    definition_period = YEAR
    unit = GBP
    reference = "https://www.chelmsford.gov.uk/media/kmml3jha/chelmsford-s13a-scheme-202526.pdf?alId=1227933"
    default_value = 0
