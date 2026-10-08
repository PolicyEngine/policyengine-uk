from policyengine_uk.model_api import *


class housing_benefit_childcare_disability_benefit_in_payment(Variable):
    value_type = bool
    entity = Person
    definition_period = YEAR
    label = "housing benefit childcare disability benefit in payment"
    documentation = "A prescribed disability benefit, including the Scottish equivalents listed in regulation 28(13), is payable for the child. Supply the factual value when known; otherwise zero/false or an unobserved future date is used."
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/28",
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/31",
        "https://www.legislation.gov.uk/nisr/2006/405/regulation/25",
    )
