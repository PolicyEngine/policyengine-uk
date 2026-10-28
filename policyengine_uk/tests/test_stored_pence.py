"""stored_pence: an amount of money held in float32, in pence.

Invariants:

1. Whole pence round-trip: every whole number of pence below £131,072,
   stored in float32, comes back as exactly that number (exhaustive).
2. Bounded: the result is never more than half a float32 step from the
   stored amount, so it moves an amount only to the whole pence it is held
   as.
3. Fractions kept: a stored amount more than half a step from every whole
   penny comes back exactly, to be rounded as the rule requires.
4. Monotonic: a larger stored amount never gives fewer pence.

summed: a float32 sum of float32 amounts, in pence.

5. Rounding bounded: a float32 sum of up to eight float32 amounts of either
   sign, nested in sums of sums and added one at a time as policyengine-core
   adds them, lies within summed's tolerance of the exact sum of the stored
   amounts, so summed returns that sum.
6. Sums recovered: such a sum of whole-pence amounts below £131,072 each
   comes back as exactly the sum of their pence, including sums that
   stored_pence alone would not recover.
7. Not a sum: a total further from the parts' sum than that rounding, as when
   it is entered directly, comes back as stored_pence(total). For amounts
   under £10,000 in all, any total a whole penny or more from their sum is.

months_summed: a monthly flow summed over a year, in pence.

8. A year's amount recovered: every whole number of pence below £32,768,
   entered for a year and divided among its twelve months in float32 as
   policyengine-core divides it, comes back as exactly that number
   (exhaustive). Below £32,768 the months' rounding and the year's is under
   half a penny, so no other whole penny lies within it.
9. Months recovered: twelve whole-pence monthly amounts below £131,072 in
   all come back as exactly the sum of their pence.
10. Bounded: the result is the exact sum of the months as stored, or a whole
    penny within a float32 step of each month and of the year of it.
"""

from fractions import Fraction
from functools import reduce

import numpy as np
from hypothesis import example, given, settings
from hypothesis import strategies as st

from policyengine_uk.utils.pence import (
    Pence,
    months_summed,
    stored,
    stored_pence,
    summed,
)

# Below 2^17 pounds a float32 step is under a penny.
LIMIT_PENCE = 2**17 * 100


def test_every_whole_pence_amount_below_2_to_the_17_pounds_round_trips():
    for start in range(0, LIMIT_PENCE, 2_000_000):
        pence = np.arange(start, min(start + 2_000_000, LIMIT_PENCE))
        stored = (pence / 100).astype(np.float32)
        recovered = stored_pence(stored)
        assert recovered.dtype == np.float64
        wrong = np.nonzero(recovered != pence)[0]
        assert len(wrong) == 0, pence[wrong[:5]]


float32_amounts = st.floats(
    min_value=0, max_value=2.0**17, width=32, allow_nan=False, allow_infinity=False
)


@settings(max_examples=300, deadline=None, derandomize=True)
@given(amount=float32_amounts)
# £10,608.52 is stored as 10,608.51953125; the float32 below it is a
# fraction of a penny short of £10,608.52.
@example(amount=10_608.51953125)
@example(amount=10_608.517578125)
def test_moves_an_amount_at_most_half_a_step_and_keeps_fractions(amount):
    stored = np.float32(amount)
    exact = Fraction(float(stored)) * 100
    half_step = Fraction(float(np.spacing(stored))) * 50
    result = Fraction(float(stored_pence(stored)))
    assert abs(result - exact) <= half_step
    whole = round(exact)
    if abs(exact - whole) > half_step:
        assert result == exact
    else:
        assert result == whole


@settings(max_examples=200, deadline=None, derandomize=True)
@given(amounts=st.lists(float32_amounts, min_size=2, max_size=50))
@example(amounts=[10_608.517578125, 10_608.51953125, 10_608.5205078125])
def test_never_gives_fewer_pence_for_more_money(amounts):
    stored = np.sort(np.array(amounts, dtype=np.float32))
    assert np.all(np.diff(stored_pence(stored)) >= 0)


def _float32_sum(tree):
    """A tree of float32 amounts (a list is a sum of its items), added one at
    a time in float32 as policyengine-core adds them, and read with summed,
    each amount as its exact value: (the float32 total, the Pence)."""
    if not isinstance(tree, list):
        amount = np.float32(tree)
        return amount, Pence(
            np.float64(amount) * 100, np.float64(abs(amount)), np.float64(1)
        )
    totals, parts = zip(*(_float32_sum(item) for item in tree))
    total = reduce(np.add, totals)
    return total, summed(total, parts)


def _exact(tree):
    """The exact sum of a tree's float32 amounts."""
    if isinstance(tree, list):
        return sum((_exact(item) for item in tree), Fraction(0))
    return Fraction(float(np.float32(tree)))


def _leaves(tree):
    return sum(_leaves(item) for item in tree) if isinstance(tree, list) else 1


# Float32 amounts of either sign below £131,072 on a grid of 2^-20, so that
# float64 sums of up to eight of them, in pence, are exact.
grid_amounts = st.integers(-(2**37) + 1, 2**37 - 1).map(
    lambda units: float(np.float32(units / 2**20))
)
sums_of_amounts = st.recursive(
    grid_amounts,
    lambda items: st.lists(items, min_size=1, max_size=4),
    max_leaves=8,
).filter(lambda tree: isinstance(tree, list))


