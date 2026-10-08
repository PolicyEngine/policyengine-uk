from policyengine_uk.model_api import *


class housing_benefit_non_dep_absent(Variable):
    value_type = bool
    entity = Person
    definition_period = YEAR
    label = "housing benefit non dep absent"
    documentation = "Not currently residing with the claimant. Used with current hospital, custody or military-operation facts, not a past absence."
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/74",
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/55",
        "https://www.legislation.gov.uk/nisr/2006/405/regulation/72",
        "https://www.legislation.gov.uk/nisr/2006/406/regulation/53",
    )
