"""Branches that measure a simulation's results at inputs set on the branch.

Behavioural responses compare a reform with its baseline at the same inputs
before the response: the labour supply responses at the reform's earnings, and
the capital gains response at the reform's gains. Each measurement runs in a
branch of the reform simulation or of its baseline, with the response
neutralised and those inputs set.
"""

from typing import Dict, Iterable

import numpy as np


def drop_calculated_values(simulation) -> None:
    """Delete the values a simulation has calculated, keeping its inputs.

    Inputs are variables without a formula, variables the simulation was built
    from, and variables set since through set_input, as a scenario's
    simulation modifier does to formula variables. Only variables the
    simulation holds values for are visited.
    """
    supplied = set(getattr(simulation, "input_variables", None) or ())
    supplied.update(
        name for name, _, _ in getattr(simulation, "_user_input_keys", None) or ()
    )
    variables = simulation.tax_benefit_system.variables
    held = {
        name
        for population in simulation.populations.values()
        for name in getattr(population, "_holders", {})
    }
    for name in held:
        variable = variables.get(name)
        if variable is None or name in supplied or variable.is_input_variable():
            continue
        simulation.delete_arrays(name)


def measurement_branch(
    simulation,
    name: str,
    period,
    neutralised: Iterable[str],
    inputs: Dict[str, np.ndarray],
):
    """A branch of ``simulation`` with the ``neutralised`` variables
    neutralised and ``inputs`` set for ``period``.

    The branch clones the tax-benefit system, so neutralising a response there
    keeps it live in the simulation, and the response does not recurse back
    into its own measurement.

    A branch starts from every value its simulation holds, and would read
    those in place of values at the inputs set here: results the simulation
    calculated at its own inputs before the response (a baseline's, if its
    data differ from the reform's), or results that include a response it
    calculated earlier. So the branch drops what the simulation calculated and
    measures from inputs alone. Its results then do not depend on what either
    simulation calculated before.

    Only the caller holds the branch: it is not kept in ``simulation.branches``,
    so the next measurement starts afresh.
    """
    # get_branch returns an existing branch of the requested name without
    # honouring clone_system, and neutralising on a shared system would
    # permanently disable the response for the simulation. Take a name nothing
    # else holds, then require the clone before touching it.
    while name in simulation.branches or name == simulation.branch_name:
        name += "_"
    branch = simulation.get_branch(name, clone_system=True)
    del simulation.branches[name]
    if branch.tax_benefit_system is simulation.tax_benefit_system:
        raise RuntimeError(
            "A measurement branch requires a cloned tax-benefit system; "
            "refusing to neutralise on the simulation's own."
        )
    for variable in neutralised:
        branch.tax_benefit_system.neutralize_variable(variable)
    drop_calculated_values(branch)
    for variable, value in inputs.items():
        branch.set_input(variable, period, value)
    return branch
