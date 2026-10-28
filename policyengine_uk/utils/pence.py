"""Sums of money as the model stores them, in pence.

The model stores amounts of money in float32, which holds most of them only
to within half a float32 step: £10,608.52 is stored as 10,608.51953125. Rules
that turn on a single penny, such as Carer's Allowance's earnings limit, need
the amount that was entered, not the nearest float32.
"""

import numpy as np


def stored_pence(amount):
    """``amount``, stored in float32, in pence as float64: the whole number of
    pence it was entered as, where it lies within half a float32 step of one,
    and otherwise its exact value.

    An amount entered in whole pence is stored within half a step of them.
    Below £131,072 a step is under a penny, so no other whole number of pence
    lies that close, and the pence are recovered exactly. An amount with a
    fraction of a penny keeps it, to be rounded as the rule requires, unless
    the fraction is within half a step of a whole penny, which float32 cannot
    tell apart from that penny.
    """
    amount = np.asarray(amount, dtype=np.float32)
    # Float32 has 24 significant bits, so multiplying by 100 in float64 is
    # exact, as are the difference and the half step below.
    pence = amount.astype(np.float64) * 100
    whole = np.round(pence)
    half_step = np.spacing(np.abs(amount)).astype(np.float64) * 50
    return np.where(np.abs(pence - whole) <= half_step, whole, pence)


def stored_sum_pence(total, parts):
    """``total``, a float32 sum of the float32 amounts ``parts``, in pence as
    float64: the sum of the parts' stored_pence, where ``total`` lies within
    float32 rounding of it, and otherwise stored_pence(total), for a total
    entered directly rather than summed.

    Summing in float32 rounds at each addition, so a sum of whole-pence
    amounts can lie more than half a step from its pence even when each part
    is recovered exactly; summing the parts' pence in float64 is exact. Each
    addition moves a sum of amounts no larger than it by at most half a step
    of the total, and each part lies within half a step of its own pence, so
    a sum of n parts lies within n steps of the parts' pence.
    """
    total = np.asarray(total, dtype=np.float32)
    exact = sum(stored_pence(part) for part in parts)
    tolerance = np.spacing(np.abs(total)).astype(np.float64) * 100 * len(parts)
    summed = np.abs(total.astype(np.float64) * 100 - exact) <= tolerance
    return np.where(summed, exact, stored_pence(total))
