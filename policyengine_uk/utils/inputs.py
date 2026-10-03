"""Which periods of a variable hold entered values rather than calculated ones."""

from typing import List, Optional

from policyengine_core.periods import Period


def _readable_branches(simulation) -> List[str]:
    """The branches whose values ``simulation`` reads: its own, then each
    ancestor branch, then ``default`` (the order ``Holder.get_array`` uses)."""
    names = []
    branch = simulation
    while branch is not None:
        names.append(getattr(branch, "branch_name", "default"))
        branch = getattr(branch, "parent_branch", None)
    names.append("default")
    return list(dict.fromkeys(names))


def input_periods(simulation, variable_name: str) -> List[Period]:
    """The periods at which ``variable_name`` holds an entered value that this
    simulation (branch) reads, earliest first.

    An entered value is a dataset column or a situation input, put in through
    ``set_input``. A value that a formula, the default or auto-carry-over gave
    is not one. Formulas that ask whether a value was entered must use this,
    not whether a value is stored (``holder.get_array(period) is not None``).
    A value is stored for a period as soon as anything calculates the variable
    for it, so that test's answer depends on what was calculated first.

    This reads the record core keeps of ``set_input`` calls
    (``Simulation._user_input_keys``), which ``put_in_cache`` never adds to.
    It leaves out entries made in branches this one cannot read, and entries
    whose value is no longer stored.
    """
    holder = simulation.get_holder(variable_name)
    definition_period = holder.variable.definition_period
    readable = _readable_branches(simulation)
    periods = {
        period
        for name, branch_name, period in getattr(simulation, "_user_input_keys", ())
        if name == variable_name
        and branch_name in readable
        and period.unit == definition_period
    }
    return sorted(
        (
            period
            for period in periods
            if holder.get_array(period, simulation.branch_name) is not None
        ),
        key=lambda period: period.start,
    )


def latest_input_period_before(
    simulation, variable_name: str, period: Period
) -> Optional[Period]:
    """The latest period before ``period`` at which ``variable_name`` holds an
    entered value (see ``input_periods``), or ``None`` if there is none."""
    earlier = [
        input_period
        for input_period in input_periods(simulation, variable_name)
        if input_period.start < period.start
    ]
    return earlier[-1] if earlier else None


def has_input_by(simulation, variable_name: str, period: Period) -> bool:
    """Whether ``variable_name`` holds an entered value (see ``input_periods``)
    for ``period`` or an earlier period, so that the value the model reads for
    ``period`` is entered data (carried forward if earlier), not a default."""
    return any(
        input_period.start <= period.start
        for input_period in input_periods(simulation, variable_name)
    )
