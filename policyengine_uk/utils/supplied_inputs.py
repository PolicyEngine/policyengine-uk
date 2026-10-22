"""Values supplied as inputs, as distinct from values the engine fills in.

The engine stores more than the inputs it is given. An input variable that is
not set for a period may inherit a previously known value
(``auto_carry_over_input_variables``), and calculated values are cached next to
inputs. A holder's known periods include both. policyengine-core records each
(variable, branch, period) that ``set_input`` stores in
``Simulation._user_input_keys``. From 3.32.27 (policyengine-core#561), core
forgets the record of an input that ``Holder.delete_arrays`` deletes, and each
clone gets its own copy of the record. The helpers also require a stored
value, so missing arrays do not count as supplied inputs.

``build_from_situation`` installs fresh populations, and so fresh holders,
through ``Simulation.build_from_populations``, which keeps the record
(policyengine-core#605). The engine could then carry an earlier value into a
period whose input the rebuild dropped, and the stale record would pass it off
as supplied. So ``Simulation.calculate`` forgets the records of a variable in
``SUPPLIED_INPUT_VARIABLES`` whose stored value is gone before the engine can
refill it, and the helpers only answer for those variables.
``Simulation.delete_arrays`` forgets such records too, for any variable it
deletes.

A scenario that stores a value the model calculated (``set_model_value``)
records it as the model's, and the helpers do not return it. The record of
such a value lasts only while it is the value stored: ``Simulation`` forgets
it when ``set_input`` stores a value for its period, whatever the value (an
input set for a longer or shorter period that stores nothing there leaves
it), when ``delete_arrays`` removes it, and when the populations are
rebuilt, and a clone or branch gets its own copy of the record.

``supplied_input_arrays`` answers for every variable. It reads only a record
whose supplied value is still stored, from the storage tier (memory or disk)
the holder records it in. A value the engine carried over or calculated into
the same period, in either tier, is not read as supplied. It includes values
``set_model_value`` stored, which ``is_model_value`` tells apart.
"""

from typing import List, Optional, Tuple

import numpy as np
from policyengine_core import periods
from policyengine_core.periods import Period


