"""Entity identifiers a simulation can store exactly.

A simulation built from data keeps each identifier column in two places. The
populations hold the entity structure (``ids`` and ``members_entity_id``),
taken from the arrays ``build_from_ids`` is given. The variables in
``ENTITY_ID_VARIABLES`` hold the same identifiers as stored values, and those
are what ``calculate``, ``to_input_dataframe`` and
``UKSingleYearDataset.from_simulation`` return. ``Simulation.build_from_dataset``
rebuilds the entities from that last export.

policyengine-core casts a stored value to its variable's dtype with ``astype``
(``Holder._to_array``). That cast wraps an integer outside the dtype's range
and drops the fraction of a float, both without an error. ``check_entity_ids``
warns about such identifiers when the entities are built. It does not refuse
them: the populations built from them still hold them exactly, and data builds
that number clones past the range (by adding multiples of a power of ten to
every identifier) load them today.
"""

import warnings

import numpy as np
from policyengine_core.variables import Variable

# The variables that store the identifier columns ``build_from_ids`` takes, in
# the order it takes them.
ENTITY_ID_VARIABLES = (
    "person_id",
    "person_benunit_id",
    "person_household_id",
    "benunit_id",
    "household_id",
)


class EntityIdWarning(UserWarning):
    """An identifier changes when the simulation stores it."""


def check_entity_ids(variable: Variable, values) -> bool:
    """Warn if ``variable`` cannot store ``values`` exactly.

    Only integer and float arrays are checked against an integer variable.
    policyengine-core reports any other mismatch when it stores the values.

    Args:
        variable: The variable that will store the identifiers.
        values: The identifiers, one per record.

    Returns:
        Whether every value is stored exactly. A ``False`` result comes with
        an ``EntityIdWarning``.
    """
    values = np.asarray(values)
    if values.size == 0 or values.dtype.kind not in "iuf":
        return True
    if not np.issubdtype(variable.dtype, np.integer):
        return True
    if values.dtype.kind == "f":
        whole = np.isfinite(values) & (values == np.trunc(values))
        if not whole.all():
            warnings.warn(
                f"{variable.name} should hold whole numbers, but "
                f"{int((~whole).sum())} of its {values.size} values do not (the "
                f"first is {values[~whole][0]}). The simulation stores them "
                f"as {np.dtype(variable.dtype).name}, so the {variable.name} "
                "values it returns will differ from them.",
                EntityIdWarning,
                stacklevel=3,
            )
            return False
    # Python integers compare exactly. A float32 or unsigned 64-bit bound does
    # not compare exactly with a NumPy integer limit.
    lowest, highest = int(values.min()), int(values.max())
    limits = np.iinfo(variable.dtype)
    if lowest < limits.min or highest > limits.max:
        warnings.warn(
            f"{variable.name} ranges from {lowest} to {highest}, but the "
            f"simulation stores it as {np.dtype(variable.dtype).name}, which "
            f"holds whole numbers from {limits.min} to {limits.max}. The "
            f"{variable.name} values it returns will differ from the ones "
            "given, and so may anything rebuilt from them. Renumber the "
            "identifiers to fit that range.",
            EntityIdWarning,
            stacklevel=3,
        )
        return False
    return True
