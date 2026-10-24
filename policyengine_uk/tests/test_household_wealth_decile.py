"""Wealth ranks split ties by a fixed hash of household_id (#2579, #2617)."""

import numpy as np
import pytest

from policyengine_uk.variables.household.wealth.household_wealth_decile import (
    _fixed_hash,
    household_wealth_decile,
)


def ids_in_hash_order(count):
    """Household ids whose fixed-hash order is their row order.

    With these ids, a tie splits in row order, so a test can state the
    expected deciles row by row.
    """
    ids = np.arange(count * 20)
    return ids[np.argsort(_fixed_hash(ids))][:count]


class FakeHousehold:
    def __init__(self, wealth, weights, sizes, ids=None):
        self.values = {
            "total_wealth": np.array(wealth, dtype=float),
            "household_weight": np.array(weights, dtype=float),
            "household_count_people": np.array(sizes),
            "household_id": np.array(
                ids_in_hash_order(len(wealth)) if ids is None else ids, dtype=int
            ),
        }

    def __call__(self, variable, period):
        return self.values[variable]


def test_zero_wealth_ties_fill_the_bottom_deciles():
    # Fifty equally weighted people: each five successive households fill
    # one decile, including the fifteen households with zero wealth. The
    # default ids put the tied households in hash order = row order.
    household = FakeHousehold([0] * 15 + list(range(1, 36)), [1] * 50, [1] * 50)

    result = household_wealth_decile.formula(household, 2026, None)

    np.testing.assert_array_equal(result, np.repeat(np.arange(1, 11), 5))


@pytest.mark.parametrize(
    "wealth, weights, sizes, expected",
    [
        # Cumulative person weights 1, 2, 4, 10 out of 10 determine deciles.
        ([0, 0, 0, 10], [1, 1, 2, 6], [1, 1, 1, 1], [1, 2, 4, 10]),
        # Sorting must restore original rows, retaining hash order within ties.
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


def test_tied_households_keep_their_decile_when_rows_are_shuffled():
    # Issue #2617: ties split by a fixed hash of household_id, so a
    # dataset rebuild that reorders households moves nobody's decile.
    ids = np.arange(1000, 1050) * 7
    wealth = [0] * 15 + list(range(1, 36))
    household = FakeHousehold(wealth, [1] * 50, [1] * 50, ids)
    by_id = dict(zip(ids, household_wealth_decile.formula(household, 2026, None)))

    order = np.random.default_rng(0).permutation(50)
    shuffled = FakeHousehold(np.array(wealth)[order], [1] * 50, [1] * 50, ids[order])
    result = household_wealth_decile.formula(shuffled, 2026, None)

    assert dict(zip(ids[order], result)) == by_id
    # The fifteen £0 households still fill deciles 1 to 3, five each.
    zero_deciles = [by_id[i] for i in ids[:15]]
    assert sorted(zero_deciles) == [1] * 5 + [2] * 5 + [3] * 5


def test_tie_order_does_not_follow_household_id_order():
    # Row order and household_id order agree here, so a rule that
    # follows either one would put the lowest ids in decile 1.
    ids = np.arange(20)
    household = FakeHousehold([0] * 20, [1] * 20, [1] * 20, ids)

    result = household_wealth_decile.formula(household, 2026, None)

    assert not np.array_equal(result, np.sort(result))


def test_zero_weight_household_gets_a_decile_of_at_least_1():
    # Issue #2617: a zero-weight household at the start of the order
    # used to get decile 0, outside the 1 to 10 range.
    for ids in ([0, 1, 2], [1, 0, 2], [5, 9, 3]):
        household = FakeHousehold([0, 0, 5], [0, 1, 1], [1, 1, 1], ids)

        result = household_wealth_decile.formula(household, 2026, None)

        assert result.min() >= 1
        assert result[2] == 10
