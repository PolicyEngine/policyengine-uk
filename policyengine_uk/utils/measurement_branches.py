"""Branches that measure a simulation's results at inputs set on the branch.

Behavioural responses compare a reform with its baseline at the same inputs
before the response: the labour supply responses at the reform's earnings and
gains, and the capital gains response at the reform's gains. Each measurement
runs in a branch of the reform simulation or of its baseline, with every
behavioural response neutralised and those inputs set.
"""

from typing import Dict

import numpy as np

# Every behavioural response. Each is measured from the position before any
# response, so one response's measurement does not include another response,
# and does not recompute it inside its own branches: the labour supply
# measurement takes gains before their realisation response, and the capital
# gains measurement takes earnings before the labour supply response.
BEHAVIOURAL_RESPONSES = (
    "employment_income_behavioral_response",
    "capital_gains_behavioural_response",
    "capital_gains_badr_behavioural_response",
)


def retained_input_variables(simulation) -> set:
    """Names retained by resets and measurements, including later inputs.

    A key can outlive its array or belong to a branch this simulation cannot
    read. Check the supplied storage record as well as branch visibility, so
    a calculated or deleted value does not become a fixed input.
    """
    retained = set(getattr(simulation, "input_variables", None) or ())
    visible = set(simulation._get_visible_branch_names())
    for name, branch, period in tuple(
        getattr(simulation, "_user_input_keys", None) or ()
    ):
        if branch in visible and simulation.get_holder(name)._stores_user_input(
            period, branch
        ):
            retained.add(name)
    return retained


def drop_calculated_totals(simulation, name: str) -> None:
    """Delete the values of a stored household total that the simulation
    calculated, keeping those the data or a caller supplied.

    A total in STORED_HOUSEHOLD_TOTALS that the data store counts as an input
    by name, but the simulation calculates it for the years the data do not
    hold, from the stored years and the parts. Core's own record of inputs
    (``_user_input_keys``, checked by ``Holder._stores_user_input``) decides
    which values go, as it does for ``drop_computed_arrays``.
    """
    simulation.get_holder(name)._drop_computed()
    cache = getattr(simulation, "_fast_cache", None)
    if cache:
        simulation._fast_cache = {
            key: value for key, value in cache.items() if key[0] != name
        }


def drop_calculated_values(simulation) -> None:
    """Delete the values a simulation has calculated, keeping its inputs.

    Inputs are variables without a formula, variables the simulation was built
    from, and variables set since through set_input, as a scenario's
    simulation modifier does to formula variables. A stored household total
    keeps only the years supplied for it (see drop_calculated_totals). It
    visits only the variables the simulation holds values for.
    """
    from policyengine_uk.data.economic_assumptions import STORED_HOUSEHOLD_TOTALS

    supplied = retained_input_variables(simulation)
    variables = simulation.tax_benefit_system.variables
    held = {
        name
        for population in simulation.populations.values()
        for name in getattr(population, "_holders", {})
    }
    for name in held:
        variable = variables.get(name)
        if variable is None:
            continue
        if name in supplied or variable.is_input_variable():
            if name in STORED_HOUSEHOLD_TOTALS:
                drop_calculated_totals(simulation, name)
            continue
        simulation.delete_arrays(name)


def held_behavioural_responses(person, period) -> dict:
    """The behavioural responses a simulation calculated, to hold fixed in a
    branch that steps one of its inputs to measure a marginal rate.

    The branch shares the simulation's tax-benefit system. A response
    recalculated there would be measured again: at the stepped input, against
    a baseline without the step, and with the step undone inside the
    measurement, whose own marginal rate branches recalculate every variable
    with a formula. A marginal rate is the change at fixed behaviour, so the
    branch reads the simulation's responses instead. Responses neutralised in
    the simulation (as in a measurement branch) are not held.
    """
    variables = person.simulation.tax_benefit_system.variables
    return {
        response: person(response, period)
        for response in BEHAVIOURAL_RESPONSES
        if not variables[response].is_neutralized
    }


def hold_behavioural_responses(branch, period, held: dict) -> None:
    """Set the responses :func:`held_behavioural_responses` returned on a
    branch, so the branch reads them instead of measuring them again."""
    for response, values in held.items():
        branch.set_input(response, period, values)


def measurement_branch(
    simulation,
    name: str,
    period,
    inputs: Dict[str, np.ndarray],
):
    """A branch of ``simulation`` with every behavioural response neutralised
    and ``inputs`` set for ``period``.

    The branch clones the tax-benefit system, so neutralising the responses
    there keeps them live in the simulation, and no response recurses back
    into a measurement.

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
    for variable in BEHAVIOURAL_RESPONSES:
        branch.tax_benefit_system.neutralize_variable(variable)
    drop_calculated_values(branch)
    for variable, value in inputs.items():
        branch.set_input(variable, period, value)
    return branch
