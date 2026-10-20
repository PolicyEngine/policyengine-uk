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
    # Use the top 53 bits so the result is exactly representable, and clamp
    # below the largest float32 under 1: model variables store as float32,
    # which would otherwise round near-1 draws up to exactly 1.0.
    draws = (z >> np.uint64(11)).astype(np.float64) / 2.0**53
    return np.minimum(draws, 1.0 - 2.0**-24)


def stratified_uniform(
    strata: np.ndarray, draws: np.ndarray, weights: np.ndarray
) -> np.ndarray:
    """Spread records evenly over [0, 1) within each stratum, by weight.

    Records in a stratum are ordered by their draw and each is placed at the
    midpoint of its slice of the stratum's cumulative weight. The weighted
    distribution within every stratum is then uniform to within the largest
    single weight, rather than only in expectation as with independent draws.
    The result does not depend on the order of the records. A stratum with no
    positive weight keeps the draws.
    """
    strata = np.asarray(strata)
    draws = np.asarray(draws, dtype=np.float64)
    weights = np.maximum(np.asarray(weights, dtype=np.float64), 0)
    order = np.lexsort((draws, strata))
    _, group = np.unique(strata[order], return_inverse=True)
    sorted_weights = weights[order]
    totals = np.bincount(group, weights=sorted_weights)
    group_starts = np.concatenate([[0.0], np.cumsum(totals)[:-1]])
    within = np.cumsum(sorted_weights) - group_starts[group] - sorted_weights / 2
    group_totals = totals[group]
    positions = np.where(
        group_totals > 0,
        within / np.where(group_totals > 0, group_totals, 1),
        draws[order],
    )
    result = np.empty_like(positions)
    result[order] = positions
    return np.clip(result, 0, 1.0 - 2.0**-24)
