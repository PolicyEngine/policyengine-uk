"""Wealth ranks split ties in original household order (issue #2579)."""

import numpy as np
import pytest

from policyengine_uk.variables.household.wealth.household_wealth_decile import (
    household_wealth_decile,
)


class FakeHousehold:
    def __init__(self, wealth, weights, sizes):
        self.values = {
            "total_wealth": np.array(wealth, dtype=float),
            "household_weight": np.array(weights, dtype=float),
            "household_count_people": np.array(sizes),
        }

    def __call__(self, variable, period):
        return self.values[variable]


def test_zero_wealth_ties_fill_the_bottom_deciles():
    # Fifty equally weighted people: each five successive households fill
    # one decile, including the fifteen households with zero wealth.
    household = FakeHousehold([0] * 15 + list(range(1, 36)), [1] * 50, [1] * 50)

    result = household_wealth_decile.formula(household, 2026, None)

    np.testing.assert_array_equal(result, np.repeat(np.arange(1, 11), 5))


@pytest.mark.parametrize(
    "wealth, weights, sizes, expected",
    [
        # Cumulative person weights 1, 2, 4, 10 out of 10 determine deciles.
        ([0, 0, 0, 10], [1, 1, 2, 6], [1, 1, 1, 1], [1, 2, 4, 10]),
        # Sorting must restore original rows, retaining order within ties.
        ([10, 0, 0, 0], [6, 1, 1, 2], [1, 1, 1, 1], [10, 1, 2, 4]),
        # The same effective weights, factored through household sizes.
        ([0, 0, 0, 10], [1, 1, 1, 1], [1, 1, 2, 6], [1, 2, 4, 10]),
        # Unique wealth retains cumulative endpoint ranks 6, 1, 10, 3.
        ([30, 10, 40, 20], [3, 1, 4, 2], [1, 1, 1, 1], [6, 1, 10, 3]),
        # Negative households still count in the population before masking.
        ([0, -5, 10, -5, 0], [1, 1, 4, 2, 2], [1, 1, 1, 1, 1], [4, -1, 10, -1, 6]),
        # Indivisible records with large weights can still skip deciles.
        ([0, 0, 0], [7, 2, 1], [1, 1, 1], [7, 9, 10]),
    ],
    ids=[
        "unequal_weights",
        "original_row_mapping",
        "household_sizes",
        "unique_wealth",
        "negative_wealth",
        "indivisible_weights",
    ],
)
def test_person_weighted_wealth_ranks(wealth, weights, sizes, expected):
    household = FakeHousehold(wealth, weights, sizes)

    for _ in range(2):
        result = household_wealth_decile.formula(household, 2026, None)
        np.testing.assert_array_equal(result, expected)
        np.testing.assert_array_equal(household.values["total_wealth"], wealth)


def test_zero_total_weight_still_raises():
    household = FakeHousehold([0, 0], [0, 0], [1, 1])

    with pytest.raises(ZeroDivisionError, match="zero total weight"):
        household_wealth_decile.formula(household, 2026, None)
