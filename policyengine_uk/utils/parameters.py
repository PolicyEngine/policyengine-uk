import datetime

from policyengine_core.model_api import *
from policyengine_core import periods


def str_to_instant(s):
    return periods.Instant(tuple(map(lambda s: int(s), s.split("-"))))


def backdate_parameters(root: str = None, first_instant: str = "2021-01-01") -> Reform:
    first_instant = str_to_instant(first_instant)
    node = root
    for param in node.get_descendants():
        if hasattr(param, "values_list"):
            earliest = param.values_list[-1]
            earliest_value = earliest.value
            earliest_instant = str_to_instant(earliest.instant_str)
            if first_instant < earliest_instant:
                num_days = (earliest_instant.date - first_instant.date).days
                param.update(
                    period=periods.Period(("day", first_instant, num_days)),
                    value=earliest_value,
                )
    return root


def fiscal_year_average(param, year: int):
    """Day-weighted average of a parameter across a UK fiscal year.

    Returns None where any value in the year is missing or non-numeric, so
    the caller can fall back to sampling a single date.
    """
    start = datetime.date(year, 4, 6)
    end = datetime.date(year + 1, 4, 6)

    changes = []
    for value_at_instant in param.values_list:
        try:
            instant = datetime.date.fromisoformat(value_at_instant.instant_str)
        except ValueError:
            return None
        if start < instant < end:
            changes.append(instant)

    if not changes:
        # One value holds all year. Return it as it is: value * days / days
        # can differ from it in the last bit.
        value = param(start.isoformat())
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            return None
        return value

    boundaries = [start, *sorted(changes), end]
    total = 0.0
    for segment_start, segment_end in zip(boundaries, boundaries[1:]):
        value = param(segment_start.isoformat())
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            return None
        total += value * (segment_end - segment_start).days

    return total / (end - start).days


def uk_fiscal_year_period(time_period):
    """Translate a bare year into the UK fiscal year it names.

    A UK parameter change for "2025" means the fiscal year starting 6 April
    2025. Writing it as the calendar year leaves January to April of 2026
    on prior law, which fiscal-year conversion then blends into the value —
    an annual override of 0.5 came out as 0.42. Non-year periods pass
    through untouched.
    """
    year = None
    if isinstance(time_period, int):
        year = time_period
    elif isinstance(time_period, str) and time_period.strip().isdigit():
        year = int(time_period.strip())
    if year is None or not 1900 < year < 2200:
        return time_period
    start = periods.Instant((year, 4, 6))
    days = (datetime.date(year + 1, 4, 6) - datetime.date(year, 4, 6)).days
    return periods.Period(("day", start, days))


# The first fiscal year converted. Parameters are backdated to 1 January 2015
# before conversion.
FIRST_FISCAL_YEAR = 2015


def _fiscal_year_value(param, year: int, blend: bool):
    value = fiscal_year_average(param, year) if blend else None
    if value is None:
        value = param(f"{year}-04-30")
    return value


def _same_value(a, b) -> bool:
    return a is b or (type(a) is type(b) and a == b)


def _fiscal_year_writes(param, blend: bool) -> dict:
    """The years whose fiscal-year value the calendar year does not already hold.

    A calendar year with no value dated after 1 January holds one value all
    year, and for a sampled parameter that is the value read on 30 April, so
    only years with a value dated inside them can change. A blended fiscal
    year also runs into the next calendar year, so every year up to the
    parameter's last dated value is checked against what it already holds.
    Past that year a parameter holds one value, which is its fiscal-year
    value for every later year too.
    """
    if not param.values_list:
        return {}
    dated_inside = {
        int(value.instant_str[:4])
        for value in param.values_list
        if value.instant_str[4:] != "-01-01"
    }
    if blend:
        last_dated_year = max(int(value.instant_str[:4]) for value in param.values_list)
        years = range(FIRST_FISCAL_YEAR, last_dated_year + 1)
    else:
        years = sorted(year for year in dated_inside if year >= FIRST_FISCAL_YEAR)
    values = {year: _fiscal_year_value(param, year, blend) for year in years}
    return {
        year: value
        for year, value in values.items()
        if year in dated_inside or not _same_value(param(f"{year}-01-01"), value)
    }


def convert_to_fiscal_year_parameters(parameters):
    """
    Convert parameters to use UK fiscal year values.

    The UK fiscal year runs April 6 to April 5. When querying a parameter
    for a year (e.g., param("2026")), we want the value at April 30 of
    that year (which represents the fiscal year starting April 6).

    This function sets each year's value, from 2015 on, to the parameter's
    value at April 30 of that year.

    Sampling a single date drops any change taking effect later in the fiscal
    year. Parameters carrying `fiscal_year_blend: true` in their metadata are
    day-weighted across the year instead, which is the right annualisation for
    a rate or threshold that applies to a flow spread over the year. Leave the
    flag off where the value at a point in time is what applies, as for a tax
    charged on a transaction at the rate in force on its date.

    Parameters with ``preserve_calendar_dates: true`` retain statutory dates.
    Their formulas must explicitly annualise the underlying transactions.

    There is no last year. Conversion used to stop at a fixed year, after
    which the calendar value applied, and writing every year to wherever the
    data ends is slow. Instead only the years whose value would change are
    rewritten; every other year already holds its fiscal-year value, so the
    result is the same on every date as writing every year.

    Values are computed for every year before any are written, so that
    rewriting one year cannot affect the reading of another.
    """
    for param in parameters.get_descendants():
        if isinstance(param, Parameter):
            if (param.metadata or {}).get("preserve_calendar_dates", False):
                continue
            blend = (param.metadata or {}).get("fiscal_year_blend", False)
            for year, value in _fiscal_year_writes(param, blend).items():
                param.update(
                    period=f"{year}",
                    value=value,
                )
            # Writing a year marks a parameter modified, and every parameter
            # used to have every year written. Mark the rest too, so the flag
            # reads as it did: Simulation.check_macro_cache in
            # policyengine-core will not reuse cached results that depend on
            # a parameter marked modified.
            param.mark_as_modified()
    return parameters
