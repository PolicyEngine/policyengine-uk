from policyengine_uk.model_api import *
from policyengine_uk.utils.data_source import built_from_data


def _firms(simulation):
    firms = simulation.populations.get("firm")
    if firms is None or firms.count == 0:
        return None
    return firms


def _weighted_total(firms, variable: str, period) -> float:
    if firms is None:
        return 0.0
    return float((firms(variable, period) * firms("firm_weight", period)).sum())


class firm_tax_change_total(Variable):
    label = "UK change in firm-only tax liability"
    documentation = (
        "The change in firm_only_tax summed over the simulation's firms with "
        "firm_weight, the reform less its baseline, less the change in the "
        "weighted Employment Allowance, each computed by its own simulation "
        "on its own employer National Insurance liabilities. Household "
        "ni_employer counts the change in gross employer National Insurance, "
        "so subtracting the full change in the allowance leaves the change "
        "in what firms pay after it: a firm that stays under the allowance "
        "after a rate rise nets to zero. Without a supplied prior-year "
        "input, the 2020-21 to 2024-25 prior-year limit reads this year's "
        "liabilities under each simulation's own rules, so a rate rise can "
        "take a firm over the limit and remove its allowance. Every "
        "household carries the same "
        "total. It is 0 without a baseline, in a household situation (which "
        "has no UK population of firms to sum), and where the simulation has "
        "no firms. The baseline must carry the same firm table; a baseline "
        "with a different number of firms (including none) raises an error."
    )
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(household, period, parameters):
        simulation = household.simulation
        zero = np.zeros(household.count)
        baseline = simulation.baseline
        if baseline is None or not built_from_data(simulation):
            return zero
        firms = _firms(simulation)
        if firms is None:
            return zero
        baseline_firms = _firms(baseline)
        if baseline_firms is None or baseline_firms.count != firms.count:
            raise ValueError(
                "The baseline holds a different number of firms from the "
                "reform, so their taxes cannot be compared firm by firm. "
                "Build both from the same firm table."
            )
        change = (
            _weighted_total(firms, "firm_only_tax", period)
            - _weighted_total(baseline_firms, "firm_only_tax", period)
            - _weighted_total(firms, "employment_allowance", period)
            + _weighted_total(baseline_firms, "employment_allowance", period)
        )
        return zero + change
