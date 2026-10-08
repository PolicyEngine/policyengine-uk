from policyengine_uk.model_api import *


class housing_benefit_childcare_disability_payment_suspended_in_hospital(Variable):
    value_type = bool
    entity = Person
    definition_period = YEAR
    label = "housing benefit childcare disability payment suspended in hospital"
    documentation = "A prescribed disability benefit was payable but is suspended solely because the child is a hospital inpatient. Supply the factual value when known; otherwise zero/false or an unobserved future date is used."
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/28",
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/31",
        "https://www.legislation.gov.uk/nisr/2006/405/regulation/25",
    )
