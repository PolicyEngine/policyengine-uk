"""Whether a variable was entered directly as a simulation input."""

from policyengine_core import periods


def entered_directly(population, variable, period):
    """Whether the value of ``variable`` for ``period`` is a user input.

    The simulation reads the value from the first of its visible branches
    (its own, then its parents', then the default) that stores one, so this
    asks whether that stored value was set with ``set_input``, when the
    simulation was built or later. ``Simulation.input_variables`` cannot
    answer this: it is fixed when the simulation is built and ignores the
    period, so it misses later inputs and treats an input for one year as an
    input for every year.

    Core records each explicit input as (variable, branch, period) in
    ``_user_input_keys``. The UK ``Simulation`` keeps that record in step
    with storage: a clone gets its own copy, and ``delete_arrays`` drops the
    entries for the arrays it deletes, so a formula result stored later is
    not taken for an input.
    """
    simulation = population.simulation
    period = periods.period(period)
    keys = simulation._user_input_keys
    stored = set(simulation.get_holder(variable).get_known_branch_periods())
    for branch in simulation._get_visible_branch_names():
        if (branch, period) in stored:
            return (variable, branch, period) in keys
    return False
