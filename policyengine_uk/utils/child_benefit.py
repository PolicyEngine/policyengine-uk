import numpy as np


def child_benefit_charge_share(
    income: np.ndarray, phase_out_start: float, phase_out_end: float
) -> np.ndarray:
    """Bound the charge share, treating nonpositive taper widths as a cliff."""
    income = np.asarray(income)
    width = phase_out_end - phase_out_start
    share = np.divide(
        np.maximum(income - phase_out_start, 0),
        width,
        out=np.asarray(income > phase_out_start, dtype=float),
        where=width > 0,
    )
    return np.clip(share, 0, 1)


def child_benefit_charge_percentage(
    income: np.ndarray, phase_out_start: float, phase_out_end: float
) -> np.ndarray:
    """The appropriate percentage of ITEPA 2003 s. 681C(2), as a fraction.

    One percentage point per hundredth of the phase-out band crossed (per £200
    from 2024-25), capped at 100 and rounded down to a whole number
    (s. 681C(3)(b)). Worked in float64, multiplying before dividing. With
    whole-pound band edges, an income on an exact step (exact in float32 too,
    below £16.7m) gives an integer-valued quotient, which IEEE division returns
    exactly, so no slack is added: slack would round a penny income just
    below a step up to it. A nonpositive band width is a cliff (100 points
    above the start).
    """
    income = np.asarray(income, dtype=np.float64)
    width = float(phase_out_end) - float(phase_out_start)
    excess = np.maximum(income - float(phase_out_start), 0)
    if width > 0:
        points = np.minimum(excess * 100 / width, 100)
    else:
        points = np.where(income > float(phase_out_start), 100.0, 0.0)
    return np.floor(points) / 100


def round_down_to_pounds(amount: np.ndarray) -> np.ndarray:
    """ITEPA 2003 s. 681C(3)(a): amounts not a whole number of pounds are
    rounded down. The amount is first taken to the nearest penny in float64,
    so that £4,199 stored as 4,198.9995 is not rounded down to £4,198, then
    to whole pounds by integer division of the pence. Child Benefit totals and
    charges are whole pence (weekly rates in pence, and whole percentage
    points of whole pounds), so the penny step loses nothing."""
    pence = np.round(np.asarray(amount, dtype=np.float64) * 100)
    return np.floor_divide(pence, 100)
