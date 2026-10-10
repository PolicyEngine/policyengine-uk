"""Values supplied as inputs, as distinct from values the engine fills in.

The engine stores more than the inputs it is given. An input variable that is
not set for a period may inherit a previously known value
(``auto_carry_over_input_variables``), and calculated values are cached next to
inputs. A holder's known periods include both. policyengine-core records each
(variable, branch, period) that ``set_input`` fills in
``Simulation._user_input_keys``. UK simulations isolate this provenance on
cloning and remove keys when deleting arrays; the helpers also require a
stored value, so missing arrays do not count as supplied inputs.

``Holder.delete_arrays`` removes a stored value without removing its record
(policyengine-core#559). The engine could then carry an earlier value into the
empty period, and the stale record would pass it off as supplied. So
``Simulation.calculate`` forgets the records of a variable in
``SUPPLIED_INPUT_VARIABLES`` whose stored value is gone before the engine can
refill it, and the helpers only answer for those variables.
"""

from typing import List, Optional

import numpy as np
from policyengine_core.periods import Period


# Variables that formulas ask about through the helpers below.
SUPPLIED_INPUT_VARIABLES = frozenset(
    {
        "bus_fare_spending",
        "bus_in_london_trips",
        "other_local_bus_trips",
        "local_bus_trips",
        "ni_class_4_losses_brought_forward",
        "ni_class_4_trading_loss",
        "trading_loss",
        "uc_carer_element",
        "uc_LCWRA_element",
    }
)


def _check_registered(variable_name: str) -> None:
    if variable_name not in SUPPLIED_INPUT_VARIABLES:
        raise ValueError(
            f"{variable_name} is not in SUPPLIED_INPUT_VARIABLES, so "
            "Simulation.calculate does not keep its input records in step "
            "with storage. Add it there before asking whether it was supplied."
        )


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


def drop_missing_supplied_inputs(simulation, variable_name: str) -> None:
    """Forget each record of ``variable_name`` as an input, on this branch
    or one it was made from, whose stored value has been deleted."""
    input_keys = getattr(simulation, "_user_input_keys", None)
    if not input_keys:
        return
    branch_names = set(_visible_branch_names(simulation))
    holder = simulation.get_holder(variable_name)
    input_keys.difference_update(
        {
            (name, branch_name, period)
            for name, branch_name, period in input_keys
            if name == variable_name
            and branch_name in branch_names
            and holder._get_array_from_storage(period, branch_name) is None
        }
    )


def supplied_input_periods(population, variable_name: str) -> List[Period]:
    """Periods for which ``variable_name`` was supplied as an input, on this
    branch or one it was made from, earliest first."""
    _check_registered(variable_name)
    simulation = population.simulation
    branch_names = set(_visible_branch_names(simulation))
    input_keys = getattr(simulation, "_user_input_keys", None) or ()
    holder = population.get_holder(variable_name)
    return sorted(
        {
            period
            for name, branch_name, period in input_keys
            if name == variable_name
            and branch_name in branch_names
            and holder._get_array_from_storage(period, branch_name) is not None
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
    _check_registered(variable_name)
    simulation = population.simulation
    input_keys = getattr(simulation, "_user_input_keys", None) or ()
    holder = population.get_holder(variable_name)
    for branch_name in _visible_branch_names(simulation):
        if (variable_name, branch_name, period) in input_keys:
            # Read the stored input itself: Holder.get_array would fall back
            # to other branches' values, including cached calculations.
            # Holder.delete_arrays leaves provenance keys behind; a missing
            # stored array must be ignored even if its key remains.
            value = holder._get_array_from_storage(period, branch_name)
            if value is not None:
                # A neutralized variable reads as its default, as it does
                # through the engine. (PolicyEngine-UK builds no
                # gov.abolitions parameters, so there is no abolition switch
                # to honour here.)
                variable = simulation.tax_benefit_system.get_variable(variable_name)
                if variable.is_neutralized:
                    return holder.default_array()
                return value
    return None
