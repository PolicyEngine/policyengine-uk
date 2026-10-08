from policyengine_uk.model_api import *


class esa_converted_award(Variable):
    value_type = bool
    entity = Person
    definition_period = YEAR
    label = "esa converted award"
    documentation = "The person is entitled to converted ESA, including entitlement prevented solely by the contributory ESA duration limit. Not inferred from benefit amounts; supply when known."
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/3/paragraph/1A",
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/3/paragraph/21",
        "https://www.legislation.gov.uk/nisr/2006/405/schedule/4",
    )
