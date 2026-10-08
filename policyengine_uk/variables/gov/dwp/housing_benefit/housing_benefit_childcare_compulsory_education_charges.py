from policyengine_uk.model_api import *


class housing_benefit_childcare_compulsory_education_charges(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = "housing benefit childcare compulsory education charges"
    documentation = "Part of the per-child charges that pays for compulsory education, which is excluded. Supply the factual value when known; otherwise zero/false or an unobserved future date is used."
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/28",
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/31",
        "https://www.legislation.gov.uk/nisr/2006/405/regulation/25",
    )
