from policyengine_uk.model_api import *


class housing_benefit_non_dep_normal_home_elsewhere(Variable):
    value_type = bool
    entity = Person
    definition_period = YEAR
    label = "housing benefit non dep normal home elsewhere"
    documentation = "The authority considers this person's normal home elsewhere, despite residence with the claimant."
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/74",
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/55",
        "https://www.legislation.gov.uk/nisr/2006/405/regulation/72",
        "https://www.legislation.gov.uk/nisr/2006/406/regulation/53",
    )
