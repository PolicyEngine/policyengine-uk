"""Hand-built households and helpers for the stored-draw tests."""

import numpy as np
import pandas as pd

F64 = np.float64
F32 = np.float32

ID_COLUMNS = (
    "person_id",
    "person_benunit_id",
    "person_household_id",
    "benunit_id",
    "household_id",
)


def one_person_units_frame(count=3, years=(2025,), columns=None, ids=None):
    """A frame of ``count`` adults, each alone in a benefit unit and a
    household, with identifiers and ``columns`` (name -> array, or a dict of
    year -> array) in each year."""
    ids = np.arange(1, count + 1) if ids is None else np.asarray(ids)
    data = {}
    for year in years:
        for variable in ID_COLUMNS:
            data[f"{variable}__{year}"] = ids
        data[f"age__{year}"] = np.full(count, 30)
        data[f"household_weight__{year}"] = np.ones(count)
    for name, values in (columns or {}).items():
        by_year = values if isinstance(values, dict) else {years[0]: values}
        for year, array in by_year.items():
            data[f"{name}__{year}"] = array
    return pd.DataFrame(data)


def encode(x, thresholds):
    """The plan's reference encoder for decision-preserving float32 draws
    (tools/encode_float32_draws.py), copied for the tests: returns (y,
    feasible, adjusted) for legacy float64 draws x and covered thresholds."""
    x = np.asarray(x, dtype=F64)
    t = np.unique(np.asarray(thresholds, dtype=F64))
    n_le = np.searchsorted(t, x, side="right")  # thresholds <= x
    lo = np.where(n_le > 0, t[np.maximum(n_le - 1, 0)], 0.0)
    hi = np.where(n_le < len(t), t[np.minimum(n_le, len(t) - 1)], 1.0)
    lo = np.maximum(lo, 0.0)
    hi = np.minimum(hi, 1.0)

    y = x.astype(F32)
    yd = y.astype(F64)
    ok = (yd >= lo) & (yd < hi)

    up = lo.astype(F32)
    up = np.where(up.astype(F64) < lo, np.nextafter(up, F32(np.inf)), up)
    down = hi.astype(F32)
    down = np.where(down.astype(F64) >= hi, np.nextafter(down, F32(-np.inf)), down)

    y = np.where(ok, y, np.where(yd < lo, up, down)).astype(F32)
    yd = y.astype(F64)
    feasible = (yd >= lo) & (yd < hi)
    return y, feasible, ~ok


# Thresholds the consumers compare stored draws with.
PIP_THRESHOLDS = [0.25 * (year - 2025) / 4 for year in range(2025, 2030)]
SHARE_GRID = sorted({float(f"{k / 100:.2f}") for k in range(0, 101)})
