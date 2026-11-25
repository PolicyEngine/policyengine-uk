"""Geography names retain the public Core encode/decode contract.

These are codec interoperability checks, not policy or timing thresholds.
"""

import numpy as np
import pandas as pd
import pytest
from policyengine_core.enums import Enum, EnumArray

from policyengine_uk.utils.geography import _names
from policyengine_uk.variables.household.demographic.country import Country
from policyengine_uk.variables.household.demographic.geography import Region
from policyengine_uk.variables.household.demographic.locations import (
    BRMAName,
    LocalAuthority,
)


GEOGRAPHIES = (Country, Region, LocalAuthority, BRMAName)
FORMS = (
    "unicode",
    "bytes",
    "objects",
    "members",
    "integers",
    "encoded",
    "member_series",
)
SHAPES = (
    "matrix_unicode",
    "matrix_integer",
    "encoded_scalar",
    "empty_encoded",
    "empty_unicode",
    "empty_matrix",
    "strided_encoded",
)


class ShortNames(Enum):
    A = "a"
    BB = "bb"


class OtherGeography(Enum):
    ALPHA = "first"
    BETA_WITH_A_LONG_NAME = "second"


class SparseNames(Enum):
    def __init__(self, label, index):
        self.index = index

    EAST = ("east", 2)
    WEST = ("west", 7)


class EmptyNames(Enum):
    pass


class CustomDecodedArray(EnumArray):
    def decode_to_str(self):
        return np.full(self.shape, "subclass-decoder", dtype="U16")


def assert_matches_core(values, possible_values):
    expected = possible_values.encode(values).decode_to_str()
    actual = _names(values, possible_values)
    assert isinstance(actual, np.ndarray)
    assert actual.shape == expected.shape
    assert actual.dtype == expected.dtype
    np.testing.assert_array_equal(actual, expected)
    return actual


@pytest.mark.parametrize("possible_values", GEOGRAPHIES, ids=lambda enum: enum.__name__)
@pytest.mark.parametrize("form", FORMS)
def test_every_geography_member_matches_core(possible_values, form):
    members = list(possible_values)
    names = [member.name for member in members]
    indices = np.array([member.index for member in members], dtype=np.int16)
    inputs = {
        "unicode": lambda: np.array(names),
        "bytes": lambda: np.array(names, dtype="S"),
        "objects": lambda: np.array(names, dtype=object),
        "members": lambda: np.array(members, dtype=object),
        "integers": lambda: indices.copy(),
        "encoded": lambda: EnumArray(indices.copy(), possible_values),
        # Core explicitly supports member Series with arbitrary labels via iloc.
        "member_series": lambda: pd.Series(
            members, index=np.arange(len(members)) + 1000
        ),
    }
    actual = assert_matches_core(inputs[form](), possible_values)
    np.testing.assert_array_equal(actual, names)


@pytest.mark.parametrize("possible_values", GEOGRAPHIES, ids=lambda enum: enum.__name__)
@pytest.mark.parametrize("shape", SHAPES)
def test_names_preserve_native_array_shape_and_dtype(possible_values, shape):
    members = list(possible_values)
    inputs = {
        "matrix_unicode": lambda: np.array(
            [member.name for member in members[:4]]
        ).reshape(2, 2),
        "matrix_integer": lambda: np.arange(4, dtype=np.int16).reshape(2, 2),
        "encoded_scalar": lambda: EnumArray(
            np.array(0, dtype=np.int16), possible_values
        ),
        "empty_encoded": lambda: EnumArray(
            np.empty(0, dtype=np.int16), possible_values
        ),
        "empty_unicode": lambda: np.empty(0, dtype="U1"),
        "empty_matrix": lambda: np.empty((0, 2), dtype=np.int16),
        "strided_encoded": lambda: EnumArray(
            np.arange(4, dtype=np.int16), possible_values
        )[::2],
    }
    assert_matches_core(inputs[shape](), possible_values)


