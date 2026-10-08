"""Date operations shared by Housing Benefit stock/status rules."""

import numpy as np


def calendar_dates(yyyymmdd):
    """Convert existing validated YYYYMMDD date values to calendar-day arrays."""
    values = np.asarray(yyyymmdd, dtype=np.int64)
    months = (12 * (values // 10000 - 1970) + values // 100 % 100 - 1).astype(
        "datetime64[M]"
    )
    return months.astype("datetime64[D]") + (values % 100 - 1).astype("timedelta64[D]")


def september_first_monday(birth_date, birthday_age):
    """The first Monday in September following the specified birthday."""
    born = np.asarray(birth_date, dtype=np.int64)
    year = born // 10000 + birthday_age
    birthday = calendar_dates(year * 10000 + born % 10000)
    september = (12 * (year - 1970) + 8).astype("datetime64[M]").astype("datetime64[D]")
    # 1 January 1970 was Thursday (weekday 3, Monday 0).
    monday = september + ((-september.astype(np.int64) - 3) % 7).astype(
        "timedelta64[D]"
    )
    year = year + (monday <= birthday)
    september = (12 * (year - 1970) + 8).astype("datetime64[M]").astype("datetime64[D]")
    return september + ((-september.astype(np.int64) - 3) % 7).astype("timedelta64[D]")
