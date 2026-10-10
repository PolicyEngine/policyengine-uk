"""Branches that measure a reform and its baseline with labour supply held
fixed, for the elasticity-based labour supply responses."""

from contextlib import contextmanager

from policyengine_uk.utils.measurement_branches import measurement_branch

RESPONSE_VARIABLE = "employment_income_behavioral_response"

# Set on both branches to the values of the simulation whose response is being
# measured, so that the two differ in policy alone.
HELD_INPUTS = ("employment_income_before_lsr", "capital_gains_before_response")

# The pair of branches of each measurement under way, by simulation and period.
# The income and substitution terms of one response read the same pair.
_open_measurements = {}


@contextmanager
def measurement_branches(person, period):
    """Yield the branches that measure the reform and the baseline with labour
    supply held fixed, as (reform, baseline).

    Simulations hold their baseline as a separately constructed simulation
    (``simulation.baseline``) rather than a branch named ``baseline``, so the
    baseline is measured there. A branch of the reform simulation carries
    reform parameters, and reports no change in net income or marginal rates
    however large the reform.

    The pair lasts as long as the outermost use: the response opens it, and
    the relative income and wage changes it then asks for read the same pair.
    """
    simulation = person.simulation
    key = (id(simulation), period)
    if key in _open_measurements:
        yield _open_measurements[key]
        return
    inputs = {variable: person(variable, period) for variable in HELD_INPUTS}
    branches = tuple(
        measurement_branch(sim, name, period, [RESPONSE_VARIABLE], inputs)
        for sim, name in (
            (simulation, "lsr_measurement"),
            (simulation.baseline, "baseline_lsr_measurement"),
        )
    )
    _open_measurements[key] = branches
    try:
        yield branches
    finally:
        del _open_measurements[key]