# Variables that formulas ask about through the helpers below.
SUPPLIED_INPUT_VARIABLES = frozenset(
    {
        "adjusted_net_income",
        "bus_fare_spending",
        "bus_in_london_trips",
        "other_local_bus_trips",
        "pip_dl_category",
        "pip_dl_points",
        "pip_m_category",
        "pip_m_points",
        "local_bus_trips",
        "local_bus_uncapped_single_fare",
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
    or one it was made from, whose stored value is gone."""
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
            and not _is_model_value(
                simulation,
                (name, branch_name, period),
                holder._get_array_from_storage(period, branch_name),
            )
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
            # A record can outlive its stored array (see above); a missing
            # stored array must be ignored even if its key remains.
            value = holder._get_array_from_storage(period, branch_name)
            if value is not None:
                # A value the model stored itself (set_model_value) is not
                # supplied, though the engine keeps it like an input.
                if _is_model_value(
                    simulation, (variable_name, branch_name, period), value
                ):
                    return None
                # A neutralized variable reads as its default, as it does
                # through the engine. (PolicyEngine-UK builds no
                # gov.abolitions parameters, so there is no abolition switch
                # to honour here.)
                variable = simulation.tax_benefit_system.get_variable(variable_name)
                if variable.is_neutralized:
                    return holder.default_array()
                return value
    return None


def supplied_input_arrays(simulation) -> List[Tuple[str, Period, np.ndarray]]:
    """Every value ``simulation`` was given as an input and still stores, on
    its own branch, with its variable and the period it is stored for.

    Ordered by variable and period, so that the same simulation always gives
    the same list.
    """
    input_keys = getattr(simulation, "_user_input_keys", None) or ()
    arrays = []
    for variable_name, branch_name, period in input_keys:
        if branch_name != simulation.branch_name:
            continue
        value = stored_supplied_value(
            simulation.get_holder(variable_name), period, branch_name
        )
        if value is not None:
            arrays.append((variable_name, period, value))
    return sorted(arrays, key=lambda item: (item[0], item[1].start, str(item[1])))


def stored_supplied_value(holder, period: Period, branch_name: str):
    """The supplied value ``holder`` still stores for ``period``, or None.

    A record can outlive its stored value (see above), and a value calculated
    later can take its place in one tier while the input survives in the
    other. So read only a tier that the holder records the input in (either
    tier when it records none) and that holds a value it did not calculate,
    as ``Holder._stores_user_input`` decides whether an input survives.
    Reading memory before disk instead could return a calculated value cached
    over an input stored on disk.
    """
    recorded = (getattr(holder, "_user_input_storage", None) or {}).get(
        (branch_name, str(period))
    )
    locations = recorded[1] if recorded is not None else {"memory", "disk"}
    for location, storage in (
        ("memory", holder._memory_storage),
        ("disk", holder._disk_storage),
    ):
        if (
            location in locations
            and storage is not None
            and storage.has(period, branch_name)
            and not storage.is_derived(period, branch_name)
        ):
            return storage.get(period, branch_name)
    return None


def _is_model_value(simulation, key, value) -> bool:
    model_values = getattr(simulation, "_model_values", None) or {}
    written = model_values.get(key)
    return written is not None and np.array_equal(written, value)


def is_model_value(simulation, variable_name: str, period: Period, value) -> bool:
    """Whether ``value``, stored for ``variable_name`` and ``period`` on this
    simulation's branch, is the model's own value (``set_model_value``)
    rather than a supplied one."""
    return _is_model_value(
        simulation, (variable_name, simulation.branch_name, period), value
    )


def set_model_value(simulation, variable_name: str, period, value) -> None:
    """Store ``value`` for ``variable_name`` and ``period`` with ``set_input``,
    as the model's own value rather than a supplied one, unless the period's
    value was supplied already.

    ``set_input`` records the value as an input, and the engine keeps
    recorded inputs when a reform is applied, so a scenario that adjusts a
    calculated amount must store it that way. ``supplied_input`` and
    ``supplied_input_periods`` do not return the stored value while it is
    the one stored here. A later ``Simulation.set_input`` for the period is
    supplied, whatever its value, and so is any value stored after
    ``delete_arrays`` removes this one or the populations are rebuilt (see
    ``forget_replaced_model_values``, ``drop_missing_model_values`` and
    ``forget_model_values``). If the value was supplied before (a scenario
    adjusting a user's entry), the new value stays supplied."""
    _check_registered(variable_name)
    period = periods.period(period)
    population = simulation.get_variable_population(variable_name)
    already_supplied = supplied_input(population, variable_name, period) is not None
    simulation.set_input(variable_name, period, value)
    if already_supplied:
        return
    branch_name = simulation.branch_name
    stored = population.get_holder(variable_name)._get_array_from_storage(
        period, branch_name
    )
    if stored is not None:
        model_values = getattr(simulation, "_model_values", None)
        if model_values is None:
            model_values = {}
            simulation._model_values = model_values
        model_values[(variable_name, branch_name, period)] = np.array(stored)


# ``Simulation`` keeps the record of model values in step with what it stores
# through the helpers below. Each simulation, clone or branch has its own
# record, as core gives each its own record of inputs.


def model_value_input_records(simulation, variable_name: str) -> dict:
    """For each model value of ``variable_name`` on this branch, the entry
    policyengine-core keeps for the input stored for its period, to pass to
    ``forget_replaced_model_values`` after a ``set_input``.

    Core replaces a period's entry (``Holder._user_input_storage``) each time
    it stores an input there, even an equal value, so a changed entry shows
    the call stored one."""
    model_values = getattr(simulation, "_model_values", None)
    if not model_values:
        return {}
    keys = [
        key
        for key in model_values
        if key[0] == variable_name and key[1] == simulation.branch_name
    ]
    if not keys:
        return {}
    holder = simulation.get_holder(variable_name)
    records = getattr(holder, "_user_input_storage", None) or {}
    return {key: records.get(_input_slot(holder, key)) for key in keys}


def forget_replaced_model_values(simulation, variable_name: str, before) -> None:
    """Forget each model value whose period a ``set_input`` stored a value
    for since ``before`` (``model_value_input_records``) was taken: a value
    set there is supplied, even one equal to the model's.

    An input set for another period can leave the model value in place, and
    then it stays the model's. Core stores an input for a longer period of
    the variable's own unit (such as ``year:2026:2``) under that period,
    which a calculation for one year does not read. For a period of another
    unit, ``set_input_divide_by_period`` and ``set_input_dispatch_by_period``
    store only in years that hold no input, so an input for part of a year,
    or for twelve months, stores nothing in a year that holds a model value
    (``set_input_divide_by_period`` raises an error if it is inconsistent
    with that value)."""
    if not before:
        return
    holder = simulation.get_holder(variable_name)
    records = getattr(holder, "_user_input_storage", None) or {}
    model_values = simulation._model_values
    for key, record in before.items():
        if records.get(_input_slot(holder, key)) is not record:
            model_values.pop(key, None)


def _input_slot(holder, key):
    """The key of core's entry for the input stored for a model value."""
    _, branch_name, period = key
    return (branch_name, str(holder._storage_period(period)))


def drop_missing_model_values(simulation, variable_name: str) -> None:
    """Forget each model value of ``variable_name``, on this branch or one it
    was made from, whose stored value is gone, so that a value stored there
    later is supplied, even one equal to the model's."""
    model_values = getattr(simulation, "_model_values", None)
    if not model_values:
        return
    branch_names = set(_visible_branch_names(simulation))
    holder = simulation.get_holder(variable_name)
    for key in [
        key
        for key in model_values
        if key[0] == variable_name
        and key[1] in branch_names
        and holder._get_array_from_storage(key[2], key[1]) is None
    ]:
        del model_values[key]


def forget_model_values(simulation) -> None:
    """Forget every model value: rebuilt populations hold none of them."""
    if getattr(simulation, "_model_values", None):
        simulation._model_values = {}


def copy_model_values(simulation, clone) -> None:
    """Give a clone of ``simulation`` its own copy of the record, so that what
    either stores later does not change what the other reads as supplied."""
    model_values = getattr(simulation, "_model_values", None)
    if model_values is not None:
        clone._model_values = dict(model_values)
