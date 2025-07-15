"""
Test OS consistency for parameter uprating.

This test verifies that the Ubuntu/macOS parameter uprating fix works correctly
by ensuring that BASELINE_GROWFACTORS is consistently accessible and contains
the expected data structure regardless of when it's accessed.
"""

import pandas as pd
from policyengine_uk.data.economic_assumptions import (
    BASELINE_GROWFACTORS,
    get_baseline_growfactors,
    create_policyengine_uprating_factors_table,
)


def test_baseline_growfactors_is_accessible():
    """Test that BASELINE_GROWFACTORS can be accessed without errors."""
    # This should not raise any exceptions
    df = BASELINE_GROWFACTORS
    # The proxy should behave like a DataFrame when accessed
    assert hasattr(df, "columns")
    assert hasattr(df, "index")
    assert len(df.columns) > 0


def test_baseline_growfactors_proxy_behavior():
    """Test that the proxy object behaves like a DataFrame."""
    # Test that we can access DataFrame methods
    df = BASELINE_GROWFACTORS

    # Test common DataFrame operations
    assert hasattr(df, "columns")
    assert hasattr(df, "index")
    assert hasattr(df, "shape")

    # Test that we can call DataFrame methods
    copy_df = df.copy()
    assert isinstance(copy_df, pd.DataFrame)
    # Compare the copy with the actual DataFrame, not the proxy
    actual_df = get_baseline_growfactors()
    assert copy_df.equals(actual_df)


def test_deferred_initialization_consistency():
    """Test that deferred initialization produces consistent results."""
    # Get the DataFrame through the proxy's __getattr__ delegation
    df1_columns = BASELINE_GROWFACTORS.columns

    # Get the DataFrame through the function
    df2 = get_baseline_growfactors()

    # Both should access the same underlying DataFrame
    assert list(df1_columns) == list(df2.columns)

    # Test that multiple accesses return the same object (caching)
    df3 = get_baseline_growfactors()
    assert df2 is df3  # Should be the same object due to caching


def test_growfactors_structure():
    """Test that the growth factors have the expected structure."""
    df = BASELINE_GROWFACTORS

    # Should have required columns
    assert "Parameter" in df.columns

    # Should have year columns
    year_columns = [col for col in df.columns if col.isdigit()]
    assert len(year_columns) > 0

    # Should have some rows (access through proxy)
    assert len(df.index) > 0

    # Parameter column should contain parameter names
    # Access through the actual DataFrame to check Parameter column
    actual_df = get_baseline_growfactors()
    assert all(isinstance(param, str) for param in actual_df["Parameter"])


def test_multiple_access_patterns():
    """Test different ways of accessing the growth factors."""
    # Direct access (proxy)
    df1 = BASELINE_GROWFACTORS

    # Function access (actual DataFrame)
    df2 = get_baseline_growfactors()

    # Copy access (should return actual DataFrame)
    df3 = BASELINE_GROWFACTORS.copy()

    # df2 and df3 should be DataFrames
    assert isinstance(df2, pd.DataFrame)
    assert isinstance(df3, pd.DataFrame)

    # df1 should be the proxy
    assert hasattr(df1, "columns")
    assert hasattr(df1, "index")

    # df2 and df3 should be equal (both are actual DataFrames)
    assert df2.equals(df3)

    # df3 should be a copy, not the same object
    assert df3 is not df2


def test_create_function_works():
    """Test that the create function works independently."""
    # This should create a new DataFrame without using the cache
    df = create_policyengine_uprating_factors_table(print_diff=False)

    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    assert "Parameter" in df.columns

    # Should be equivalent to the cached version
    cached_df = get_baseline_growfactors()
    assert df.equals(cached_df)


def test_os_consistency_simulation():
    """
    Simulate the OS consistency issue by testing multiple initialization patterns.

    This test verifies that regardless of when the growth factors are accessed,
    they return consistent results.
    """
    import importlib
    from policyengine_uk.data import economic_assumptions

    # Force reload to simulate fresh import
    importlib.reload(economic_assumptions)

    # Access through different paths
    df1 = economic_assumptions.BASELINE_GROWFACTORS
    df2 = economic_assumptions.get_baseline_growfactors()

    # Should be consistent - df1 is proxy, df2 is actual DataFrame
    assert isinstance(df2, pd.DataFrame)
    assert hasattr(df1, "columns")
    assert hasattr(df1, "index")

    # Should have the same structure when accessed through proxy
    assert list(df1.columns) == list(df2.columns)
    assert len(df1.index) == len(df2)
