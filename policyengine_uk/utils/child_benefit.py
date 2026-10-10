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
