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
    assert weighted_median(np.array([5.0, 9.0]), np.array([0.0, 0.0])) == 0.0
    assert weighted_median(np.array([1.0, 2.0, 3.0]), np.array([1.0, 1.0, 1.0])) == 2.0


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


def test_quintiles_cover_adults_in_equal_shares():
    sim = make_sim()
    quintile = calculate_earnings_quintile(sim, 2025)
    adults = sim.calculate("adult_index") > 0

    counts = [((quintile == q) & adults).sum() for q in range(1, 6)]
    # 80 adults over five quintiles, split evenly despite the tied mass of
    # non-workers all sharing one imputed value.
    assert counts == [16, 16, 16, 16, 16]


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
