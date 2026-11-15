"""Checks the policyengine-core ``Dataset`` route makes before it exports.

``Simulation.build_from_dataset`` stores each variable of a core ``Dataset``
through ``set_input``, which casts identifiers to int32, exports the
simulation at the dataset's first period with
``UKSingleYearDataset.from_simulation`` and rebuilds from that export. Two
things a stored draw or decision needs can be lost on the way:

* Identities. The rebuild declares benefit units and households in sorted
  order of the cast identifiers, and a stored decision keyed on a raw
  identifier no longer matches one keyed on the cast identifier. So a dataset
  carrying a stored column must give identifiers that survive the int32 cast,
  for people, benefit units and households.
* Periods. Only the first period is exported. A column supplied only for
  later periods would be exported as its default and then stored as a
  supplied input. So a stored column, or an outcome that exempts a draw, that
  the dataset supplies for any period must be supplied for the first; and a
  draw's later periods must repeat the first, since only the first is kept.
"""

import warnings

import numpy as np
from policyengine_core.periods import period as period_

# Stored columns the data build writes: the UC deduction draws, the
# birthday position, the Warm Home Discount draw, the UC new-claimant draw,
# the student loan decision and the PIP phase-in draw.
STORED_COLUMNS = (
    "uc_deduction_random_draw",
    "uc_deduction_type_random_draw",
    "months_since_last_birthday",
    "warm_home_discount_random_draw",
    "uc_new_claimant_health_element_draw",
    "would_claim_student_loan",
    "pip_phase_in_draw",
)
# Draws, whose later periods must repeat the first.
DRAW_COLUMNS = (
    "uc_deduction_random_draw",
    "uc_deduction_type_random_draw",
    "warm_home_discount_random_draw",
    "uc_new_claimant_health_element_draw",
    "pip_phase_in_draw",
    "attends_private_school_random_draw",
)
# Columns that must be supplied for the first period if supplied at all: the
# stored columns, the private school draw, and the outcomes that exempt a
# draw.
FIRST_PERIOD_COLUMNS = STORED_COLUMNS + (
    "attends_private_school_random_draw",
    "uc_receives_new_claimant_health_element",
    "attends_private_school",
)
# The identifier arrays of each entity: its own and its members' memberships.
ENTITY_IDENTIFIERS = {
    "person": ("person_id",),
    "benunit": ("benunit_id", "person_benunit_id"),
    "household": ("household_id", "person_household_id"),
}


class CoreRouteError(ValueError):
    """A core ``Dataset`` that the export and rebuild would change."""


def _fails_int32_cast(ids) -> np.ndarray:
    """Which identifiers change when cast to int32."""
    values = np.asarray(ids)
    if values.dtype.kind == "O":
        try:
            values = np.array(values.tolist(), dtype=np.float64)
        except (TypeError, ValueError):
            return np.ones(values.shape, dtype=bool)
    if values.dtype.kind not in "iub":
        values = values.astype(np.float64)
        finite = np.isfinite(values)
        safe = np.where(finite, values, 0.0)
        in_range = (safe >= np.iinfo(np.int32).min) & (safe <= np.iinfo(np.int32).max)
        return ~(finite & in_range & (safe == np.trunc(safe)))
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return values.astype(np.int32).astype(values.dtype) != values


def check_identifiers(data: dict) -> None:
    """Refuse a dataset carrying a stored column whose identifiers do not
    survive the int32 cast, naming the entity and the identifiers."""
    carried = [column for column in STORED_COLUMNS if column in data]
    if not carried:
        return
    for entity, columns in ENTITY_IDENTIFIERS.items():
        failing = []
        for column in columns:
            for values in (data.get(column) or {}).values():
                values = np.asarray(values)
                bad = _fails_int32_cast(values)
                failing.extend(values[bad].reshape(-1).tolist())
        if failing:
            unique = list(dict.fromkeys(failing))
            raise CoreRouteError(
                f"This core Dataset carries {', '.join(carried)}, and "
                f"{len(unique)} {entity} identifier(s) do not survive the "
                f"int32 cast its route stores identifiers with (the first: "
                f"{unique[:5]}). The rebuild would key or order the stored "
                "values on other identifiers. Renumber the identifiers within "
                "the int32 range, or load the data as a UKSingleYearDataset."
            )


def check_supplied_periods(
    data: dict, system, first_time_period, group_orders: dict
) -> None:
    """Refuse a dataset whose stored columns the first-period export would
    change, naming the column and its periods."""
    first = str(period_(first_time_period))
    for column in FIRST_PERIOD_COLUMNS:
        if column not in data or column not in system.variables:
            continue
        by_period = data[column]
        if not len(by_period):
            continue
        supplied = {str(period_(key)): key for key in by_period}
        if first not in supplied:
            raise CoreRouteError(
                f"This core Dataset supplies {column} for "
                f"{', '.join(sorted(supplied))} but not for {first}, the only "
                "period its route exports. The export would store the "
                "variable's default as a supplied value."
            )
        if column not in DRAW_COLUMNS or len(supplied) == 1:
            continue
        variable = system.variables[column]
        orders = group_orders.get(variable.entity.key)

        def aligned(key):
            values = np.asarray(by_period[key])
            if orders is not None and values.ndim > 0:
                values = values[orders.get(key, orders[supplied[first]])]
            return values.astype(variable.dtype)

        first_values = aligned(supplied[first])
        differing = [
            name
            for name, key in supplied.items()
            if name != first and not np.array_equal(aligned(key), first_values)
        ]
        if differing:
            raise CoreRouteError(
                f"This core Dataset supplies {column} for {', '.join(sorted(supplied))} "
                f"with values in {', '.join(sorted(differing))} that differ "
                f"from {first}'s. Its route keeps only {first}, so a draw "
                "must not change between periods."
            )
