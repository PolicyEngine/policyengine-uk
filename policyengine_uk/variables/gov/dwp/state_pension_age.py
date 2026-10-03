from policyengine_uk.model_api import *
from policyengine_uk.utils.dates import (
    add_months_to_yyyymmdd,
    exact_age_in_months,
    grid_month,
    grid_months_to_yyyymmdd,
    yyyymmdd_to_grid_months,
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
        # Dates are in months on a grid whose months start on the 6th, so the
        # middle of the fiscal year (6 October) is a whole month.
        mid_year = grid_month(period.start.year, 10)
        age_in_months = exact_age_in_months(
            person("age", period), person("months_since_last_birthday", period)
        )
        birth = mid_year - age_in_months
        # The day of birth: the one starting at or after that instant, so the
        # person's legal age on 6 October is age.
        birth_date = grid_months_to_yyyymmdd(birth)

        # Pensions Act 1995 Sch 4 para 1 rule (1): men born before 6 December
        # 1953 attain pensionable age at 65. Everyone else follows the
        # timetable in rules (2) to (10), which sets either an age or a day.
        male_rule = person("is_male", period) & (birth_date < p.male.born_before)
        age_rule = where(male_rule, p.male.age, p.age_by_birth_date.calc(birth_date))
        day_rule = where(male_rule, 0, p.day_by_birth_date.calc(birth_date))
        day_rule_month = where(
            day_rule > 0,
            yyyymmdd_to_grid_months(np.maximum(day_rule, 10101)),
            -np.inf,
        )
        # An age of N years and M months is attained at the commencement of
        # the anniversary (Family Law Reform Act 1969 s.9(1)): the same day of
        # the month, or the month's last day where that day does not exist,
        # which also gives the three days in rule (7A).
        anniversary = yyyymmdd_to_grid_months(
            add_months_to_yyyymmdd(birth_date, age_rule)
        )
        attained = np.maximum(anniversary, day_rule_month)
        return (attained - birth) / 12
