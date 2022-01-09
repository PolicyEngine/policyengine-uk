from openfisca_uk.model_api import *


class EmploymentStatus(Enum):
    FT_EMPLOYED = "Full-time employed"
    PT_EMPLOYED = "Part-time employed"
    FT_SELF_EMPLOYED = "Full-time self-employed"
    PT_SELF_EMPLOYED = "Part-time self-employed"
    UNEMPLOYED = "Unemployed"
    RETIRED = "Retired"
    STUDENT = "Student"
    CARER = "Carer"
    LONG_TERM_DISABLED = "Long-term sick/disabled"
    SHORT_TERM_DISABLED = "Short-term sick/disabled"
    OTHER_INACTIVE = "Inactive for another reason"
    CHILD = "Child"


class employment_status(Variable):
    value_type = Enum
    entity = Person
    possible_values = EmploymentStatus
    default_value = EmploymentStatus.UNEMPLOYED
    label = "Employment status"
    documentation = "The employment status of this person"
    definition_period = YEAR

class is_in_work(Variable):
    label = "In work"
    documentation = "Whether this person is in work"
    entity = Person
    definition_period = YEAR
    value_type = bool

    def formula(person, period):
        employment_status = person("employment_status", period)
        return is_in(employment_status, *[
            EmploymentStatus.FT_EMPLOYED,
            EmploymentStatus.PT_EMPLOYED,
            EmploymentStatus.FT_SELF_EMPLOYED,
            EmploymentStatus.PT_SELF_EMPLOYED,
        ])
