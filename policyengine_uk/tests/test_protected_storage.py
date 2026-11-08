"""Protected storage keeps values immutable and rejects input changes atomically."""

import pickle

import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from policyengine_core.data_storage import InMemoryStorage
from policyengine_core.periods import period

from policyengine_uk.utils.protected_storage import ProtectedMemoryStorage
from policyengine_uk.utils.stored_draws import StoredDrawError, calculation


NAME = "pip_phase_in_draw"
VALUES = np.array([0.25, 0.5, 0.75], dtype=np.float32)
OTHER = np.array([0.125, 0.375, 0.625], dtype=np.float32)


def storage():
    result = ProtectedMemoryStorage(False, NAME)
    result.put(VALUES, 2025, sequence_number=31)
    return result


def snapshot(memory):
    return (
        {
            key: (value.dtype, value.shape, value.tobytes())
            for key, value in memory._arrays.items()
        },
        memory._inputs,
        memory._sequence_numbers.copy(),
    )


def assert_immutable(value, expected):
    assert type(value) is np.ndarray
    assert isinstance(value.base, bytes)
    assert not value.flags.writeable
    assert value.dtype == expected.dtype
    assert value.shape == expected.shape
    assert value.tobytes() == expected.tobytes()
    with pytest.raises(ValueError):
        value.flags.writeable = True
    if value.size:
        with pytest.raises(ValueError):
            value.flat[0] = 0


@pytest.mark.parametrize("branch", ["default", "child", "ancestor"])
@pytest.mark.parametrize("target", [2025, 2026, 2027])
@pytest.mark.parametrize("values", [VALUES, OTHER])
def test_input_store_refuses_during_a_calculation_without_changing_storage(
    branch, target, values
):
    memory = storage()
    before = snapshot(memory)
    with calculation():
        with pytest.raises(StoredDrawError, match=f"{NAME} for {target}.*{branch}"):
            memory.put(values, target, branch)
    assert snapshot(memory) == before


@pytest.mark.parametrize("during", [False, True])
@pytest.mark.parametrize("values", [VALUES, OTHER])
def test_derived_store_never_replaces_a_stored_input(during, values):
    memory = storage()
    before = snapshot(memory)

    def attempt():
        with pytest.raises(StoredDrawError, match="over a stored input"):
            memory.put(values, 2025, derived=True)

    if during:
        with calculation():
            attempt()
    else:
        attempt()
    assert snapshot(memory) == before


def test_derived_values_can_change_during_a_calculation():
    memory = storage()
    with calculation():
        memory.put(VALUES, 2026, derived=True, sequence_number=32)
        memory.put(OTHER, 2026, derived=True, sequence_number=33)
    assert memory.is_derived(2026)
    assert_immutable(memory.get(2026), OTHER)
    assert memory._sequence_numbers["default:2026"] == 33
    assert memory._inputs == frozenset({"default:2025"})


def test_an_input_can_replace_a_derived_value_between_calculations():
    memory = storage()
    memory.put(VALUES, 2026, derived=True)
    memory.put(OTHER, 2026)
    assert not memory.is_derived(2026)
    assert_immutable(memory.get(2026), OTHER)
    assert isinstance(memory._inputs, frozenset)


@pytest.mark.parametrize("target", [None, 2025, "year:2024:3"])
def test_delete_refuses_before_removing_any_selected_value(target):
    memory = storage()
    memory.put(OTHER, 2024, derived=True)
    memory.put(OTHER, 2026, derived=True)
    before = snapshot(memory)
    with calculation():
        with pytest.raises(StoredDrawError, match=f"{NAME} for 2025.*default"):
            memory.delete(target)
    assert snapshot(memory) == before


def test_delete_and_cache_drop_keep_inputs_while_removing_only_derived_values():
    memory = storage()
    memory.put(OTHER, 2025, "child", derived=True)
    memory.put(OTHER, 2026, derived=True)
    memory.put(OTHER, 2027, derived=True)
    with calculation():
        memory.delete(2025, "child")
        memory.delete(2026)
        memory.mark_derived_except({"default:2025"})
        assert memory.drop_computed() == 1
    assert_immutable(memory.get(2025), VALUES)
    assert memory._inputs == frozenset({"default:2025"})
    assert memory._sequence_numbers == {"default:2025": 31}


@pytest.mark.parametrize("operation", ["mark", "unmark"])
def test_actual_input_demotion_refuses_without_changing_any_mark(operation):
    memory = storage()
    memory.put(OTHER, 2026)
    before = snapshot(memory)
    with calculation():
        with pytest.raises(StoredDrawError, match=f"demote an input of {NAME}"):
            if operation == "mark":
                memory.mark_derived_except(set())
            else:
                memory._unmark_input("default:2025")
    assert snapshot(memory) == before


