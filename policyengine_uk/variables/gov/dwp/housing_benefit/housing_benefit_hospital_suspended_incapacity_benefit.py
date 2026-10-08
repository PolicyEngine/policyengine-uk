from policyengine_uk.model_api import *


class housing_benefit_hospital_suspended_incapacity_benefit(Variable):
    value_type = bool
    entity = Person
    definition_period = YEAR
    label = "housing benefit hospital suspended incapacity benefit"
    documentation = "A prescribed incapacity/disability award ceased to be payable solely because of hospital admission under regulation 28(11)(e)-(ec). Supply the factual value when known; otherwise zero/false or an unobserved future date is used."
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/28",
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/31",
        "https://www.legislation.gov.uk/nisr/2006/405/regulation/25",
    )
