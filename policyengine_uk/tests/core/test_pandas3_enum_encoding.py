"""Test pandas 3.0 compatibility with enum encoding.

This test verifies that policyengine-core 3.23.5+ correctly handles
pandas Series with StringDtype index when encoding enums.
"""
import numpy as np
import pandas as pd
import pytest

from policyengine_core.enums import Enum


class SampleEnum(Enum):
    VALUE_A = "value_a"
    VALUE_B = "value_b"


def test_enum_encode_with_pandas_series():
    """Test that Enum.encode works with pandas Series containing enum items.
    
    In pandas 3.0, Series with StringDtype use label-based indexing by default.
    This test verifies the fix in policyengine-core 3.23.5 that uses .iloc[0]
    for positional access instead of array[0].
    """
    enum_items = [SampleEnum.VALUE_A, SampleEnum.VALUE_B, SampleEnum.VALUE_A]
    series = pd.Series(enum_items)
    
    # This would fail with KeyError: 0 before the fix
    encoded = SampleEnum.encode(series)
    
    assert len(encoded) == 3
    assert list(encoded) == [0, 1, 0]


def test_enum_encode_with_string_index():
    """Test enum encoding with explicitly string-indexed Series."""
    enum_items = [SampleEnum.VALUE_A, SampleEnum.VALUE_B]
    series = pd.Series(enum_items, index=["a", "b"])
    
    encoded = SampleEnum.encode(series)
    
    assert len(encoded) == 2
    assert list(encoded) == [0, 1]
