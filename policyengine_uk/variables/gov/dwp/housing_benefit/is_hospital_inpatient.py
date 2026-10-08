from policyengine_uk.model_api import *


class is_hospital_inpatient(Variable):
    value_type = bool
    entity = Person
    definition_period = YEAR
    label = "is hospital inpatient"
    documentation = "The person currently receives inpatient hospital treatment. Supply the factual value when known; otherwise zero/false or an unobserved future date is used."
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/28",
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/31",
        "https://www.legislation.gov.uk/nisr/2006/405/regulation/25",
    )