@settings(max_examples=500, deadline=None, derandomize=True)
@given(tree=sums_of_amounts)
# Cancellation: the amounts are far larger than the total.
@example(tree=[65_536.01, -65_536.0, 0.01])
@example(tree=[[131_071.99, 0.01], [-131_071.99, [-0.01, 0.03]]])
@example(tree=[[1.0, 2.0**-20, 2.0**-20], [-1.0, 2.0**-20]])
def test_float32_sums_lie_within_the_tolerance_of_the_exact_sum(tree):
    total, read = _float32_sum(tree)
    # Every level was accepted as a sum, so the exact sum is returned.
    assert read.count == _leaves(tree), (tree, float(total))
    assert Fraction(float(read.pence)) == _exact(tree) * 100, (tree, float(total))


def test_sums_of_whole_pence_are_recovered():
    rng = np.random.default_rng(2541)
    missed_by_stored_pence = 0
    for shape in ([1], [2], [5], [2, 3], [1, 4, 2]):
        # Whole-pence amounts of either sign below £131,072, in groups of the
        # sizes ``shape`` lists, each group summed and the groups' sums added.
        groups = [
            [rng.integers(1 - LIMIT_PENCE, LIMIT_PENCE, 200_000) for _ in range(size)]
            for size in shape
        ]
        group_totals, group_sums = [], []
        for group in groups:
            amounts = [(pence / 100).astype(np.float32) for pence in group]
            group_total = reduce(np.add, amounts)
            group_totals.append(group_total)
            group_sums.append(summed(group_total, [stored(a) for a in amounts]))
        total = reduce(np.add, group_totals)
        exact = sum(sum(group) for group in groups)
        assert np.array_equal(summed(total, group_sums).pence, exact), shape
        missed_by_stored_pence += int(np.sum(stored_pence(total) != exact))
    # Summing in float32 leaves some totals too far from their pence for
    # stored_pence alone, which is why the parts are summed again.
    assert missed_by_stored_pence > 0


@settings(max_examples=200, deadline=None, derandomize=True)
@given(
    parts=st.lists(st.integers(0, 199_999), min_size=1, max_size=5),
    entered=st.integers(0, 999_999),
)
# £1,000 entered as a pension total, with no programme amounts.
@example(parts=[0, 0], entered=100_000)
# A penny from the sum of the amounts.
@example(parts=[180_749, 143_515], entered=324_265)
def test_a_total_that_is_not_the_sum_is_read_as_stored(parts, entered):
    """Amounts under £2,000, five at most: the rounding of their sum is under
    half a penny, so a total a whole penny or more from it is not the sum."""
    amounts = [np.float32(p / 100) for p in parts]
    read = [stored(amount) for amount in amounts]
    assert summed(np.float32(entered / 100), read).pence == entered
    assert summed(reduce(np.add, amounts), read).pence == sum(parts)


def _months(amounts):
    """Twelve float32 monthly amounts, summed one month at a time in float32
    as policyengine-core sums a flow over a year, and read with
    months_summed."""
    return months_summed(reduce(np.add, amounts), [stored(m) for m in amounts])


def test_a_years_whole_pence_divided_among_its_months_are_recovered():
    for start in range(0, 32_768 * 100, 1_000_000):
        pence = np.arange(start, min(start + 1_000_000, 32_768 * 100))
        # policyengine-core's set_input_divide_by_period: the year's float32
        # amount divided by twelve in float32, for each month.
        month = (pence / 100).astype(np.float32) / 12
        assert month.dtype == np.float32
        recovered = _months([month] * 12).pence
        wrong = np.nonzero(recovered != pence)[0]
        assert len(wrong) == 0, pence[wrong[:5]]


def test_whole_pence_entered_for_each_month_are_recovered():
    rng = np.random.default_rng(2541)
    pence = rng.integers(0, LIMIT_PENCE // 12, (12, 200_000))
    recovered = _months([(p / 100).astype(np.float32) for p in pence]).pence
    assert np.array_equal(recovered, pence.sum(axis=0))


# Float32 monthly amounts below £131,072 in all, on a grid of 2^-20 so that
# float64 sums of twelve of them, in pence, are exact.
monthly_amounts = st.integers(0, 2**37 // 12).map(
    lambda units: float(np.float32(units / 2**20))
)


def _step(amount):
    """The float32 step of the next float32 above ``amount``, in pounds."""
    return Fraction(
        float(np.spacing(np.nextafter(np.float32(amount), np.float32(np.inf))))
    )


@settings(max_examples=300, deadline=None, derandomize=True)
@given(months=st.lists(monthly_amounts, min_size=12, max_size=12))
# Twelve 10p months, which float32 sums to 1.2000002, more than half a step
# from £1.20.
@example(months=[0.1] * 12)
def test_moves_the_months_sum_only_to_a_whole_penny_within_their_rounding(months):
    amounts = [np.float32(m) for m in months]
    read = _months(amounts)
    exact = sum(Fraction(float(a)) for a in amounts) * 100
    result = Fraction(float(read.pence))
    if result != exact:
        steps = sum(_step(a) for a in amounts) + _step(sum(float(a) for a in amounts))
        assert result.denominator == 1 and abs(result - exact) <= steps * 100, (
            months,
            float(result),
            float(exact),
        )
