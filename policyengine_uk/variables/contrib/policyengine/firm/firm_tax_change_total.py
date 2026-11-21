from policyengine_uk.model_api import *
from policyengine_uk.utils.data_source import built_from_data


def _weighted_firm_only_tax(simulation, period) -> float:
    firms = simulation.populations.get("firm")
    if firms is None or firms.count == 0:
        return 0.0
    liability = firms("firm_only_tax", period)
    weight = firms("firm_weight", period)
    return float((liability * weight).sum())


class firm_tax_change_total(Variable):
    label = "UK change in firm-only tax liability"
    documentation = (
        "The change in firm_only_tax summed over the simulation's firms with "
        "firm_weight, the reform less its baseline. Every household carries "
        "the same total. It is 0 without a baseline, in a household "
        "situation (which has no UK population of firms to sum), and where "
        "the simulation has no firms. The baseline must carry the same firm "
        "table, or its liability counts as zero."
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
        change = _weighted_firm_only_tax(simulation, period) - _weighted_firm_only_tax(
            baseline, period
        )
        return zero + change
