from policyengine_uk.model_api import *


class housing_benefit_paid_work_expected(Variable):
    value_type = bool
    entity = Person
    definition_period = YEAR
    label = "housing benefit paid work expected"
    documentation = "The person's current work is for remuneration expected to be paid even if no earnings have yet been received. Supply the factual value when known; otherwise zero/false or an unobserved future date is used."
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/28",
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/31",
        "https://www.legislation.gov.uk/nisr/2006/405/regulation/25",
    )
