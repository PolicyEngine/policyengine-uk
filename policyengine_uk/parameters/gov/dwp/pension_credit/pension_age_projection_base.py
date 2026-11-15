"""The enacted year the pension-age forecast indices start from.

The Savings Credit threshold and protected pension-age Housing Benefit
allowance indices are built from the standard minimum guarantee, threshold and
allowances of the last year with enacted rates. That year is the latest one
with an explicit value, so entering the next year's rates moves the base with
them. Every one of these parameters must reach the same year: an uprating
update that misses one would otherwise build the indices from a projected
amount, so it fails here instead.
"""

from policyengine_core.parameters import Parameter, ParameterNode

BASE_PARAMETERS = (
    "gov.dwp.pension_credit.guarantee_credit.minimum_guarantee.SINGLE",
    "gov.dwp.pension_credit.guarantee_credit.minimum_guarantee.COUPLE",
    "gov.dwp.pension_credit.savings_credit.threshold.SINGLE",
    "gov.dwp.pension_credit.savings_credit.threshold.COUPLE",
    "gov.dwp.housing_benefit.allowances.single.aged",
    "gov.dwp.housing_benefit.allowances.lone_parent.aged",
    "gov.dwp.housing_benefit.allowances.couple.aged",
)


def last_enacted_year(parameter: Parameter) -> int:
    """The year of the parameter's latest explicit value."""
    return max(int(entry.instant_str[:4]) for entry in parameter.values_list)


def projection_base_year(parameters: ParameterNode) -> int:
    """The last year with enacted rates for every projected parameter.

    Callers supply the YAML as loaded, before any modifier or dated reform:
    later reform values anchor uprating, not a new projection base. The
    consistency guard therefore validates YAML rates updates alone.
    """
    years = {
        path: last_enacted_year(parameters.get_child(path)) for path in BASE_PARAMETERS
    }
    if len(set(years.values())) > 1:
        listed = ", ".join(f"{path} {year}" for path, year in years.items())
        raise ValueError(
            "The pension-age projections need the standard minimum guarantee, "
            "the Savings Credit threshold and the pension-age Housing Benefit "
            "allowances enacted to the same year. Their last explicit values "
            f"are in: {listed}."
        )
    return years[BASE_PARAMETERS[0]]