def test_unchanged_marks_and_absent_marks_pass_during_a_calculation():
    memory = storage()
    before = snapshot(memory)
    with calculation():
        memory.mark_derived_except({"default:2025", "default:2026"})
        memory._unmark_input("default:2026")
    assert snapshot(memory) == before


def test_a_one_shot_kept_key_iterable_cannot_demote_an_input():
    memory = storage()
    before = snapshot(memory)
    with calculation():
        memory.mark_derived_except(iter(["default:2025"]))
    assert snapshot(memory) == before


@pytest.mark.parametrize("during", [False, True])
def test_a_derived_store_clears_only_its_stale_input_mark(during):
    memory = storage()
    memory._inputs = memory._inputs | {"default:2026", "default:2027"}

    def store_derived():
        memory.put(OTHER, 2026, derived=True, sequence_number=32)

    if during:
        with calculation():
            store_derived()
    else:
        store_derived()
    assert memory._inputs == frozenset({"default:2025", "default:2027"})
    assert memory.is_derived(2026)
    assert_immutable(memory.get(2025), VALUES)
    assert_immutable(memory.get(2026), OTHER)
    assert memory._sequence_numbers == {"default:2025": 31, "default:2026": 32}


@pytest.mark.parametrize("during", [False, True])
@pytest.mark.parametrize("invalid", ["array", "branch", "period"])
def test_an_invalid_derived_store_keeps_stale_marks_and_storage_unchanged(
    during, invalid
):
    memory = storage()
    values, target, branch = OTHER, 2026, "default"
    if invalid == "array":
        values = OTHER.astype(object)
    elif invalid == "branch":
        branch = "bad:branch"
    else:
        target = "year:2026-01-02"
    memory._inputs = memory._inputs | {memory._key(target, branch)}
    before = snapshot(memory)

    def attempt():
        with pytest.raises(ValueError):
            memory.put(values, target, branch, derived=True)

    if during:
        with calculation():
            attempt()
    else:
        attempt()
    assert snapshot(memory) == before


def test_between_calculation_deletions_and_demotions_keep_frozen_marks():
    memory = storage()
    memory.put(OTHER, 2026)
    memory.mark_derived_except({"default:2025"})
    assert isinstance(memory._inputs, frozenset)
    memory.delete(2026)
    assert isinstance(memory._inputs, frozenset)
    memory.delete()
    assert memory._inputs == frozenset()
    assert memory._sequence_numbers == {}
    memory.put(VALUES, 2025)
    memory._unmark_input("default:2025")
    assert memory._inputs == frozenset()


@pytest.mark.parametrize("derived", [False, True])
def test_put_copies_the_callers_memory_and_get_returns_a_separate_array(derived):
    memory = ProtectedMemoryStorage(False, NAME)
    given = VALUES.copy()
    memory.put(given, 2025, derived=derived)
    given[:] = 0
    first = memory.get(2025)
    second = memory.get(2025)
    assert first is not second
    assert first is not memory._arrays["default:2025"]
    assert first.base is second.base
    assert_immutable(first, VALUES)
    first.shape = (3, 1)
    second.dtype = np.uint32
    assert_immutable(memory.get(2025), VALUES)


@pytest.mark.parametrize(
    "values",
    [np.array(0.25), np.arange(6).reshape(2, 3), np.empty((0, 3)), np.arange(10)[::2]],
)
def test_every_shape_and_layout_reads_over_bytes(values):
    memory = ProtectedMemoryStorage(False, NAME)
    memory.put(values, 2025)
    assert_immutable(memory.get(2025), values)
    assert isinstance(memory._arrays["default:2025"].base, bytes)


@pytest.mark.parametrize(
    "values",
    [
        np.array([0.0, -0.0, np.inf, -np.inf, np.nan], dtype=">f8"),
        np.array([complex(-0.0, 1), complex(2, -0.0), complex(np.nan, np.inf)]),
    ],
)
def test_numeric_special_values_keep_their_stored_bits(values):
    memory = ProtectedMemoryStorage(False, NAME)
    memory.put(values, 2025)
    assert_immutable(memory.get(2025), values)
    assert_immutable(memory.clone().get(2025), values)
    assert_immutable(pickle.loads(pickle.dumps(memory)).get(2025), values)


class ArraySubclass(np.ndarray):
    pass


