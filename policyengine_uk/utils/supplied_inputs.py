"""Values supplied as inputs, as distinct from values the engine fills in.

The engine stores more than the inputs it is given. An input variable that is
not set for a period may inherit a previously known value
(``auto_carry_over_input_variables``), and calculated values are cached next to
inputs. A holder's known periods include both. policyengine-core records each
(variable, branch, period) that ``set_input`` fills in
``Simulation._user_input_keys``, and nothing else adds to it, so it is
independent of what has been calculated before.
"""

from typing import List, Optional

import numpy as np
from policyengine_core.errors import ParameterNotFoundError
from policyengine_core.periods import Period


def _visible_branch_names(simulation) -> List[str]:
    """This branch, then the branches it was made from, then the default."""
    names = []
    branch = simulation
    while branch is not None:
        names.append(branch.branch_name)
        branch = getattr(branch, "parent_branch", None)
    if "default" not in names:
        names.append("default")
    return names


def supplied_input_periods(population, variable_name: str) -> List[Period]:
    """Periods for which ``variable_name`` was supplied as an input, on this
    branch or one it was made from, earliest first."""
    simulation = population.simulation
    branch_names = set(_visible_branch_names(simulation))
    input_keys = getattr(simulation, "_user_input_keys", None) or ()
    return sorted(
        {
            period
            for name, branch_name, period in input_keys
            if name == variable_name and branch_name in branch_names
        },
        key=lambda period: period.start,
    )


def supplied_input(
    population, variable_name: str, period: Period
) -> Optional[np.ndarray]:
    """The value of ``variable_name`` for ``period`` if it was supplied as an
    input, on this branch or the nearest one it was made from; otherwise
    None. A value the engine carried over from an earlier period, or cached
    after a calculation, is not an input."""
    simulation = population.simulation
    input_keys = getattr(simulation, "_user_input_keys", None) or ()
    holder = population.get_holder(variable_name)
    for branch_name in _visible_branch_names(simulation):
        if (variable_name, branch_name, period) in input_keys:
            # Read the stored input itself: Holder.get_array would fall back
            # to other branches' values, including cached calculations.
            value = holder._get_array_from_storage(period, branch_name)
            if value is not None:
                # Preserve the engine's reform handling while reading the
                # supplied value rather than a branch's calculated cache.
                system = simulation.tax_benefit_system
                disabled = system.get_variable(variable_name).is_neutralized
                try:
                    disabled = (
                        disabled
                        or system.parameters(period).gov.abolitions[variable_name]
                    )
                except (ParameterNotFoundError, KeyError):
                    # Input variables have no generated abolition parameter.
                    pass
                if disabled:
                    return holder.default_array()
                return value
    return None
