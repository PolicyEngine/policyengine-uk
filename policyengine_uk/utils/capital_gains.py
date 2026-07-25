"""Measurement of capital gains marginal tax rates against the baseline."""

import numpy as np

from policyengine_core.simulations import Simulation


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
    branch = simulation.get_branch(branch_name, clone_system=True)
    branch.tax_benefit_system.neutralize_variable("capital_gains_behavioural_response")
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
