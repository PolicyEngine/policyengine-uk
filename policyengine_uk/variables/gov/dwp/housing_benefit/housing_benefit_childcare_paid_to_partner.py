from policyengine_uk.model_api import *


class housing_benefit_childcare_paid_to_partner(Variable):
    value_type = bool
    entity = Person
    definition_period = YEAR
    label = "housing benefit childcare paid to partner"
    documentation = "The claimant pays their partner, or the partner pays the claimant, for this child's care. Supply the factual value when known; otherwise zero/false or an unobserved future date is used."
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/28",
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/31",
        "https://www.legislation.gov.uk/nisr/2006/405/regulation/25",
    )
