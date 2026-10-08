from policyengine_uk.model_api import *
from policyengine_uk.variables.household.demographic.highest_education import (
    EducationType,
)


class housing_benefit_non_dep_full_time_student(Variable):
    value_type = bool
    entity = Person
    definition_period = YEAR
    label = "Full-time student for Housing Benefit non-dependant rules"
    documentation = "Full-time course status. The fallback uses the model's education enrolment and higher-education inputs, as the existing local-benefit rules do; explicitly override it for part-time courses. This fact alone does not exempt a working student during summer vacation."
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/74",
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/55",
        "https://www.legislation.gov.uk/nisr/2006/405/regulation/72",
        "https://www.legislation.gov.uk/nisr/2006/406/regulation/53",
    )

    def formula(person, period, parameters):
        return (
            person("current_education", period) != EducationType.NOT_IN_EDUCATION
        ) | person("in_HE", period)