@pytest.mark.parametrize("possible_values", GEOGRAPHIES, ids=lambda enum: enum.__name__)
def test_raw_integer_encoding_keeps_cores_int16_wrap(possible_values):
    # Core3.34.1 encodes ordinary integer arrays to int16 before decoding.
    values = np.array([65_536, 65_537, -65_536], dtype=np.int64)
    actual = assert_matches_core(values, possible_values)
    members = list(possible_values)
    np.testing.assert_array_equal(
        actual, [members[0].name, members[1].name, members[0].name]
    )


@pytest.mark.parametrize("possible_values", GEOGRAPHIES, ids=lambda enum: enum.__name__)
def test_already_encoded_invalid_indices_remain_lowercase_unknown(possible_values):
    # Already encoded arrays pass through Core.encode without an int16 cast.
    values = EnumArray(
        np.array([-1, len(possible_values), 65_536, 0], dtype=np.int64), possible_values
    )
    actual = assert_matches_core(values, possible_values)
    np.testing.assert_array_equal(actual[:3], ["unknown", "unknown", "unknown"])
    assert actual[3] == next(iter(possible_values)).name


@pytest.mark.parametrize(
    "possible_values", (Country, Region), ids=lambda enum: enum.__name__
)
def test_real_unknown_member_is_distinct_from_invalid_index(possible_values):
    values = EnumArray(
        np.array([possible_values.UNKNOWN.index, -1], dtype=np.int64), possible_values
    )
    np.testing.assert_array_equal(
        assert_matches_core(values, possible_values), ["UNKNOWN", "unknown"]
    )


@pytest.mark.parametrize(
    "values",
    [
        np.array([0.0, 1.5, np.nan]),
        np.array([False, True]),
        np.array([0 + 0j, 1 + 0j, 1.5 + 0j]),
        np.array([0, "0", None], dtype=object),
    ],
    ids=("float", "bool", "complex", "object"),
)
def test_encoded_noninteger_arrays_retain_native_decoder_semantics(values):
    assert_matches_core(EnumArray(values, Country), Country)


@pytest.mark.parametrize(
    "values",
    [
        np.array([0.5]),
        np.array([True]),
        np.array([1 + 1j]),
        np.array("ENGLAND"),
        ["ENGLAND"],
        np.array([b"\xff"], dtype="S1"),
    ],
    ids=("float", "bool", "complex", "raw-scalar", "string-list", "invalid-utf8"),
)
def test_unsupported_raw_inputs_preserve_encode_exceptions(values):
    with pytest.raises(Exception) as expected:
        Country.encode(values)
    with pytest.raises(type(expected.value)) as actual:
        _names(values, Country)
    assert str(actual.value) == str(expected.value)


@pytest.mark.parametrize("possible_values", GEOGRAPHIES, ids=lambda enum: enum.__name__)
def test_invalid_names_keep_native_encode_validation(possible_values):
    values = np.array(["not_a_geography_member"])
    with pytest.raises(ValueError) as expected:
        possible_values.encode(values)
    with pytest.raises(ValueError) as actual:
        _names(values, possible_values)
    assert str(actual.value) == str(expected.value)


@pytest.mark.parametrize(
    "requested_values", GEOGRAPHIES, ids=lambda enum: enum.__name__
)
def test_encoded_other_class_is_the_decoding_authority(requested_values):
    values = OtherGeography.encode(np.array(["BETA_WITH_A_LONG_NAME", "ALPHA"]))
    assert requested_values.encode(values) is values
    np.testing.assert_array_equal(
        assert_matches_core(values, requested_values),
        ["BETA_WITH_A_LONG_NAME", "ALPHA"],
    )


def test_short_custom_enum_dtype_keeps_native_unknown_width():
    values = np.array([0, 1], dtype=np.int16)
    actual = assert_matches_core(values, ShortNames)
    np.testing.assert_array_equal(actual, ["A", "BB"])
    assert actual.dtype == np.dtype("U7")