@pytest.mark.parametrize(
    "values",
    [
        np.ma.array(VALUES, mask=[False, True, False]),
        VALUES.view(ArraySubclass),
        np.array([1, 2, 3], dtype=object),
        np.array(["1", "2", "3"]),
        np.array([b"1", b"2", b"3"]),
        np.array(["2025-01-01"], dtype="datetime64[D]"),
        np.zeros(3, dtype=[("draw", "f4")]),
        [0.25, 0.5, 0.75],
    ],
)
def test_non_plain_or_non_numeric_values_refuse_before_changing_storage(values):
    memory = storage()
    before = snapshot(memory)
    with pytest.raises(StoredDrawError, match=NAME):
        memory.put(values, 2026)
    assert snapshot(memory) == before


@pytest.mark.parametrize("share_arrays", [False, True])
def test_clone_shares_only_immutable_arrays_and_copies_indices(share_arrays):
    memory = storage()
    memory.put(OTHER, 2026, derived=True, sequence_number=32)
    child = memory.clone(share_arrays=share_arrays)
    assert isinstance(child, ProtectedMemoryStorage)
    assert snapshot(child) == snapshot(memory)
    assert child._arrays is not memory._arrays
    assert child._arrays["default:2025"] is memory._arrays["default:2025"]
    assert child._sequence_numbers is not memory._sequence_numbers
    assert isinstance(child._inputs, frozenset)
    returned = child.get(2025)
    returned.dtype = np.uint8
    assert_immutable(child.get(2025), VALUES)
    assert_immutable(memory.get(2025), VALUES)
    child.put(OTHER, 2025)
    child.delete(2026)
    assert_immutable(memory.get(2025), VALUES)
    assert_immutable(memory.get(2026), OTHER)


def test_getstate_hands_out_no_mutable_container_or_kept_array():
    memory = storage()
    before = snapshot(memory)
    state = memory.__getstate__()
    assert state["_arrays"] is not memory._arrays
    assert state["_arrays"]["default:2025"] is not memory._arrays["default:2025"]
    assert state["_sequence_numbers"] is not memory._sequence_numbers
    assert "_array_dtypes" not in memory.__dict__
    assert isinstance(state["_inputs"], frozenset)
    state["_arrays"]["default:2025"].dtype = np.uint8
    state["_arrays"].clear()
    state["_sequence_numbers"].clear()
    state["_array_dtypes"].clear()
    state["_inputs"] = frozenset()
    assert snapshot(memory) == before


def test_standard_pickle_restores_every_value_over_immutable_bytes():
    memory = storage()
    memory.put(OTHER, 2026, derived=True, sequence_number=32)
    with calculation():
        restored = pickle.loads(pickle.dumps(memory))
    assert snapshot(restored) == snapshot(memory)
    assert isinstance(restored._inputs, frozenset)
    assert_immutable(restored.get(2025), VALUES)
    assert_immutable(restored.get(2026), OTHER)


def test_pickle_keeps_an_empty_non_native_array_dtype():
    values = np.empty(0, dtype=">i2")
    memory = ProtectedMemoryStorage(False, NAME)
    memory.put(values, 2025)
    restored = pickle.loads(pickle.dumps(memory))
    assert_immutable(restored.get(2025), values)


def test_pickling_exposes_only_detached_array_objects():
    import io

    memory = storage()
    arrays = []

    class ArrayCollector(pickle.Pickler):
        def persistent_id(self, value):
            if isinstance(value, np.ndarray):
                arrays.append(value)
            return None

    ArrayCollector(io.BytesIO()).dump(memory)
    assert arrays
    for value in arrays:
        assert value is not memory._arrays["default:2025"]
        value.shape = (value.size, 1)
        value.dtype = np.uint8
    assert_immutable(memory.get(2025), VALUES)
    assert_immutable(memory.clone().get(2025), VALUES)


def test_setstate_copies_legacy_values_and_marks_without_changing_the_state():
    memory = ProtectedMemoryStorage(False, NAME)
    given = VALUES.copy()
    state = {"is_eternal": False, "_arrays": {"default:2025": given}}
    memory.__setstate__(state)
    assert state["_arrays"]["default:2025"] is given
    given[:] = 0
    assert_immutable(memory.get(2025), VALUES)
    assert memory._inputs == frozenset({"default:2025"})
    assert memory._sequence_numbers == {}


def test_from_storage_preserves_values_marks_and_sequence_numbers():
    plain = InMemoryStorage(False)
    plain.put(VALUES.copy(), 2025, sequence_number=31)
    plain.put(OTHER.copy(), 2026, derived=True, sequence_number=32)
    protected = ProtectedMemoryStorage.from_storage(plain, NAME)
    assert snapshot(protected) == snapshot(plain)
    assert protected.variable_name == NAME
    plain.get(2025)[:] = 0
    assert_immutable(protected.get(2025), VALUES)
    assert_immutable(protected.get(2026), OTHER)
    assert isinstance(protected._inputs, frozenset)


