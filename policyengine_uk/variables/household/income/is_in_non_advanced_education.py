from policyengine_uk.model_api import *
from policyengine_uk.variables.household.demographic.highest_education import (
    EducationType,
)


class is_in_non_advanced_education(Variable):
    value_type = bool
    entity = Person
    label = "In non-advanced education"
    documentation = (
        "Whether this person is in non-advanced education for child and "
        "qualifying young person benefit rules. The default proxy treats "
        "non-tertiary education as non-advanced and excludes apprenticeships."
    )
    definition_period = YEAR
    reference = "https://www.legislation.gov.uk/uksi/2013/376/regulation/5"

    def formula(person, period, parameters):
        education = person("current_education", period)
        in_education = education != EducationType.NOT_IN_EDUCATION
        not_higher_education = education != EducationType.TERTIARY
        return in_education & not_higher_education & ~person("is_apprentice", period)
