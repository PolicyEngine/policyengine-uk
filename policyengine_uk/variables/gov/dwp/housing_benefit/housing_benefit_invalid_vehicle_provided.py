from policyengine_uk.model_api import *


class housing_benefit_invalid_vehicle_provided(Variable):
    value_type = bool
    entity = Person
    definition_period = YEAR
    label = "housing benefit invalid vehicle provided"
    documentation = "The prescribed NHS/Scottish/NI authority has provided the person an invalid carriage or vehicle under regulation 28(11)(g). Supply the factual value when known; otherwise zero/false or an unobserved future date is used."
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/28",
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/31",
        "https://www.legislation.gov.uk/nisr/2006/405/regulation/25",
    )
