"""Entity identifiers a simulation can store exactly.

A simulation built from data keeps each identifier column in two places. The
populations hold the entity structure (``ids`` and ``members_entity_id``).
The variables in ``ENTITY_ID_VARIABLES`` hold the same identifiers as stored
values, and those are what ``calculate``, ``to_input_dataframe`` and
``UKSingleYearDataset.from_simulation`` return. ``Simulation.build_from_dataset``
rebuilds the entities from that last export.

policyengine-core casts a stored value to its variable's dtype with ``astype``
(``Holder._to_array``). That cast wraps an integer outside the dtype's range and
drops the fraction of a float, both without an error. ``check_entity_ids``
refuses such identifiers when the entities are built, so that every identifier
a simulation accepts reads back exactly.
"""

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


def check_entity_ids(variable: Variable, values) -> None:
    """Raise ``ValueError`` if ``variable`` cannot store ``values`` exactly.

    Only integer and float arrays are checked against an integer variable.
    policyengine-core reports any other mismatch when it stores the values.

    Args:
        variable: The variable that will store the identifiers.
        values: The identifiers, one per record.
    """
    values = np.asarray(values)
    if values.size == 0 or values.dtype.kind not in "iuf":
        return
    if not np.issubdtype(variable.dtype, np.integer):
        return
    if values.dtype.kind == "f":
        whole = np.isfinite(values) & (values == np.trunc(values))
        if not whole.all():
            raise ValueError(
                f"{variable.name} must hold whole numbers, but "
                f"{int((~whole).sum())} of its {values.size} values are not "
                f"(the first is {values[~whole][0]})."
            )
    # Python integers compare exactly. A float32 or unsigned 64-bit bound does
    # not compare exactly with a NumPy integer limit.
    lowest, highest = int(values.min()), int(values.max())
    limits = np.iinfo(variable.dtype)
    if lowest < limits.min or highest > limits.max:
        raise ValueError(
            f"{variable.name} ranges from {lowest} to {highest}, but a "
            f"simulation stores it as {np.dtype(variable.dtype).name}, which "
            f"holds whole numbers from {limits.min} to {limits.max}. Renumber "
            "the identifiers to fit that range."
        )
