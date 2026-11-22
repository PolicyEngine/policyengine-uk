from policyengine_uk.model_api import *
from policyengine_uk.utils.data_source import built_from_data


def _weighted_firm_only_tax(simulation, period) -> float:
    firms = simulation.populations.get("firm")
    if firms is None or firms.count == 0:
        return 0.0
    liability = firms("firm_only_tax", period)
    weight = firms("firm_weight", period)
    return float((liability * weight).sum())


def _employment_allowance_under_rules(
    simulation, period, baseline_firms, liability
) -> float:
    """The weighted Employment Allowance under ``simulation``'s rules (the
    amount and the eligibility conditions), with every quantity that moves
    with employer National Insurance (this year's liability and, for the
    prior-year limit of 2020-21 to 2024-25, last year's) taken from the
    baseline firms. This mirrors ``employment_allowance_eligible`` and
    ``employment_allowance``; keep them in step."""
    firms = simulation.populations["firm"]
    p = simulation.tax_benefit_system.get_parameters_at_instant(
        period
    ).gov.hmrc.national_insurance.employment_allowance
    excluded_public_body = firms("firm_is_public_body", period) & ~firms(
        "firm_is_charity", period
    )
    excluded_single_director = (
        firms("firm_is_single_director_company", period)
        & p.excludes_single_director_companies
    )
    prior_year_liabilities = baseline_firms(
        "firm_prior_year_secondary_class_1_liabilities", period
    )
    excluded_by_prior_year_liabilities = (
        prior_year_liabilities >= p.prior_year_liabilities_limit
    )
    eligible = (
        firms("firm_claims_employment_allowance", period)
        & ~excluded_public_body
        & ~excluded_single_director
        & ~excluded_by_prior_year_liabilities
    )
    weight = firms("firm_weight", period)
    return float((eligible * np.minimum(p.amount, liability) * weight).sum())


def _employment_allowance_rule_change(simulation, baseline, period) -> float:
    """The change in the weighted Employment Allowance from a change in its
    own rules, holding each firm's baseline employer National Insurance
    liabilities (this year's and last year's), so a change in employer
    National Insurance rates or thresholds (which reaches households
    through ni_employer) is not counted again."""
    firms = simulation.populations.get("firm")
    baseline_firms = baseline.populations.get("firm")
    if firms is None or firms.count == 0:
        return 0.0
    if baseline_firms is None or baseline_firms.count != firms.count:
        raise ValueError(
            "The baseline holds a different number of firms from the "
            "reform, so their Employment Allowances cannot be compared "
            "firm by firm. Build both from the same firm table."
        )
    liability = baseline_firms("firm_employer_ni_before_allowance", period)
    return _employment_allowance_under_rules(
        simulation, period, baseline_firms, liability
    ) - _employment_allowance_under_rules(baseline, period, baseline_firms, liability)


class firm_tax_change_total(Variable):
    label = "UK change in firm-only tax liability"
    documentation = (
        "The change in firm_only_tax summed over the simulation's firms with "
        "firm_weight, the reform less its baseline, less the change in the "
        "Employment Allowance from a change in its own rules (eligibility "
        "and amount), each firm's employer National Insurance liability "
        "(this year's, and last year's for the prior-year limit) held at "
        "their baseline values. Every household carries "
        "the same total. It is 0 without a baseline, in a household "
        "situation (which has no UK population of firms to sum), and where "
        "the simulation has no firms. The baseline must carry the same firm "
        "table; a baseline with a different number of firms (including "
        "none) raises an error."
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
