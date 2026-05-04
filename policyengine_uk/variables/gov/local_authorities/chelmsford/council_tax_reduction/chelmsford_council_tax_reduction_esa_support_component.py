from policyengine_uk.model_api import *


class chelmsford_council_tax_reduction_esa_support_component(Variable):
    value_type = float
    entity = BenUnit
    label = (
        "Chelmsford LCTS annual ESA support or work-related activity component amount"
    )
    definition_period = YEAR
    unit = GBP
    reference = "https://www.chelmsford.gov.uk/media/kmml3jha/chelmsford-s13a-scheme-202526.pdf?alId=1227933"
    default_value = 0
