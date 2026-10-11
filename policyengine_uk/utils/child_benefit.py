import numpy as np

# Floating-point slack, so an exact whole number computed as 55.999999...
# is not rounded down to the number below.
ROUNDING_TOLERANCE = 1e-9


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

    The share of the phase-out band crossed is a percentage of one point per
    hundredth of the band (one point per £200 from 2024-25), which s. 681C(3)(b)
    rounds down to a whole number.
    """
    share = child_benefit_charge_share(income, phase_out_start, phase_out_end)
    return np.floor(share * 100 + ROUNDING_TOLERANCE) / 100


def round_down_to_pounds(amount: np.ndarray) -> np.ndarray:
    """ITEPA 2003 s. 681C(3)(a): amounts not a whole number of pounds are
    rounded down."""
    return np.floor(np.asarray(amount) + ROUNDING_TOLERANCE)
