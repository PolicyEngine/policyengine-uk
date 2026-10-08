from policyengine_uk.model_api import *


class housing_benefit_income_support_for_incapacity(Variable):
    value_type = bool
    entity = Person
    definition_period = YEAR
    label = "housing benefit income support for incapacity"
    documentation = "The person's Income Support award is on the prescribed incapacity ground. Supply the factual value when known; otherwise zero/false or an unobserved future date is used."
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/28",
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/31",
        "https://www.legislation.gov.uk/nisr/2006/405/regulation/25",
    )
