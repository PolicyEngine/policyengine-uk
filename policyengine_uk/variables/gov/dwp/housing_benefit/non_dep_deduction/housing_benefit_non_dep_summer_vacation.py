from policyengine_uk.model_api import *


class housing_benefit_non_dep_summer_vacation(Variable):
    value_type = bool
    entity = Person
    definition_period = YEAR
    label = "housing benefit non dep summer vacation"
    documentation = (
        "Currently in a recognised summer vacation appropriate to the full-time course."
    )
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/74",
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/55",
        "https://www.legislation.gov.uk/nisr/2006/405/regulation/72",
        "https://www.legislation.gov.uk/nisr/2006/406/regulation/53",
    )
