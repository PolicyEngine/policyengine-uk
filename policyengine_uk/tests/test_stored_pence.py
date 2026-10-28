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

stored_sum_pence: a float32 sum of float32 amounts, in pence.

5. Sums recovered: a float32 sum of up to five whole-pence amounts, added
   one at a time as policyengine-core's ``adds`` does, comes back as exactly
   the sum of their pence while it is below £131,072, including sums that
   stored_pence alone would not recover.
6. Entered totals kept: a total that is not a float32 sum of the parts, as
   when it is entered directly, comes back as stored_pence(total).
"""

from fractions import Fraction
from functools import reduce

import numpy as np
from hypothesis import example, given, settings
from hypothesis import strategies as st

from policyengine_uk.utils.pence import stored_pence, stored_sum_pence

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


def _float32_sum(parts):
    """Parts in pence, stored and added one at a time in float32."""
    stored = [(np.asarray(p) / 100).astype(np.float32) for p in parts]
    return reduce(np.add, stored), stored


def test_sums_of_whole_pence_are_recovered():
    rng = np.random.default_rng(2541)
    missed_by_stored_pence = 0
    for count in range(1, 6):
        # Up to five parts whose sum is below £131,072.
        parts = [rng.integers(0, LIMIT_PENCE // count, 400_000) for _ in range(count)]
        total, stored = _float32_sum(parts)
        exact = sum(parts)
        assert np.array_equal(stored_sum_pence(total, stored), exact), count
        missed_by_stored_pence += int(np.sum(stored_pence(total) != exact))
    # Summing in float32 leaves some totals too far from their pence for
    # stored_pence alone, which is why the parts are summed again.
    assert missed_by_stored_pence > 0


@settings(max_examples=200, deadline=None, derandomize=True)
@given(
    parts=st.lists(st.integers(0, LIMIT_PENCE // 5 - 1), min_size=1, max_size=5),
    entered=st.integers(0, LIMIT_PENCE - 1),
)
# £1,000 entered as a pension total, with no programme amounts.
@example(parts=[0, 0], entered=100_000)
def test_a_total_entered_directly_is_read_as_entered(parts, entered):
    total, stored = _float32_sum([[p] for p in parts])
    entered_total = np.array([entered / 100], dtype=np.float32)
    result = stored_sum_pence(entered_total, stored)
    if abs(entered - sum(parts)) <= len(parts):
        # Within float32 rounding of the parts' sum (a penny for each part
        # here, far less below £131,072): read as that sum.
        assert result[0] in (entered, sum(parts))
    else:
        assert result[0] == entered
    assert stored_sum_pence(total, stored)[0] == sum(parts)
