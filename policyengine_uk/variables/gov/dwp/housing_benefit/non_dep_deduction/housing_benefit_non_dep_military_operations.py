from policyengine_uk.model_api import *


class housing_benefit_non_dep_military_operations(Variable):
    value_type = bool
    entity = Person
    definition_period = YEAR
    label = "housing benefit non dep military operations"
    documentation = "Currently away on military operations; ordinary military service or training does not qualify."
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/74",
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/55",
        "https://www.legislation.gov.uk/nisr/2006/405/regulation/72",
        "https://www.legislation.gov.uk/nisr/2006/406/regulation/53",
    )
