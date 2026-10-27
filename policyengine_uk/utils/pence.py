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
