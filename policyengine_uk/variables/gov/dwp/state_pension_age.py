from policyengine_uk.model_api import *
from policyengine_uk.utils.state_pension_age import (
    age_attaining_pensionable_age,
    date_of_birth,
)


class state_pension_age(Variable):
    value_type = float
    entity = Person
    label = "State Pension age for this person"
    documentation = (
        "The age at which this person attains State Pension age (pensionable "
        "age), set by their date of birth. Where the statute sets the day on "
        "which it is attained, this is the person's age on that day. The date "
        "of birth comes from age and months_since_last_birthday."
    )
    definition_period = YEAR
    unit = "year"
    reference = (
        "https://www.legislation.gov.uk/ukpga/1995/26/schedule/4",
        "https://www.legislation.gov.uk/ukpga/2014/19/section/26",
    )

    def formula(person, period, parameters):
        p = parameters(period).gov.dwp.state_pension.age
        birth, birth_date = date_of_birth(
            person("age", period),
            person("months_since_last_birthday", period),
            period.start.year,
        )
        # Pensions Act 1995 Sch 4 para 1 rule (1): men born before 6 December
        # 1953 attain pensionable age at 65. Everyone else follows the
        # timetable in rules (2) to (10), which sets either an age or a day.
        male_rule = person("is_male", period) & (birth_date < p.male.born_before)
        return age_attaining_pensionable_age(p, birth, birth_date, male_rule)
