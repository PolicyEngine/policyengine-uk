from policyengine_uk.model_api import *


class esa_claim_made(Variable):
    value_type = bool
    entity = Person
    definition_period = YEAR
    label = "esa claim made"
    documentation = "The person has made a claim for Employment and Support Allowance. Not inferred from benefit amounts; supply when known."
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/3/paragraph/1A",
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/3/paragraph/21",
        "https://www.legislation.gov.uk/nisr/2006/405/schedule/4",
    )