def test_from_storage_copies_a_shared_array_without_changing_the_source():
    source = InMemoryStorage(False)
    source.put(VALUES.copy(), 2025, sequence_number=31)
    plain = source.clone(share_arrays=True)
    before = snapshot(plain)
    protected = ProtectedMemoryStorage.from_storage(plain, NAME)
    assert snapshot(plain) == before
    source.get(2025)[:] = 0
    assert_immutable(protected.get(2025), VALUES)


def test_legacy_state_keeps_its_recorded_derived_values_derived():
    memory = ProtectedMemoryStorage(False, NAME)
    memory.__setstate__(
        {
            "is_eternal": False,
            "_arrays": {"default:2025": VALUES.copy(), "default:2026": OTHER.copy()},
            "_derived": {"default:2026"},
        }
    )
    assert memory._inputs == frozenset({"default:2025"})
    assert memory.is_derived(2026)
    assert_immutable(memory.get(2025), VALUES)
    assert_immutable(memory.get(2026), OTHER)


def test_eternal_keys_and_refusals_follow_the_storage_period():
    memory = ProtectedMemoryStorage(True, NAME)
    memory.put(VALUES, 2025)
    assert_immutable(memory.get(2040), VALUES)
    assert memory._inputs == frozenset({"default:ETERNITY"})
    with calculation():
        with pytest.raises(StoredDrawError):
            memory.delete(2040)
        with pytest.raises(StoredDrawError):
            memory.put(OTHER, 2040, derived=True)
    assert_immutable(memory.get(2025), VALUES)


def test_core_key_validation_still_precedes_any_storage_change():
    memory = storage()
    before = snapshot(memory)
    with pytest.raises(ValueError, match="may not contain"):
        memory.put(VALUES, 2026, "bad:branch")
    with pytest.raises(ValueError, match="mid-month"):
        memory.put(VALUES, "year:2026-01-02")
    assert snapshot(memory) == before


NUMERIC_DTYPES = tuple(
    dict.fromkeys(
        np.dtype(dtype).newbyteorder(order)
        for dtype in [
            np.bool_,
            np.int8,
            np.int16,
            np.int32,
            np.int64,
            np.uint8,
            np.uint16,
            np.uint32,
            np.uint64,
            np.float16,
            np.float32,
            np.float64,
            np.longdouble,
            np.complex64,
            np.complex128,
            np.clongdouble,
        ]
        for order in ["<", ">"]
    )
)


@settings(max_examples=150, deadline=None)
@given(
    dtype=st.sampled_from(NUMERIC_DTYPES),
    size=st.integers(0, 64),
    data=st.data(),
)
def test_numeric_dtypes_and_sizes_round_trip_over_immutable_bytes(dtype, size, data):
    byte_count = size * dtype.itemsize
    raw = data.draw(st.binary(min_size=byte_count, max_size=byte_count))
    given = np.frombuffer(raw, dtype=dtype)
    memory = ProtectedMemoryStorage(False, NAME)
    memory.put(given, 2025)
    assert_immutable(memory.get(2025), given)
    assert_immutable(memory.clone().get(2025), given)
    assert_immutable(pickle.loads(pickle.dumps(memory)).get(2025), given)


@settings(max_examples=100, deadline=None)
@given(
    operations=st.lists(
        st.sampled_from(
            ["read", "clone", "derived", "delete", "drop", "marks", "input", "demote"]
        ),
        max_size=40,
    )
)
def test_no_sequence_of_operations_during_a_calculation_changes_an_input(operations):
    memory = storage()
    input_record = (memory._inputs, memory._sequence_numbers["default:2025"])
    with calculation():
        for operation in operations:
            if operation == "read":
                returned = memory.get(2025)
                returned.shape = (1, 3)
            elif operation == "clone":
                assert_immutable(memory.clone().get(2025), VALUES)
            elif operation == "derived":
                memory.put(OTHER, 2026, derived=True)
            elif operation == "delete":
                memory.delete(2026)
            elif operation == "drop":
                memory.drop_computed()
            elif operation == "marks":
                memory.mark_derived_except({"default:2025"})
            elif operation == "input":
                with pytest.raises(StoredDrawError):
                    memory.put(OTHER, 2025)
            else:
                with pytest.raises(StoredDrawError):
                    memory.mark_derived_except(set())
            assert_immutable(memory.get(2025), VALUES)
            assert (
                memory._inputs,
                memory._sequence_numbers["default:2025"],
            ) == input_record
