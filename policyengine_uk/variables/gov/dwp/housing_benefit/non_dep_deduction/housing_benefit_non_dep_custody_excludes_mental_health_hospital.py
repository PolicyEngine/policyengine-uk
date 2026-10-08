from policyengine_uk.model_api import *


class housing_benefit_non_dep_custody_excludes_mental_health_hospital(Variable):
    value_type = bool
    entity = Person
    definition_period = YEAR
    label = "housing benefit non dep custody excludes mental health hospital"
    documentation = "Current custody is pending trial, pending sentence after conviction, or under a court sentence, and is not statutory mental-health hospital detention. Used with is_in_prison and current absence."
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/74",
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/55",
        "https://www.legislation.gov.uk/nisr/2006/405/regulation/72",
        "https://www.legislation.gov.uk/nisr/2006/406/regulation/53",
    )
