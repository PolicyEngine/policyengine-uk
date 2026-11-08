"""Install protected draw storage and check its input records before reads."""

from policyengine_core.data_storage import InMemoryStorage
from policyengine_core.data_storage.store_history import _period_from_storage_key

from policyengine_uk.utils.data_source import built_from_data
from policyengine_uk.utils.protected_storage import ProtectedMemoryStorage
from policyengine_uk.utils.stored_draws import REGISTERED_DRAW_NAMES, StoredDrawError


def protects_draws(simulation) -> bool:
    """Whether the current population attachment installed draw protection."""
    return bool(getattr(simulation, "_stored_draws_protected", False))


def install_draw_storage(simulation) -> None:
    """Snapshot registered holders before a data loader supplies its values."""
    protected = built_from_data(simulation)
    simulation._stored_draws_protected = protected
    for name in REGISTERED_DRAW_NAMES:
        if name not in simulation.tax_benefit_system.variables:
            continue
        if protected:
            holder = simulation.get_holder(name)
        else:
            entity = simulation.tax_benefit_system.variables[name].entity.key
            holder = simulation.populations[entity]._holders.get(name)
            if holder is None:
                continue
        storage = holder._memory_storage
        if protected:
            if not isinstance(storage, ProtectedMemoryStorage):
                holder._memory_storage = ProtectedMemoryStorage.from_storage(
                    storage, name
                )
        elif isinstance(storage, ProtectedMemoryStorage):
            # A situation owns ordinary writeable values, including adopted inputs.
            state = storage.__getstate__()
            state.pop("_array_dtypes", None)
            state.pop("variable_name", None)
            state["_arrays"] = {
                key: values.copy() for key, values in state["_arrays"].items()
            }
            plain = InMemoryStorage(storage.is_eternal)
            plain.__setstate__(state)
            holder._memory_storage = plain


def check_draw_storage(simulation, holder, name: str) -> None:
    """Require protected memory and matching provenance for every visible mark."""
    storage = holder._memory_storage
    if not isinstance(storage, ProtectedMemoryStorage):
        raise StoredDrawError(f"{name} needs protected memory storage for every read.")
    visible = set(simulation._get_visible_branch_names())
    recorded = getattr(simulation, "_user_input_keys", None)
    for storage_key in storage._inputs:
        if storage_key not in storage._arrays:
            continue
        branch_name, period_string = storage_key.split(":", 1)
        if branch_name not in visible:
            continue
        stored_period = _period_from_storage_key(period_string)
        stored_period = holder._storage_period(stored_period)
        key = (name, branch_name, stored_period)
        description = f"{name} for {stored_period} on branch {branch_name!r}"
        if recorded is None or key not in recorded:
            raise StoredDrawError(
                f"Protected storage holds {description} as an input, but the "
                "simulation's input record does not name it as a supplied input."
            )
        # Core seeds register-only inputs before testing their storage locations.
        holder._seed_input_storage(stored_period, branch_name)
        location = getattr(holder, "_user_input_storage", {}).get(
            (branch_name, str(stored_period))
        )
        if (
            location is None
            or location[0] != stored_period
            or "memory" not in location[1]
            or not holder._stores_user_input(stored_period, branch_name, "memory")
        ):
            raise StoredDrawError(
                f"Protected storage holds {description} as an input, but the "
                "holder's location record does not name it as a supplied input "
                "in memory."
            )
