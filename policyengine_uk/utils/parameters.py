from policyengine_core.model_api import *
from policyengine_core import periods


def str_to_instant(s):
    return periods.Instant(tuple(map(lambda s: int(s), s.split("-"))))


def backdate_parameters(
    root: str = None, first_instant: str = "2021-01-01"
) -> Reform:
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


def convert_to_fiscal_year_parameters(parameters):
    """
    Convert parameters to use UK fiscal year values.

    The UK fiscal year runs April 6 to April 5. When querying a parameter
    for a year (e.g., param("2026")), we want the value at April 30 of
    that year (which represents the fiscal year starting April 6).

    This function samples each parameter at April 30 of each year and
    sets that as the value for the entire year period.
    """
    # Cover years from 2015 through 2040 for long-term projections
    YEARS = list(range(2015, 2041))
    for param in parameters.get_descendants():
        if isinstance(param, Parameter):
            for year in YEARS:
                value_mid_year = param(f"{year}-04-30")
                param.update(
                    period=f"{year}",
                    value=value_mid_year,
                )
    return parameters
