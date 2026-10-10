from policyengine_uk.model_api import *
from policyengine_uk.utils.dates import birth_instant, grid_months_to_yyyymmdd
from policyengine_uk.utils.state_pension_age import (
    age_attaining_pensionable_age,
)


class state_pension_age(Variable):
    value_type = float
    entity = Person
    label = "State Pension age for this person"
    documentation = (
        "The age at which this person attains State Pension age (pensionable "
        "age), set by their date of birth. Where the statute sets the day on "
        "which it is attained, this is the person's age on that day. The date "
        "of birth is date_of_birth where given, and otherwise comes from age and "
        "months_since_last_birthday."
    )
    definition_period = YEAR
    unit = "year"
    reference = (
        "https://www.legislation.gov.uk/ukpga/1995/26/schedule/4",
        "https://www.legislation.gov.uk/ukpga/2014/19/section/26",
    )

    def formula(person, period, parameters):
        p = parameters(period).gov.dwp.state_pension.age
        # The instant of birth: date_of_birth where given, otherwise from age
        # and months_since_last_birthday. months_since_state_pension_age
        # measures from the same instant, so it is 6 October less the day of
        # attainment. The day of birth is the one starting at or after it, so
        # the person's legal age on 6 October is age.
        birth = birth_instant(person, period)
        birth_date = grid_months_to_yyyymmdd(birth)
        # Pensions Act 1995 Sch 4 para 1 rule (1): men born before 6 December
        # 1953 attain pensionable age at 65. Everyone else follows the
        # timetable in rules (2) to (10), which sets either an age or a day.
        male_rule = person("is_male", period) & (birth_date < p.male.born_before)
        return age_attaining_pensionable_age(p, birth, birth_date, male_rule)
