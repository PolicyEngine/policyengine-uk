"""Pensionable age by date of birth, and ages that follow its timetable.

Pensions Act 1995 Schedule 4 paragraph 1 sets pensionable age (State Pension
age) by date of birth. Rule (1) gives men born before 6 December 1953 the age
of 65; the other rules set an age or a day for everyone else, including every
woman. The qualifying age for State Pension Credit (State Pension Credit Act
2002 s.1(6)) is a woman's pensionable age, and for a man the pensionable age of
a woman born on the same day: the same timetable without rule (1).

Dates are measured in months on the grid in policyengine_uk.utils.dates, whose
months start on the 6th, so the middle of the fiscal year (6 October) is a
whole month.
"""

import numpy as np

from policyengine_uk.utils.dates import (
    add_months_to_yyyymmdd,
    exact_age_in_months,
    grid_month,
    grid_months_to_yyyymmdd,
    yyyymmdd_to_grid_months,
)


def date_of_birth(age, months_since_last_birthday, year: int) -> tuple:
    """The instant of birth, in grid months, and the day of birth (YYYYMMDD).

    The person was born age years and months_since_last_birthday months before
    6 October of the fiscal year starting in ``year``. The day of birth is the
    one starting at or after that instant, so the person's legal age on 6
    October is age.
    """
    birth = grid_month(year, 10) - exact_age_in_months(age, months_since_last_birthday)
    return birth, grid_months_to_yyyymmdd(birth)


def age_attaining_pensionable_age(
    timetable, birth, birth_date, male_rule
) -> np.ndarray:
    """The age, in years, at which pensionable age is attained.

    ``timetable`` is the gov.dwp.state_pension.age parameter node. Where
    ``male_rule`` is true, rule (1) applies (the male age); elsewhere the
    timetable in rules (2) to (10) sets an age or a day, and the later of the
    two is when pensionable age is attained.
    """
    age_rule = np.where(
        male_rule, timetable.male.age, timetable.age_by_birth_date.calc(birth_date)
    )
    day_rule = np.where(male_rule, 0, timetable.day_by_birth_date.calc(birth_date))
    day_rule_month = np.where(
        day_rule > 0,
        yyyymmdd_to_grid_months(np.maximum(day_rule, 10101)),
        -np.inf,
    )
    # An age of N years and M months is attained at the commencement of the
    # anniversary (Family Law Reform Act 1969 s.9(1)): the same day of the
    # month, or the month's last day where that day does not exist, which
    # also gives the three days in rule (7A).
    anniversary = yyyymmdd_to_grid_months(add_months_to_yyyymmdd(birth_date, age_rule))
    attained = np.maximum(anniversary, day_rule_month)
    return (attained - birth) / 12


def months_since_attaining(age, months_since_last_birthday, attained_age) -> np.ndarray:
    """Months between attaining ``attained_age`` and 6 October; negative if
    the person attains it later.

    Rounding to a thousandth of a month (under an hour) removes float error,
    so attaining the age exactly on 6 October, or exactly on 6 April six
    months earlier, counts as having attained it then.
    """
    age_in_months = exact_age_in_months(age, months_since_last_birthday)
    months_since = age_in_months - 12 * np.asarray(attained_age, dtype=np.float64)
    return np.round(months_since, 3)
