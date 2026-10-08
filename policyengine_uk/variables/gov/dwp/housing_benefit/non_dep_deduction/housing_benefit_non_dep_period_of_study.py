from policyengine_uk.model_api import *


class housing_benefit_non_dep_period_of_study(Variable):
    value_type = bool
    entity = Person
    definition_period = YEAR
    label = "Non-dependant is in a Housing Benefit statutory period of study"
    documentation = "Period of study as defined by the relevant HB student regulations. In the absence of more precise course dates, an enrolled full-time student outside a reported summer vacation is treated as studying. Override for other periods outside the statutory course dates."
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/74",
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/55",
        "https://www.legislation.gov.uk/nisr/2006/405/regulation/72",
        "https://www.legislation.gov.uk/nisr/2006/406/regulation/53",
    )

    def formula(person, period, parameters):
        return person("housing_benefit_non_dep_full_time_student", period) & ~person(
            "housing_benefit_non_dep_summer_vacation", period
        )
