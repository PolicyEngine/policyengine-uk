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

    def formula(person, period, parameters):
        PT_HOURS_THRESHOLD = 16
        weekly_hours = person("weekly_hours", period)
        works_ft_hours = weekly_hours >= PT_HOURS_THRESHOLD
        works_pt_hours = ~works_ft_hours
        has_employment_income = person("employment_income", period) > 0
        has_self_employment_income = (
            person("self_employment_income", period) > 0
        )
        is_retired = person("is_SP_age", period)
        is_child = person("is_child", period)
        return select(
            [
                works_ft_hours & has_employment_income,
                works_pt_hours & has_employment_income,
                works_ft_hours & has_self_employment_income,
                works_pt_hours & has_self_employment_income,
                is_retired,
                is_child,
                True,
            ],
            [
                EmploymentStatus.FT_EMPLOYED,
                EmploymentStatus.PT_EMPLOYED,
                EmploymentStatus.FT_SELF_EMPLOYED,
                EmploymentStatus.PT_SELF_EMPLOYED,
                EmploymentStatus.RETIRED,
                EmploymentStatus.CHILD,
                EmploymentStatus.UNEMPLOYED,
            ],
        )


class is_in_work(Variable):
    label = "In work"
    documentation = "Whether this person is in work"
    entity = Person
    definition_period = YEAR
    value_type = bool

    def formula(person, period):
        employment_status = person("employment_status", period)
        WORK_STATUSES = [
            EmploymentStatus.FT_EMPLOYED,
            EmploymentStatus.PT_EMPLOYED,
            EmploymentStatus.FT_SELF_EMPLOYED,
            EmploymentStatus.PT_SELF_EMPLOYED,
        ]
        return is_in(employment_status, *WORK_STATUSES)
