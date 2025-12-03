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


def convert_instant_to_fiscal_year(instant_str: str) -> str:
    """
    Convert an instant to use UK fiscal year reference date.

    The UK fiscal year runs April 6 to April 5. When querying for January 1
    of a year, we should use April 30 of that year to get the fiscal year value.

    Args:
        instant_str: Date string in format "YYYY-MM-DD" or "YYYY"

    Returns:
        Date string adjusted for UK fiscal year (April 30 if year-only input)

    Example:
        "2026" -> "2026-04-30" (gets fiscal year 2026/27 value)
        "2026-01-01" -> "2026-04-30" (same adjustment)
        "2026-04-30" -> "2026-04-30" (no change, already mid-fiscal-year)
        "2026-06-15" -> "2026-06-15" (no change, specific date requested)
    """
    # Only convert if it's a year-only or January 1 query
    # This preserves behavior for specific date queries
    if len(instant_str) == 4:  # Year only: "2026"
        return f"{instant_str}-04-30"
    elif instant_str.endswith("-01-01"):  # January 1: "2026-01-01"
        year = instant_str[:4]
        return f"{year}-04-30"
    else:
        # Specific date requested - don't modify
        return instant_str


def convert_to_fiscal_year_parameters(parameters):
    """
    DEPRECATED: This function pre-computes fiscal year values.

    For on-the-fly fiscal year handling, use convert_instant_to_fiscal_year()
    in get_parameters_at_instant() instead.

    This function is kept for backward compatibility but will be removed
    in a future version.
    """
    # No longer pre-compute - fiscal year conversion is now done on-the-fly
    # in CountryTaxBenefitSystem.get_parameters_at_instant()
    return parameters
