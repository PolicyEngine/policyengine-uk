"""Capital gains marginal tax rates against the baseline, and the realisation
response they drive."""

import numpy as np

from policyengine_core.simulations import Simulation


# The response, and the part of it on gains qualifying for Business Asset
# Disposal Relief, which capital_gains_tax reads to keep those gains apart.
RESPONSE_VARIABLES = (
    "capital_gains_behavioural_response",
    "capital_gains_badr_behavioural_response",
)


def measure_mtr(
    simulation: Simulation,
    branch_name: str,
    period,
    gains: np.ndarray,
) -> np.ndarray:
    """Measure the capital gains MTR in a simulation, holding gains fixed.

    The branch clones the tax-benefit system because it neutralises the
    behavioural response variable, which would otherwise recurse back into
    this measurement. Cloning keeps that neutralisation off the simulation
    being measured.
    """
    # get_branch returns an existing branch of the requested name without
    # honouring clone_system, and neutralising on a shared system would
    # permanently disable the response variable for the caller. Take a name
    # nothing else holds, then require the clone before touching it.
    while branch_name in simulation.branches:
        branch_name += "_"
    branch = simulation.get_branch(branch_name, clone_system=True)
    if branch.tax_benefit_system is simulation.tax_benefit_system:
        raise RuntimeError(
            "Capital gains MTR measurement requires a cloned tax-benefit "
            "system; refusing to neutralise on the simulation's own."
        )
    for variable in RESPONSE_VARIABLES:
        branch.tax_benefit_system.neutralize_variable(variable)
    branch.set_input("capital_gains_before_response", period, gains)
    mtr = branch.populations["person"]("marginal_tax_rate_on_capital_gains", period)
    del simulation.branches[branch_name]
    return mtr


def measure_capital_gains_mtrs(person, period) -> tuple[np.ndarray, np.ndarray]:
    """Return the reform and baseline capital gains MTRs for each person.

    Both rates are measured at the same level of gains, so the difference
    reflects the reform alone. Returns two zero arrays where the simulation
    has no baseline to compare against.

    Simulations hold their baseline as a separately constructed simulation
    rather than a branch, so the baseline rate has to be measured there. A
    branch of the reform simulation carries reform parameters, and reports no
    rate change however large the reform.
    """
    simulation: Simulation = person.simulation
    baseline = simulation.baseline
    if baseline is None:
        zeros = np.zeros(person.count)
        return zeros, zeros

    gains = person("capital_gains_before_response", period)
    reform_mtr = measure_mtr(simulation, "cgr_measurement", period, gains)
    baseline_mtr = measure_mtr(baseline, "baseline_cgr_measurement", period, gains)
    return reform_mtr, baseline_mtr


def badr_gains_before_response(person, period) -> np.ndarray:
    """Gains qualifying for Business Asset Disposal Relief before any response,
    up to the person's total gains. The lifetime limit is not applied: gains
    above it still qualify, and are charged at the main rates."""
    gains = person("capital_gains_before_response", period)
    return np.maximum(0, np.minimum(person("capital_gains_badr", period), gains))


def realisation_factors(person, period, parameters):
    """Factors by which realised gains scale under a reform, as (main, BADR).

    Gains qualifying for Business Asset Disposal Relief take
    capital_gains_badr_elasticity and the rest of the person's gains take
    capital_gains_elasticity. Both respond to the same share-weighted change
    in the person's marginal rate, so the elasticity is the only difference.
    The marginal tax rate convention has one elasticity for all gains.

    Returns None where there is no response: no baseline to compare against,
    or every elasticity zero.
    """
    p = parameters(period).gov.simulation.capital_gains_responses
    badr_elasticity = p.badr_elasticity if p.separate_badr_elasticity else p.elasticity

    if p.elasticity != 0 and p.mtr_elasticity != 0:
        raise ValueError(
            "gov.simulation.capital_gains_responses.elasticity and "
            "gov.simulation.capital_gains_responses.mtr_elasticity "
            "cannot both be nonzero for the same period."
        )
    if badr_elasticity != 0 and p.mtr_elasticity != 0:
        raise ValueError(
            "gov.simulation.capital_gains_responses.badr_elasticity, in "
            "effect while separate_badr_elasticity is true, and "
            "gov.simulation.capital_gains_responses.mtr_elasticity "
            "cannot both be nonzero for the same period."
        )

    if person.simulation.baseline is None:
        return None
    if p.elasticity == 0 and badr_elasticity == 0 and p.mtr_elasticity == 0:
        return None

    if p.mtr_elasticity != 0:
        change = person("relative_capital_gains_mtr_change", period)
        factor = np.exp(p.mtr_elasticity * change)
        return factor, factor

    change = person("relative_capital_gains_retention_rate_change", period)
    main = np.exp(person("capital_gains_elasticity", period) * change)
    badr = np.exp(person("capital_gains_badr_elasticity", period) * change)
    return main, badr
