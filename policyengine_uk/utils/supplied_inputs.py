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
"""

from typing import List, Optional

import numpy as np
from policyengine_core import periods
from policyengine_core.periods import Period


# Variables that formulas ask about through the helpers below.
SUPPLIED_INPUT_VARIABLES = frozenset(
    {
        "adjusted_net_income",
        "carers_allowance",
        "carers_allowance_pre_couple_limit",
        "carers_allowance_pre_overlap",
        "carer_support_payment",
        "carer_support_payment_pre_overlap",
        "is_entitled_to_carer_benefit",
        "receives_carer_benefit",
        "receives_carers_allowance",
        "receives_carer_support_payment",
        "bus_fare_spending",
        "bus_in_london_trips",
        "current_education",
        "early_years_term_share_before_school",
        "electricity_consumption_kwh",
        "extended_childcare_entitlement_term_share",
        "extended_childcare_entitlement_total_per_child",
        "gas_consumption_kwh",
        "in_HE",
        "other_local_bus_trips",
        "pip_dl_category",
        "pip_dl_points",
        "pip_m_category",
        "pip_m_points",
        "local_bus_trips",
        "local_bus_uncapped_single_fare",
        "monthly_domestic_energy_consumption",
        "ni_class_4_losses_brought_forward",
        "ni_class_4_trading_loss",
        "ni_epg_full_rate_applies",
        "tenure_type",
        "targeted_childcare_entitlement",
        "trading_loss",
        "uc_carer_element",
        "uc_LCWRA_element",
        "universal_childcare_entitlement",
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


def latest_supplied_input_period(
    population, variable_name: str, before: Period
) -> Optional[Period]:
    """The latest period before ``before`` for which ``variable_name`` was
    supplied as an input (see ``supplied_input_periods``), or None."""
    earlier = [
        period
        for period in supplied_input_periods(population, variable_name)
        if period.start < before.start
    ]
    return earlier[-1] if earlier else None


def supplied_by(population, variable_name: str, period: Period) -> bool:
    """Whether ``variable_name`` was supplied as an input for ``period`` or an
    earlier period, so that the value read for ``period`` is supplied data
    (carried forward from the latest earlier input if need be), not a
    default."""
    return any(
        supplied_period.start <= period.start
        for supplied_period in supplied_input_periods(population, variable_name)
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


def _is_model_value(simulation, key, value) -> bool:
    model_values = getattr(simulation, "_model_values", None) or {}
    written = model_values.get(key)
    return written is not None and np.array_equal(written, value)


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
