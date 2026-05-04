from policyengine_uk.model_api import *


class chelmsford_council_tax_reduction_uc_relevant_period_pensioner(Variable):
    value_type = bool
    entity = BenUnit
    label = "Whether Chelmsford disregards UC during the pension-age relevant period"
    definition_period = YEAR
    reference = "https://www.chelmsford.gov.uk/media/kmml3jha/chelmsford-s13a-scheme-202526.pdf?alId=1227933"
    default_value = False
