"""Deterministic pseudo-random draws for stochastic variable assignment.

Draws are pure functions of entity ids, so results are reproducible across
runs and machines, and datasets can override them by providing the draw
variable directly.
"""

import numpy as np


def splitmix64_uniform(ids: np.ndarray, salt: int = 0) -> np.ndarray:
    """Map integer ids to deterministic uniform draws on [0, 1).

    Uses the splitmix64 finalizer, which passes standard statistical tests
    for avalanche behavior. Different salts give independent streams.
    """
    with np.errstate(over="ignore"):
        z = ids.astype(np.uint64) + np.uint64(salt) * np.uint64(0x632BE59BD9B4E019)
        z = z + np.uint64(0x9E3779B97F4A7C15)
        z = (z ^ (z >> np.uint64(30))) * np.uint64(0xBF58476D1CE4E5B9)
        z = (z ^ (z >> np.uint64(27))) * np.uint64(0x94D049BB133111EB)
        z = z ^ (z >> np.uint64(31))
    return z.astype(np.float64) / 2.0**64
