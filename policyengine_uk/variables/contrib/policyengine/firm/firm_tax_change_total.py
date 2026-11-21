from policyengine_uk.model_api import *
from policyengine_uk.utils.data_source import built_from_data


def _weighted_firm_only_tax(simulation, period) -> float:
    firms = simulation.populations.get("firm")
    if firms is None or firms.count == 0:
        return 0.0
    liability = firms("firm_only_tax", period)
    weight = firms("firm_weight", period)
    return float((liability * weight).sum())


def _employment_allowance_at_liability(simulation, period, liability) -> float:
    """The weighted Employment Allowance under a simulation's own rules,
    claimed against a given employer National Insurance liability."""
    firms = simulation.populations["firm"]
    eligible = firms("employment_allowance_eligible", period)
    amount = simulation.tax_benefit_system.get_parameters_at_instant(
        period
    ).gov.hmrc.national_insurance.employment_allowance.amount
    weight = firms("firm_weight", period)
    return float((eligible * np.minimum(amount, liability) * weight).sum())


def _employment_allowance_rule_change(simulation, baseline, period) -> float:
    """The change in the weighted Employment Allowance from a change in its
    own rules, holding each firm's baseline employer National Insurance
    liability, so a change in employer National Insurance rates or
    thresholds (which reaches households through ni_employer) is not
    counted again."""
    firms = simulation.populations.get("firm")
    baseline_firms = baseline.populations.get("firm")
    if firms is None or baseline_firms is None or firms.count == 0:
        return 0.0
    liability = baseline_firms("firm_employer_ni_before_allowance", period)
    return _employment_allowance_at_liability(
        simulation, period, liability
    ) - _employment_allowance_at_liability(baseline, period, liability)


class firm_tax_change_total(Variable):
    label = "UK change in firm-only tax liability"
    documentation = (
        "The change in firm_only_tax summed over the simulation's firms with "
        "firm_weight, the reform less its baseline, less the change in the "
        "Employment Allowance from a change in its own rules (eligibility "
        "and amount), each firm's employer National Insurance liability "
        "held at its baseline value. Every household carries "
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
        change = (
            _weighted_firm_only_tax(simulation, period)
            - _weighted_firm_only_tax(baseline, period)
            - _employment_allowance_rule_change(simulation, baseline, period)
        )
        return zero + change
