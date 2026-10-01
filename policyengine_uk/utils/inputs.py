"""Whether a variable was entered directly as a simulation input."""

from policyengine_core import periods


def entered_directly(population, variable, period):
    """Whether ``variable`` was set as an input for ``period``.

    The input counts if it was set on this simulation's branch or a branch it
    inherits from, at construction or later with ``set_input``. The value
    must also still be stored. ``Simulation.input_variables`` cannot answer
    this: it is fixed when the simulation is built and ignores the period, so
    it misses later inputs and treats an input for one year as an input for
    every year. Core records each explicit input as (variable, branch,
    period) in ``_user_input_keys``, which is what ``to_input_dataframe``
    reads; this reads the same record.
    """
    simulation = population.simulation
    period = periods.period(period)
    if hasattr(simulation, "_get_visible_branch_names"):
        branches = set(simulation._get_visible_branch_names())
    else:
        branches = {getattr(simulation, "branch_name", "default"), "default"}
    if period not in simulation.get_holder(variable).get_known_periods():
        return False
    return any(
        name == variable and branch in branches and periods.period(key) == period
        for name, branch, key in getattr(simulation, "_user_input_keys", ())
    )
