"""Project Savings Credit thresholds from the guarantee and maximum award.

The standard minimum guarantee rises with earnings, while the Savings Credit
maximum rises with September CPI (HCWS1101). Under the 60% phase-in rule,
maximum = phase_in * (standard minimum guarantee - threshold), so the
threshold is the guarantee less maximum / phase_in. Keep the published
thresholds, including their rounding, and derive only subsequent years.

Run after general uprating and before fiscal-year conversion, on both the
main tree and its baseline copy. Reprocessing a reform then reads its changed
guarantee, maximum and phase-in rate.
"""

from policyengine_core.parameters import ParameterNode
from policyengine_core.parameters.parameter_at_instant import ParameterAtInstant


def project_savings_credit_threshold(parameters: ParameterNode) -> ParameterNode:
    """Fill the years after each threshold's last stated value."""
    pc = parameters.gov.dwp.pension_credit
    sc = pc.savings_credit
    index = parameters.gov.economic_assumptions.indices.earnings_uprating
    last_year = max(int(entry.instant_str[:4]) for entry in index.values_list)
    for relation, threshold in sc.threshold.children.items():
        last_stated = max(entry.instant_str for entry in threshold.values_list)
        for year in range(int(last_stated[:4]) + 1, last_year + 1):
            sample = f"{year}-04-30"
            guarantee = pc.guarantee_credit.minimum_guarantee.children[relation](sample)
            maximum = sc.maximum.children[relation](sample)
            phase_in = sc.rate.phase_in(sample)
            value = guarantee - maximum / phase_in
            threshold.values_list.append(
                ParameterAtInstant(threshold.name, f"{year}-01-01", data=value)
            )
        threshold.values_list.sort(key=lambda entry: entry.instant_str, reverse=True)
        threshold.mark_as_modified()
    sc.threshold.clear_parent_cache()
    return parameters
