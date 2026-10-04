from policyengine_uk.model_api import *
from policyengine_uk.utils.dates import (
    add_months_to_yyyymmdd,
    exact_age_in_months,
    grid_month,
    grid_months_to_yyyymmdd,
)


class state_pension_age_date(Variable):
    value_type = int
    entity = Person
    label = "date this person attains State Pension age"
    documentation = (
        "The day on which this person attains State Pension age (pensionable "
        "age), written as a YYYYMMDD number. It is set by their date of birth, "
        "which comes from age and months_since_last_birthday."
    )
    definition_period = YEAR
    unit = "date"
    reference = (
        "https://www.legislation.gov.uk/ukpga/1995/26/schedule/4",
        "https://www.legislation.gov.uk/ukpga/2014/19/section/26",
    )

    def formula(person, period, parameters):
        p = parameters(period).gov.dwp.state_pension.age
        # Dates are in months on a grid whose months start on the 6th, so the
        # middle of the fiscal year (6 October) is a whole month.
        age_in_months = exact_age_in_months(
            person("age", period), person("months_since_last_birthday", period)
        )
        # The day of birth: the one starting at or after that instant, so the
        # person's legal age on 6 October is age.
        birth_date = grid_months_to_yyyymmdd(
            grid_month(period.start.year, 10) - age_in_months
        )

        # Pensions Act 1995 Sch 4 para 1 rule (1): men born before 6 December
        # 1953 attain pensionable age at 65. Everyone else follows the
        # timetable in rules (2) to (10), which sets either an age or a day.
        male_rule = person("is_male", period) & (birth_date < p.male.born_before)
        age_rule = where(male_rule, p.male.age, p.age_by_birth_date.calc(birth_date))
        day_rule = where(male_rule, 0, p.day_by_birth_date.calc(birth_date))
        # An age of N years and M months is attained at the commencement of
        # the anniversary (Family Law Reform Act 1969 s.9(1)): the same day of
        # the month, or the month's last day where that day does not exist,
        # which also gives the three days in rule (7A). Where the statute sets
        # a day instead, the day rule is later; otherwise it is zero.
        anniversary = add_months_to_yyyymmdd(birth_date, age_rule)
        return np.maximum(anniversary, day_rule)
