"""Steps for marginal rates measured by finite differences.

A marginal rate here adds a step to an input, recomputes household net income
and divides the change by the step. Both the input and net income are stored
as float32, whose spacing doubles with each power of two: £2 between £16.8m
and £33.6m, £32 between £268m and £537m. A fixed £1,000 step is then partly
rounding at the largest gains and earnings, in the input and in the change
in net income alike (issue #1979).
"""

import numpy as np

from policyengine_uk.utils.inputs import variables_with_input

# Float32 rounds a value by at most 2^-24 of itself, so a step of 0.1% of the
# value keeps each rounding below 6e-5 of the step at any size.
RELATIVE_STEP = 1e-3


def marginal_rate_step(values, minimum: float) -> np.ndarray:
    """The step to add to each value: the minimum, or 0.1% of the value if larger.

    Below minimum / RELATIVE_STEP (£1m for a £1,000 minimum) the step is the
    minimum. Above it the reading is the average rate over the larger step,
    so a rate change inside the step, such as gains relief reaching its
    lifetime limit, is blended into the reading rather than seen as a kink.

    Callers divide by the step as stored, the stored input after the step
    less the stored input before it: float32 rounds the sum, so the step
    stored is not exactly the step asked for.
    """
    values = np.abs(np.asarray(values, dtype=np.float64))
    return np.maximum(minimum, RELATIVE_STEP * values)


def clear_branch_for_recalculation(simulation, branch, period) -> None:
    """Delete from ``branch`` every value that a changed input could change,
    so that the branch recalculates it for ``period``.

    Variables without a formula keep their values, and so do variables
    entered for ``period``. A variable entered only for other periods (a
    dataset column, for years past the data) keeps those entries but loses
    its value for ``period``. Every other variable loses all its values.
    Whether a variable was entered is read from the inputs, not from
    ``simulation.input_variables``, which lists every variable stored at load
    for any period: keeping such a variable's ``period`` value let the branch
    read the value this simulation had calculated before the branch existed,
    so the result depended on calculation order.
    """
    entered = variables_with_input(simulation, period)
    for name, variable in simulation.tax_benefit_system.variables.items():
        if variable.is_input_variable() or name in entered:
            continue
        if name in simulation.input_variables:
            branch.delete_arrays(name, period)
        else:
            branch.delete_arrays(name)
