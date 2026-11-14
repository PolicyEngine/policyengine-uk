"""Export recorded inputs without treating formulas or caches as provenance."""

import pandas as pd

from policyengine_uk.utils.supplied_inputs import _is_model_value


def _legacy_recorded_array(holder, period, branch_name):
    """Read the surviving input tier on Core 3.32.27.

    Core 3.33.2 supplies ``Simulation._get_recorded_input_array``. The
    supported minimum instead exposes only the holder's combined predicate;
    mirror its recorded-location/has/not-derived checks before reading a tier.
    An ordinary holder read would let a calculated memory value hide an input
    still stored on disk.
    """
    recorded = getattr(holder, "_user_input_storage", {}).get(
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


def _recorded_array(simulation, variable, period, branch_names, input_keys):
    holder = simulation.get_holder(variable)
    for branch_name in branch_names:
        key = (variable, branch_name, period)
        if key not in input_keys or not holder._stores_user_input(period, branch_name):
            continue
        reader = getattr(simulation, "_get_recorded_input_array", None)
        values = (
            reader(variable, period)
            if reader is not None
            else _legacy_recorded_array(holder, period, branch_name)
        )
        # The Core reader and the fallback choose this same first surviving
        # branch. Match the model marker to that source, not another branch
        # whose input happens to have the same numeric value.
        if values is None or _is_model_value(simulation, key, values):
            return None
        return values
    return None


def input_dataframe(simulation):
    """Project actual supplied arrays to people, including formula overrides.

    The simulation's existing input record, storage marks and UK model-value
    markers remain authoritative. Export neither calculates nor records data.
    """
    branch_names = simulation._get_visible_branch_names()
    input_keys = getattr(simulation, "_user_input_keys", set())
    periods_by_variable = {}
    for variable, branch_name, period in input_keys:
        if branch_name in branch_names:
            periods_by_variable.setdefault(variable, set()).add(period)

    columns = {}
    for name, variable in simulation.tax_benefit_system.variables.items():
        for period in sorted(periods_by_variable.get(name, ()), key=str):
            if variable.definition_period != period.unit:
                continue
            values = _recorded_array(simulation, name, period, branch_names, input_keys)
            if values is not None:
                columns[f"{name}__{period}"] = simulation.map_result(
                    values, variable.entity.key, simulation.persons.entity.key
                )
    return pd.DataFrame(columns)
