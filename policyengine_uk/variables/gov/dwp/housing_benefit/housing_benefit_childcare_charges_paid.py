from policyengine_uk.model_api import *


class housing_benefit_childcare_charges_paid(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = "housing benefit childcare charges paid"
    documentation = "Annual charges paid by the claimant/partner in respect of this child, not spending by the child. Provide per-child amounts rather than reallocating aggregate adult childcare consumption. Supply the factual value when known; otherwise zero/false or an unobserved future date is used."
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/28",
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/31",
        "https://www.legislation.gov.uk/nisr/2006/405/regulation/25",
    )
