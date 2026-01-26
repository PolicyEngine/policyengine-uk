"""
Tests for pandas 3.0.0 compatibility in policyengine-uk.

These tests verify that policyengine-uk works correctly with pandas 3.0.0,
which introduces PyArrow-backed strings as default (StringDtype).

These tests will FAIL if policyengine-core < 3.9.1 is used, which doesn't
have the pandas 3 compatibility fixes.
"""

import numpy as np

from policyengine_uk import Simulation


class TestRegionParameterLookupWithPandas3:
    """
    Test that region-based parameter lookup works with pandas 3 StringArray.

    In pandas 3, string columns use StringDtype by default. When looking up
    region-specific parameters using vectorial indexing, the region codes
    may be StringArray instead of numpy array.

    policyengine-core >= 3.9.1 converts StringArray to numpy before lookup.
    """

    def test_region_parameter_lookup(self):
        """
        Test that region-based parameter lookup works for multiple regions.

        This exercises the VectorialParameterNodeAtInstant.__getitem__ fix
        that converts pandas StringArray to numpy array.
        """
        # Create a simulation with households in different regions
        sim = Simulation(
            situation={
                "people": {
                    "person1": {"age": {"2024": 30}},
                    "person2": {"age": {"2024": 40}},
                },
                "households": {
                    "household1": {
                        "members": ["person1"],
                        "region": {"2024": "LONDON"},
                    },
                    "household2": {
                        "members": ["person2"],
                        "region": {"2024": "SCOTLAND"},
                    },
                },
            }
        )

        # This calculation involves region-based parameter lookups
        # If pandas 3 StringArray handling is broken, this would raise:
        # TypeError: unhashable type: 'StringArray'
        result = sim.calculate("household_net_income", "2024")

        # Basic sanity check - should return an array
        assert isinstance(result, np.ndarray)
        assert len(result) == 2  # Two households


class TestFilledArrayWithStringDtype:
    """
    Test that population.filled_array works with pandas StringDtype.

    In pandas 3, numpy.full() cannot handle StringDtype. policyengine-core
    >= 3.9.1 converts StringDtype to object dtype before calling numpy.full().
    """

    def test_string_variable_default_value(self):
        """
        Test that string-typed variables work correctly.

        Variables with value_type=str use filled_array with a string dtype.
        In pandas 3, this would fail with:
        TypeError: Cannot interpret '<StringDtype>' as a data type
        """
        # Create a simple simulation
        sim = Simulation(
            situation={
                "people": {
                    "person1": {"age": {"2024": 30}},
                },
                "households": {
                    "household1": {
                        "members": ["person1"],
                    },
                },
            }
        )

        # region is a string/enum variable - calculating it exercises filled_array
        result = sim.calculate("region", "2024")

        # Should return valid results without error
        assert len(result) == 1


class TestEnumVariableWithPandas3:
    """
    Test that Enum variables work correctly with pandas 3.

    Enum variables involve string-based parameter lookups which can
    trigger the StringArray issue in pandas 3.
    """

    def test_tenure_type_enum(self):
        """
        Test that tenure_type enum works correctly.
        """
        sim = Simulation(
            situation={
                "people": {
                    "person1": {"age": {"2024": 30}},
                },
                "households": {
                    "household1": {
                        "members": ["person1"],
                    },
                },
            }
        )

        # tenure_type is an enum variable
        result = sim.calculate("tenure_type", "2024")

        # Should return valid results
        assert len(result) == 1
