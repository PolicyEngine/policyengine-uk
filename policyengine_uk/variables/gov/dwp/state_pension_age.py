from policyengine_uk.model_api import *
from policyengine_uk.utils.dates import (
    add_months_to_yyyymmdd,
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
        # float64: at around 24,000 months, float32 is only good to an hour.
        age = np.floor(person("age", period)).astype(np.float64)
        months = person("months_since_last_birthday", period).astype(np.float64)
        age_in_months = 12 * age + months
        birth = mid_year - age_in_months
        birth_date = grid_months_to_yyyymmdd(birth)

        # Pensions Act 1995 Sch 4 para 1 rule (1): men born before 6 December
        # 1953 attain pensionable age at 65. Everyone else follows the
        # timetable in rules (2) to (10), which sets either an age or a day.
        year, month, day = p.male.born_before
        male_rule = person("is_male", period) & (
            birth_date < year * 10000 + month * 100 + day
        )
        age_rule = where(male_rule, p.male.age, p.age_by_birth_date.calc(birth_date))
        day_rule = where(male_rule, 0, p.day_by_birth_date.calc(birth_date))
        day_rule_month = where(
            day_rule > 0,
            yyyymmdd_to_grid_months(np.maximum(day_rule, 10101)),
            -np.inf,
        )
        # An age of N years and M months is attained on the same day of the
        # month, or the month's last day where that day does not exist, which
        # also gives the three days in rule (7A). The time of day carries over,
        # so someone born late on 6 October is not yet older at its start.
        time_of_day = birth - yyyymmdd_to_grid_months(birth_date)
        anniversary = (
            yyyymmdd_to_grid_months(add_months_to_yyyymmdd(birth_date, age_rule))
            + time_of_day
        )
        attained = np.maximum(anniversary, day_rule_month)
        return (attained - birth) / 12
