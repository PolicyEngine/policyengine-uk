"""Tests for the participation module's earnings quintiles and wage imputation.

`calculate_earnings_quintile` previously ranked every person in the dataset,
children included, on *actual* earnings. Over half that population has no
earnings, so the bottom two quintiles were entirely non-earners and about a
quarter of each lower quintile were children.

That had two consequences. The OBR Table A1 elasticities are indexed by this
quintile and rise steeply as the quintile falls, so every potential entrant was
placed near the top of the table. And because `impute_wages_for_nonworkers`
drew its donors from the same elasticity groups, the lowest quintiles had no
employed donors at all and their non-workers were imputed a wage of zero — which
silently bars someone from entering employment in
`apply_participation_responses`, whatever the reform.
"""

import numpy as np
import pytest

from policyengine_uk.dynamics.participation import (
    calculate_earnings_quintile,
    impute_wages_for_nonworkers,
    weighted_median,
)
from policyengine_uk.model_api import WEEKS_IN_YEAR


class FakeSimulation:
    """Minimal stand-in exposing the variables these functions read."""

    def __init__(
        self, employment_income, hours_worked, age, gender, adult_index, weight
    ):
        self._values = {
            "employment_income": np.array(employment_income, dtype=float),
            "hours_worked": np.array(hours_worked, dtype=float),
            "age": np.array(age, dtype=float),
            "gender": np.array(gender),
            "adult_index": np.array(adult_index, dtype=float),
            "household_weight": np.array(weight, dtype=float),
        }

    def calculate(self, variable, period=None, **kwargs):
        return self._values[variable]


def make_sim(n_workers=40, n_nonworkers=40, n_children=40):
    """A population of workers, non-working adults and children."""
    annual_hours = 37.5 * WEEKS_IN_YEAR
    earnings = list(np.linspace(15_000, 90_000, n_workers))
    return FakeSimulation(
        employment_income=earnings + [0.0] * (n_nonworkers + n_children),
        hours_worked=[annual_hours] * n_workers + [0.0] * (n_nonworkers + n_children),
        age=[40] * (n_workers + n_nonworkers) + [5] * n_children,
        gender=["FEMALE"] * (n_workers + n_nonworkers + n_children),
        adult_index=[1] * (n_workers + n_nonworkers) + [0] * n_children,
        weight=[1.0] * (n_workers + n_nonworkers + n_children),
    )


def test_weighted_median_handles_empty_and_zero_weight_groups():
    assert weighted_median(np.array([]), np.array([])) == 0.0
    assert weighted_median(np.array([1.0, 2.0, 3.0]), np.array([1.0, 1.0, 1.0])) == 2.0
    # A zero-weight group falls back to the unweighted median rather than zero:
    # a zero wage silently bars entry into employment.
    assert weighted_median(np.array([5.0, 9.0]), np.array([0.0, 0.0])) == 7.0


def test_zero_weight_donors_still_yield_a_wage():
    # One worker carrying no weight, one non-worker. The donor group is
    # non-empty but weightless, so the weighted median is undefined.
    sim = FakeSimulation(
        employment_income=[40_000.0, 0.0],
        hours_worked=[37.5 * WEEKS_IN_YEAR, 0.0],
        age=[40, 40],
        gender=["FEMALE", "FEMALE"],
        adult_index=[1, 1],
        weight=[0.0, 1.0],
    )
    assert impute_wages_for_nonworkers(sim, 2025)[1] > 0


def test_quintiles_do_not_depend_on_row_order():
    """Placement must not vary with the order of rows in the dataset.

    Non-workers in a donor group share one imputed wage, so ranking a pooled
    distribution would split that tied mass across a quintile boundary and let
    serialisation order decide who falls on which side.
    """
    sim = make_sim()
    expected = calculate_earnings_quintile(sim, 2025)

    for seed in range(5):
        order = np.random.RandomState(seed).permutation(len(expected))
        shuffled = FakeSimulation(
            employment_income=sim.calculate("employment_income")[order],
            hours_worked=sim.calculate("hours_worked")[order],
            age=sim.calculate("age")[order],
            gender=sim.calculate("gender")[order],
            adult_index=sim.calculate("adult_index")[order],
            weight=sim.calculate("household_weight")[order],
        )
        restored = calculate_earnings_quintile(shuffled, 2025)[np.argsort(order)]
        assert (restored == expected).all()


def test_every_non_working_adult_gets_a_wage():
    # A zero imputed wage bars entry into employment, so it must not happen
    # merely because of how donors are grouped.
    sim = make_sim()
    imputed = impute_wages_for_nonworkers(sim, 2025)
    adults = sim.calculate("adult_index") > 0
    non_workers = adults & (sim.calculate("employment_income") == 0)

    assert (imputed[non_workers] > 0).all()


