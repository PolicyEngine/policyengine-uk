from policyengine_uk.model_api import *


class esa_assessment_phase_ended(Variable):
    value_type = bool
    entity = Person
    definition_period = YEAR
    label = "esa assessment phase ended"
    documentation = "The person's statutory ESA assessment phase has ended. Not inferred from benefit amounts; supply when known."
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/3/paragraph/1A",
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/3/paragraph/21",
        "https://www.legislation.gov.uk/nisr/2006/405/schedule/4",
    )
