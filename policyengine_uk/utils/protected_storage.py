"""Memory storage that keeps stored draws over immutable bytes."""

import numpy as np
from policyengine_core import periods
from policyengine_core.data_storage import InMemoryStorage
from policyengine_core.data_storage.store_history import _period_from_storage_key

from policyengine_uk.utils.stored_draws import (
    StoredDrawError,
    calculation_in_flight,
)


class ProtectedMemoryStorage(InMemoryStorage):
    """Keep numeric values immutable and refuse input changes during a calculation."""

    def __init__(self, is_eternal: bool, variable_name: str):
        super().__init__(is_eternal)
        self.variable_name = variable_name
        self._inputs = frozenset()

    def _immutable_array(self, value):
        if type(value) is not np.ndarray:
            raise StoredDrawError(
                f"{self.variable_name} needs a plain numeric numpy.ndarray; "
                f"{type(value).__name__} cannot supply protected storage."
            )
        if value.dtype.kind not in "biufc":
            raise StoredDrawError(
                f"{self.variable_name} needs a numeric dtype; "
                f"{value.dtype} cannot supply protected storage."
            )
        result = np.frombuffer(value.tobytes(), dtype=value.dtype)
        if result.shape != value.shape:
            result.shape = value.shape
        return result

    @staticmethod
    def _new_array(value):
        result = np.frombuffer(value.base, dtype=value.dtype)
        if result.shape != value.shape:
            result.shape = value.shape
        return result

    def _key(self, period, branch_name):
        if self.is_eternal:
            period = periods.period(periods.ETERNITY)
        return f"{branch_name}:{periods.period(period)}"

    def _refuse(self, action, period, branch_name):
        raise StoredDrawError(
            f"Cannot {action} {self.variable_name} for {period} "
            f"on branch {branch_name!r} during a calculation."
        )

    def put(
        self,
        value,
        period,
        branch_name="default",
        derived=False,
        sequence_number=None,
    ):
        if not derived and calculation_in_flight():
            self._refuse("store an input of", period, branch_name)
        key = self._key(period, branch_name)
        if derived and key in self._arrays and key in self._inputs:
            raise StoredDrawError(
                f"Cannot store a derived value of {self.variable_name} for "
                f"{period} on branch {branch_name!r} over a stored input."
            )
        value = self._immutable_array(value)
        inputs = self._inputs
        if derived and key not in self._arrays:
            self._inputs = inputs - {key}
        try:
            super().put(
                value,
                period,
                branch_name,
                derived=derived,
                sequence_number=sequence_number,
            )
        except Exception:
            self._inputs = inputs
            raise

    def get(self, period, branch_name="default"):
        value = self._arrays.get(self._key(period, branch_name))
        return None if value is None else self._new_array(value)

    def delete(self, period=None, branch_name="default"):
        prefix = f"{branch_name}:"
        if period is not None:
            period = periods.period(periods.ETERNITY if self.is_eternal else period)
        selected = {
            key
            for key in self._arrays
            if key.startswith(prefix)
            and (
                period is None
                or period.contains(_period_from_storage_key(key.split(":", 1)[1]))
            )
        }
        selected_inputs = selected.intersection(self._inputs)
        if calculation_in_flight() and selected_inputs:
            stored_branch, stored_period = next(iter(selected_inputs)).split(":", 1)
            self._refuse("delete an input of", stored_period, stored_branch)
        super().delete(period, branch_name)

    def _mark_input(self, key):
        self._inputs = self._inputs | {key}

    def _unmark_input(self, key):
        if calculation_in_flight() and key in self._inputs and key in self._arrays:
            branch_name, period = key.split(":", 1)
            self._refuse("demote an input of", period, branch_name)
        self._inputs = self._inputs - {key}

    def _unmark_dropped_keys(self):
        self._inputs = self._inputs.intersection(self._arrays)

    def mark_derived_except(self, keys):
        keys = frozenset(keys)
        demoted = self._inputs.difference(keys)
        if calculation_in_flight() and demoted.intersection(self._arrays):
            key = next(iter(demoted.intersection(self._arrays)))
            branch_name, period = key.split(":", 1)
            self._refuse("demote an input of", period, branch_name)
        self._inputs = self._inputs.intersection(keys)

    def clone(self, share_arrays=False):
        """Copy the indices and share only immutable arrays and input marks."""
        result = type(self)(self.is_eternal, self.variable_name)
        result._arrays = self._arrays.copy()
        result._inputs = self._inputs.intersection(result._arrays)
        result._sequence_numbers = self._sequence_numbers.copy()
        return result

    @classmethod
    def from_storage(cls, storage, variable_name):
        """Copy a storage's values, input marks and sequence numbers."""
        result = cls(storage.is_eternal, variable_name)
        state = storage.__getstate__()
        state["variable_name"] = variable_name
        result.__setstate__(state)
        return result

    def __getstate__(self):
        state = super().__getstate__()
        state["_arrays"] = {
            key: self._new_array(value) for key, value in self._arrays.items()
        }
        state["_inputs"] = frozenset(self._inputs)
        state["_sequence_numbers"] = self._sequence_numbers.copy()
        state["_array_dtypes"] = {
            key: value.dtype.str for key, value in self._arrays.items()
        }
        state.pop("_shared", None)
        return state

    def __setstate__(self, state):
        state = state.copy()
        dtypes = state.pop("_array_dtypes", {})
        super().__setstate__(state)
        arrays = {}
        for key, value in self._arrays.items():
            dtype = np.dtype(dtypes.get(key, value.dtype))
            if value.dtype != dtype:
                # NumPy's standard pickler restores numeric arrays in native byte order.
                value = value.byteswap().view(dtype)
            arrays[key] = self._immutable_array(value)
        self._arrays = arrays
        self._inputs = frozenset(self._inputs)
        self._sequence_numbers = self._sequence_numbers.copy()
        self.__dict__.pop("_shared", None)
