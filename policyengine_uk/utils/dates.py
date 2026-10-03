"""Vectorised dates on a monthly grid whose months start on the 6th.

UK tax years start on 6 April, and the State Pension age timetable (Pensions
Act 1995 Schedule 4 paragraph 1) groups dates of birth into periods running
from the 6th of one month to the 5th of the next. Measuring dates in months on
that grid makes every statutory boundary a whole number: month ``m`` runs from
the 6th of calendar month ``m % 12 + 1`` of year ``m // 12`` up to the 5th of
the following month, and a fraction of a month is spread evenly over its days.
Adding whole months keeps the day of the month, as attaining an age of "N
years and M months" does.

Dates are passed in and out as YYYYMMDD integers, which is how parameters
store them.
"""

import numpy as np

_MONTHS_BEFORE_1970 = 12 * 1970

# The fiscal year starts on 6 April, six grid months before its middle (6
# October), where annual status such as is_SP_age is read.
MONTHS_FROM_TAX_YEAR_START_TO_MID_YEAR = 6


def grid_month(year: int, month: int) -> int:
    """The grid month that starts on the 6th of ``month`` in ``year``."""
    return 12 * year + month - 1


def _sixth_of(grid_months: np.ndarray) -> np.ndarray:
    months_since_1970 = (grid_months - _MONTHS_BEFORE_1970).astype("datetime64[M]")
    return months_since_1970.astype("datetime64[D]") + np.timedelta64(5, "D")


def yyyymmdd_to_grid_months(dates) -> np.ndarray:
    """Convert YYYYMMDD integers to (fractional) grid months."""
    dates = np.asarray(dates, dtype=np.int64)
    year, month, day = dates // 10000, dates // 100 % 100, dates % 100
    first_of_month = (12 * year + month - 1 - _MONTHS_BEFORE_1970).astype(
        "datetime64[M]"
    )
    calendar_date = first_of_month.astype("datetime64[D]") + (day - 1).astype(
        "timedelta64[D]"
    )
    whole = 12 * year + month - 1 - (day < 6)
    start = _sixth_of(whole)
    length = (_sixth_of(whole + 1) - start).astype(np.int64)
    elapsed = (calendar_date - start).astype(np.int64)
    return whole + elapsed / length


def grid_months_to_yyyymmdd(months) -> np.ndarray:
    """Convert (fractional) grid months to YYYYMMDD integers: the calendar day
    that starts at or after each instant.

    A person attains an age at the commencement of the anniversary of their
    date of birth (Family Law Reform Act 1969 s.9(1)). Taking a birth instant
    that falls within a day as the next day keeps the whole number of years
    between it and a later midnight equal to the person's legal age there.
    """
    months = np.asarray(months, dtype=np.float64)
    whole = np.floor(months).astype(np.int64)
    start = _sixth_of(whole)
    length = (_sixth_of(whole + 1) - start).astype(np.int64)
    # Model variables are stored as float32, which can put an instant that is
    # exactly midnight a fraction of a second either side of it. A tolerance
    # of about a minute and a half keeps it on its day.
    elapsed = np.ceil((months - whole) * length - 1e-3).astype(np.int64)
    overflow = elapsed >= length
    whole = np.where(overflow, whole + 1, whole)
    elapsed = np.where(overflow, 0, elapsed)
    start = _sixth_of(whole)
    calendar_date = start + elapsed.astype("timedelta64[D]")
    calendar_month = calendar_date.astype("datetime64[M]")
    year = calendar_month.astype(np.int64) // 12 + 1970
    month = calendar_month.astype(np.int64) % 12 + 1
    day = (calendar_date - calendar_month.astype("datetime64[D]")).astype(np.int64) + 1
    return year * 10000 + month * 100 + day


def add_months_to_yyyymmdd(dates, months) -> np.ndarray:
    """Add whole months to YYYYMMDD dates, keeping the day of the month.

    Where that day does not exist in the target month, the result is the
    month's last day, as when a person born on 31 July attains an age of some
    years and four months on 30 November. That also puts a 29 February
    anniversary on 28 February in other years; the statute does not say, and
    State Pension age status, read on the 6th, is the same either way.
    """
    dates = np.asarray(dates, dtype=np.int64)
    months = np.round(np.asarray(months, dtype=np.float64)).astype(np.int64)
    year, month, day = dates // 10000, dates // 100 % 100, dates % 100
    target = 12 * year + month - 1 + months
    first_of_month = (target - _MONTHS_BEFORE_1970).astype("datetime64[M]")
    days_in_month = (
        (first_of_month + np.timedelta64(1, "M")).astype("datetime64[D]")
        - first_of_month.astype("datetime64[D]")
    ).astype(np.int64)
    return (
        (target // 12) * 10000
        + (target % 12 + 1) * 100
        + np.minimum(day, days_in_month)
    )


# Months since the last birthday stop about four minutes short of 12, beyond
# the tolerance above, so an exact age never rounds onto the next birthday.
_LATEST_MONTHS_SINCE_BIRTHDAY = 12 - 1e-4


def exact_age_in_months(age, months_since_last_birthday) -> np.ndarray:
    """Exact age in months, in float64: at around 24,000 months, float32 is
    only good to an hour.

    A fractional age is the exact age. A whole age adds the months since the
    last birthday, which stop about four minutes short of 12 so the exact age
    never rounds onto the next birthday.
    """
    age = np.asarray(age, dtype=np.float64)
    whole_years = np.floor(age)
    fraction = age - whole_years
    months = np.where(
        fraction > 0,
        12 * fraction,
        np.asarray(months_since_last_birthday, dtype=np.float64),
    )
    return 12 * whole_years + np.clip(months, 0, _LATEST_MONTHS_SINCE_BIRTHDAY)