@pytest.mark.parametrize("form", ("names", "indices"))
def test_nondense_custom_enum_retains_native_decoder(form):
    values = np.array(["EAST", "WEST"]) if form == "names" else np.array([2, 7, -1])
    actual = assert_matches_core(values, SparseNames)
    np.testing.assert_array_equal(actual[:2], ["EAST", "WEST"])
    if form == "indices":
        assert actual[2] == "unknown"


@pytest.mark.parametrize("metadata", (None, EmptyNames), ids=("missing", "empty"))
def test_unsupported_metadata_preserves_native_failure(metadata):
    values = EnumArray(np.array([0], dtype=np.int16), metadata)
    with pytest.raises(Exception) as expected:
        Country.encode(values).decode_to_str()
    with pytest.raises(type(expected.value)) as actual:
        _names(values, Country)
    assert str(actual.value) == str(expected.value)


@pytest.mark.parametrize("kind", ("subclass", "instance"))
def test_custom_array_decoder_dispatch_is_preserved(kind):
    if kind == "subclass":
        values = CustomDecodedArray(np.array([0, 1]), Country)
        expected = ["subclass-decoder", "subclass-decoder"]
    else:
        values = EnumArray(np.array([0, 1]), Country)
        values.decode_to_str = lambda: np.full(
            values.shape, "instance-decoder", dtype="U16"
        )
        expected = ["instance-decoder", "instance-decoder"]
    np.testing.assert_array_equal(assert_matches_core(values, Region), expected)


def test_decoded_names_do_not_alias_sources_or_other_results():
    values = Country.encode(np.array(["ENGLAND", "SCOTLAND"]))
    original_indices = values.view(np.ndarray).copy()
    first = _names(values, Country)
    second = _names(values, Country)
    assert not np.shares_memory(first, values)
    assert not np.shares_memory(first, second)
    first[0] = "changed"
    np.testing.assert_array_equal(values.view(np.ndarray), original_indices)
    np.testing.assert_array_equal(second, ["ENGLAND", "SCOTLAND"])
    np.testing.assert_array_equal(_names(values, Country), ["ENGLAND", "SCOTLAND"])
    values[0] = Country.WALES.index
    np.testing.assert_array_equal(_names(values, Country), ["WALES", "SCOTLAND"])
    np.testing.assert_array_equal(second, ["ENGLAND", "SCOTLAND"])


def test_replacement_class_identity_cannot_reuse_another_classs_names():
    first = Enum("ReplacementGeography", {"FIRST": "first"})
    second = Enum("ReplacementGeography", {"A_DIFFERENT_LONG_NAME": "second"})
    assert first is not second
    np.testing.assert_array_equal(assert_matches_core(np.array([0]), first), ["FIRST"])
    np.testing.assert_array_equal(
        assert_matches_core(np.array([0]), second), ["A_DIFFERENT_LONG_NAME"]
    )
    # Class-only lookup eviction must not change results or cache caller arrays.
    for index in range(20):
        temporary = Enum("ReplacementGeography", {f"MEMBER_{index}": str(index)})
        np.testing.assert_array_equal(
            assert_matches_core(np.array([0]), temporary), [f"MEMBER_{index}"]
        )
    np.testing.assert_array_equal(assert_matches_core(np.array([0]), first), ["FIRST"])


def test_native_decoder_rebound_to_another_array_is_respected():
    values = Country.encode(np.array(["ENGLAND", "SCOTLAND"]))
    other = Country.encode(np.array(["WALES"]))
    # Core accepts this existing instance override; both function and self
    # determine native bound-method dispatch, including the returned shape.
    values.decode_to_str = other.decode_to_str
    np.testing.assert_array_equal(assert_matches_core(values, Country), ["WALES"])
