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

    boundaries = [start, *sorted(changes), end]
    total = 0.0
    for segment_start, segment_end in zip(boundaries, boundaries[1:]):
        value = param(segment_start.isoformat())
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            return None
        total += value * (segment_end - segment_start).days

    return total / (end - start).days


def convert_to_fiscal_year_parameters(parameters):
    """
    Convert parameters to use UK fiscal year values.

    The UK fiscal year runs April 6 to April 5. When querying a parameter
    for a year (e.g., param("2026")), we want the value at April 30 of
    that year (which represents the fiscal year starting April 6).

    This function samples each parameter at April 30 of each year and
    sets that as the value for the entire year period.

    Sampling a single date drops any change taking effect later in the fiscal
    year. Parameters carrying `fiscal_year_blend: true` in their metadata are
    day-weighted across the year instead, which is the right annualisation for
    a rate or threshold that applies to a flow spread over the year. Leave the
    flag off where the value at a point in time is what applies, as for a tax
    charged on a transaction at the rate in force on its date.

    Values are computed for every year before any are written, so that
    rewriting one year cannot affect the reading of another.
    """
    # Cover years from 2015 through 2040 for long-term projections
    YEARS = list(range(2015, 2041))
    for param in parameters.get_descendants():
        if isinstance(param, Parameter):
            blend = (param.metadata or {}).get("fiscal_year_blend", False)
            values = {}
            for year in YEARS:
                value = fiscal_year_average(param, year) if blend else None
                if value is None:
                    value = param(f"{year}-04-30")
                values[year] = value
            for year, value in values.items():
                param.update(
                    period=f"{year}",
                    value=value,
                )
    return parameters