def test_imputed_earnings_are_a_plausible_part_time_wage():
    sim = make_sim()
    imputed = impute_wages_for_nonworkers(sim, 2025, hours_for_new_entrants=18.8)
    non_workers = (sim.calculate("adult_index") > 0) & (
        sim.calculate("employment_income") == 0
    )

    assert 10_000 < imputed[non_workers].mean() < 40_000


def test_workers_are_spread_evenly_across_quintiles():
    """Thresholds come from the worker earnings distribution, so workers split
    roughly evenly. Non-workers are then *placed* against those thresholds
    rather than ranked into them, so the adult population as a whole is not in
    equal fifths — the quintiles are of the earnings distribution."""
    sim = make_sim()
    quintile = calculate_earnings_quintile(sim, 2025)
    working = sim.calculate("employment_income") > 0

    counts = [((quintile == q) & working).sum() for q in range(1, 6)]
    assert all(6 <= count <= 10 for count in counts), counts
    assert sum(counts) == working.sum()


def test_no_quintile_is_left_without_earners():
    sim = make_sim()
    quintile = calculate_earnings_quintile(sim, 2025)
    adults = sim.calculate("adult_index") > 0
    working = sim.calculate("employment_income") > 0

    for q in range(1, 6):
        in_quintile = adults & (quintile == q)
        assert in_quintile.sum() > 0

    # The top quintiles must be earners; ranking on potential earnings must not
    # push every non-worker to the bottom regardless of earning capacity.
    assert (working & (quintile == 5)).sum() > 0


def test_children_are_not_ranked_among_adults():
    sim = make_sim()
    quintile = calculate_earnings_quintile(sim, 2025)
    children = sim.calculate("adult_index") == 0

    # Children are excluded from labour supply responses elsewhere; they must
    # not consume quintile space that belongs to the adult distribution.
    assert (quintile[children] == 1).all()


def test_handles_a_population_with_no_adults():
    sim = FakeSimulation([0.0], [0.0], [5], ["FEMALE"], [0], [1.0])
    assert calculate_earnings_quintile(sim, 2025).tolist() == [1]


def test_a_population_with_no_workers_is_not_all_top_quintile():
    """Thresholds come from observed earnings, so with no workers there are none.

    Falling through left every threshold at zero and placed every adult in the
    top quintile — the end of the OBR table with the smallest elasticities,
    which is the opposite of what a population of non-workers implies.
    """
    sim = FakeSimulation(
        employment_income=[0.0, 0.0, 0.0, 0.0],
        hours_worked=[0.0, 0.0, 0.0, 0.0],
        age=[30, 40, 50, 60],
        gender=["FEMALE", "MALE", "FEMALE", "MALE"],
        adult_index=[1, 1, 1, 1],
        weight=[1.0, 1.0, 1.0, 1.0],
    )
    quintile = calculate_earnings_quintile(sim, 2025)
    assert not (quintile == 5).all(), quintile.tolist()
    assert set(quintile.tolist()) <= {1, 2, 3, 4, 5}


def test_non_workers_are_placed_on_a_full_time_equivalent_basis():
    """Imputed earnings assume part-time hours; the thresholds do not.

    Placing a part-time figure against a distribution of observed earnings at
    whatever hours workers actually do pushes every non-worker down by roughly
    the hours ratio. Left uncorrected the imputed values all landed in one
    threshold interval, so no non-worker could reach the upper quintiles at all
    and the OBR table's variation went unexercised.
    """
    sim = make_sim()
    quintile = calculate_earnings_quintile(sim, 2025)
    non_workers = (sim.calculate("adult_index") > 0) & (
        sim.calculate("employment_income") == 0
    )

    # With donors spanning £15,000-£90,000 at full-time hours, a non-worker
    # imputed at the median wage belongs mid-distribution, not at the bottom.
    placed = set(quintile[non_workers].tolist())
    assert placed, "no non-workers to place"
    # The specific quintile matters, not merely that it is not 1 or 2: a
    # non-worker imputed at the median wage of donors spanning £15,000-£90,000
    # at full time belongs mid-distribution. Asserting only "not the bottom"
    # would pass on a placement that is still degenerate.
    assert placed <= {3, 4}, f"expected mid-distribution placement, got {placed}"


def test_weighted_quantiles_survives_degenerate_weights():
    from policyengine_uk.dynamics.participation import weighted_quantiles

    values = np.array([10.0, 20.0, 30.0, 40.0])
    quantiles = [0.2, 0.4, 0.6, 0.8]

    # All-zero weights previously returned all-zero thresholds, which places
    # every positive value in the top quintile — the lowest-elasticity end.
    zero_weighted = weighted_quantiles(values, np.zeros(4), quantiles)
    assert (zero_weighted > 0).all()
    assert (np.diff(zero_weighted) >= 0).all()

    assert (weighted_quantiles(np.array([]), np.array([]), quantiles) == 0).all()


