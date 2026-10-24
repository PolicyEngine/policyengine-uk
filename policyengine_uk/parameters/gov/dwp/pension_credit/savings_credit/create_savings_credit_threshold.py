"""Project Savings Credit thresholds from the guarantee and maximum award.

The standard minimum guarantee rises with earnings, while the Savings Credit
maximum rises with September CPI (HCWS1101). Under the 60% phase-in rule,
maximum = phase_in * (standard minimum guarantee - threshold), so the
threshold is the guarantee less maximum / phase_in. Keep the published
thresholds, including their rounding, and derive only subsequent years.

A zero phase-in rate pays no Savings Credit at any threshold, and the
maximum fixes none, so a year with a zero rate keeps the threshold in force
before it.

Run after general uprating and before fiscal-year conversion, on both the
main tree and its baseline copy. Reprocessing a reform then reads its changed
guarantee, maximum and phase-in rate.
"""

from typing import Any, Callable

from policyengine_core.parameters import Parameter, ParameterNode
from policyengine_core.parameters.parameter_at_instant import ParameterAtInstant


def last_projected_year(parameters: ParameterNode) -> int:
    """The last year of the earnings index, which the projections run to."""
    index = parameters.gov.economic_assumptions.indices.earnings_uprating
    return max(int(entry.instant_str[:4]) for entry in index.values_list)


def extend_after_last_stated(
    parameter: Parameter,
    last_year: int,
    derive: Callable[[str, Any], Any],
) -> None:
    """Add a value for each year after the parameter's last stated value.

    ``derive(sample, previous)`` gives the year's value from the other
    parameters at its 30 April ``sample``; ``previous`` is the value in force
    before it. Each value applies from 1 January, as uprating's do.
    """
    last = max(parameter.values_list, key=lambda entry: entry.instant_str)
    previous = last.value
    for year in range(int(last.instant_str[:4]) + 1, last_year + 1):
        previous = derive(f"{year}-04-30", previous)
        parameter.values_list.append(
            ParameterAtInstant(parameter.name, f"{year}-01-01", data=previous)
        )
    parameter.values_list.sort(key=lambda entry: entry.instant_str, reverse=True)
    parameter.mark_as_modified()


def project_savings_credit_threshold(parameters: ParameterNode) -> ParameterNode:
    """Fill the years after each threshold's last stated value."""
    pc = parameters.gov.dwp.pension_credit
    sc = pc.savings_credit
    last_year = last_projected_year(parameters)
    for relation, threshold in sc.threshold.children.items():
        guarantee = pc.guarantee_credit.minimum_guarantee.children[relation]
        maximum = sc.maximum.children[relation]

        def derive(sample, previous):
            phase_in = sc.rate.phase_in(sample)
            if phase_in == 0:
                return previous
            return guarantee(sample) - maximum(sample) / phase_in

        extend_after_last_stated(threshold, last_year, derive)
    sc.threshold.clear_parent_cache()
    return parameters