def test_weighted_median_rejects_malformed_input():
    from policyengine_uk.dynamics.participation import weighted_median

    # np.argsort sorts NaN last, so without a guard a NaN wage would be returned
    # as the group maximum — silently imputing the highest wage in the group.
    # Non-finite pairs are dropped instead; this is a lower median, so [1, 3]
    # gives 1.0 rather than an interpolated 2.0.
    assert weighted_median(np.array([1.0, np.nan, 3.0]), np.ones(3)) == 1.0
    assert weighted_median(np.array([1.0, 2.0]), np.array([np.nan, 1.0])) == 2.0
    assert weighted_median(np.array([np.nan, np.nan]), np.ones(2)) == 0.0

    with pytest.raises(ValueError):
        weighted_median(np.array([1.0, 2.0]), np.ones(3))


def test_degenerate_distribution_placement_is_order_invariant():
    """Identical records must get identical quintiles.

    With no workers there is no earnings distribution, so every threshold is
    equal and placement falls to the degenerate branch. Spreading adults row by
    row through that branch sorted ties in input order, so permuting the rows
    changed who landed in which quintile — identical people drawing different
    OBR elasticities purely from serialisation order.
    """
    n = 10
    identical = FakeSimulation(
        employment_income=[0.0] * n,
        hours_worked=[0.0] * n,
        age=[40] * n,
        gender=["FEMALE"] * n,
        adult_index=[1] * n,
        weight=[1.0] * n,
    )
    placed = calculate_earnings_quintile(identical, 2025)
    assert set(placed.tolist()) == {3}, (
        "ten identical non-workers must all get the same quintile, "
        f"got {sorted(set(placed.tolist()))}"
    )


def test_degenerate_distribution_is_invariant_to_row_permutation():
    """Permuting the input must not move anyone between quintiles."""
    ages = [22, 35, 48, 61, 29, 44, 57, 33, 40, 26]
    genders = ["FEMALE", "MALE"] * 5
    n = len(ages)

    def build(order):
        return FakeSimulation(
            employment_income=[0.0] * n,
            hours_worked=[0.0] * n,
            age=[ages[i] for i in order],
            gender=[genders[i] for i in order],
            adult_index=[1] * n,
            weight=[1.0] * n,
        )

    order = list(range(n))
    base = calculate_earnings_quintile(build(order), 2025)

    shuffled_order = [7, 2, 9, 0, 4, 1, 8, 3, 6, 5]
    shuffled = calculate_earnings_quintile(build(shuffled_order), 2025)

    restored = np.empty_like(shuffled)
    for position, original in enumerate(shuffled_order):
        restored[original] = shuffled[position]

    assert np.array_equal(base, restored), (
        "quintile placement depends on row order: "
        f"{base.tolist()} vs {restored.tolist()}"
    )


def test_weighted_quantiles_aggregate_tied_values_by_weight():
    """Equal values must occupy one position however many rows carry them.

    Sorting rows and taking each row's own weight midpoint split a tied value
    across several positions, ordered by input row, so two equal-earning
    workers with unequal weights produced different thresholds depending on
    which appeared first — and could land either side of a quintile boundary.
    """
    from policyengine_uk.dynamics.participation import weighted_quantiles

    values = np.array([10_000.0, 10_000.0, 20_000.0, 30_000.0])
    quantiles = [0.2, 0.4, 0.6, 0.8]

    first = weighted_quantiles(values, np.array([1.0, 2.0, 1.0, 1.0]), quantiles)
    swapped = weighted_quantiles(values, np.array([2.0, 1.0, 1.0, 1.0]), quantiles)

    assert np.allclose(first, swapped), (
        f"thresholds depend on row order: {first} vs {swapped}"
    )


def test_tied_workers_with_unequal_weights_share_a_quintile():
    """Swapping the weights of two identical earners must not move anyone.

    Both rows earn the same, so between them the population is unchanged — only
    which row carries which weight differs. Under the row-sorted CDF the tied
    pair moved from quintile 1 to quintile 2 on that swap alone.
    """
    earnings = [10_000.0, 10_000.0, 15_000.0, 22_000.0, 22_000.0, 26_000.0, 40_000.0]
    weights = [1.0, 3.0, 2.0, 2.0, 2.0, 3.0, 2.0]
    n = len(earnings)
    annual_hours = 37.5 * WEEKS_IN_YEAR

    def build(w):
        return FakeSimulation(
            employment_income=earnings,
            hours_worked=[annual_hours] * n,
            age=[40] * n,
            gender=["FEMALE"] * n,
            adult_index=[1] * n,
            weight=w,
        )

    placed = calculate_earnings_quintile(build(weights), 2025)
    swapped_weights = [weights[1], weights[0]] + weights[2:]
    swapped = calculate_earnings_quintile(build(swapped_weights), 2025)

    assert placed[0] == placed[1], (
        f"identical earners split across quintiles: {placed[0]} vs {placed[1]}"
    )
    assert np.array_equal(placed, swapped), (
        "placement depends on which tied row carries the heavier weight: "
        f"{placed.tolist()} vs {swapped.tolist()}"
    )
