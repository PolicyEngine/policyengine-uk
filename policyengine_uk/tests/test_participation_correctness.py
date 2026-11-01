"""Participation contracts; controlled incentives are not population predictions."""

from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

from policyengine_uk import Microsimulation, Simulation
from policyengine_uk.dynamics import participation as p
from policyengine_uk.model_api import WEEKS_IN_YEAR


class PeriodSimulation:
    """Small mutable simulation protocol, with observable cash and year storage."""

    def __init__(self, pay, *, default=2025, roles=None, dtype=np.float32):
        n = len(pay)
        self.default = default
        self.baseline = None
        self.pay = {year: pd.Series(pay, dtype=dtype) for year in (2025, 2027)}
        self.hours = {
            year: pd.Series(np.where(np.array(pay) > 0, 1000, 0), dtype=dtype)
            for year in (2025, 2027)
        }
        self.roles = roles or {year: np.ones(n, dtype=int) for year in (2025, 2027)}
        self.populations = {"benunit": SimpleNamespace(members_entity_id=np.arange(n))}

    def calculate(self, name, period=None, **kwargs):
        year = period or self.default
        if name == "employment_income":
            return self.pay[year].copy()
        if name == "hours_worked":
            return self.hours[year].copy()
        if name == "adult_index":
            return pd.Series(self.roles[year])
        if name == "household_net_income":
            return pd.Series(np.repeat(500 + self.pay[year].sum(), len(self.pay[year])))
        if name == "household_weight":
            return pd.Series(np.ones(len(self.pay[year])))
        raise AssertionError(name)

    def set_input(self, name, year, values):
        target = self.pay if name == "employment_income" else self.hours
        target[year] = pd.Series(np.asarray(values), dtype=target[year].dtype)

    def reset_calculations(self):
        pass


def controlled(
    monkeypatch,
    pay,
    elasticities,
    changes,
    *,
    excluded=None,
    imputed=None,
    dtype=np.float32,
):
    """Hold incentives fixed while executing the real response/bin/draw/writeback API."""
    sim = PeriodSimulation(pay, dtype=dtype)
    sim.baseline = PeriodSimulation(pay, dtype=dtype)
    n = len(pay)
    elasticities = np.asarray(elasticities, dtype=float)
    changes = np.asarray(changes, dtype=float)
    if excluded is None:
        excluded = np.zeros(n, dtype=bool)
    if imputed is None:
        imputed = np.repeat(5000.123456, n)
    from policyengine_uk.dynamics import labour_supply

    monkeypatch.setattr(
        labour_supply,
        "calculate_excluded_from_labour_supply_responses",
        lambda *args: np.asarray(excluded),
    )
    monkeypatch.setattr(p, "calculate_earnings_quintile", lambda *args: np.ones(n))
    monkeypatch.setattr(
        p,
        "calculate_participation_elasticities",
        lambda sim, quintile, year=None: elasticities.copy(),
    )
    monkeypatch.setattr(
        p, "impute_wages_for_nonworkers", lambda *args: np.asarray(imputed)
    )

    def gain(source, *args, **kwargs):
        return pd.DataFrame(
            {
                "gain_to_work": 100 * (1 + changes)
                if source is sim
                else np.repeat(100.0, n),
                "in_work_income": np.repeat(100.0, n),
                "out_of_work_income": np.zeros(n),
            }
        )

    monkeypatch.setattr(p, "calculate_gain_to_work", gain)
    return sim


def test_requested_year_changes_real_parent_elasticity_and_cash(monkeypatch):
    """Real public-input Simulation, isolated hypothetical loss of work incentive."""
    sim = Microsimulation(
        situation={
            "people": {
                "parent": {
                    "age": {"2025": 40, "2027": 42},
                    "gender": "FEMALE",
                    "employment_income": {"2025": 20000, "2027": 20000},
                    "hours_worked": {"2025": 1000, "2027": 1000},
                },
                "child": {"age": {"2025": 2, "2027": 4}},
            },
            "benunits": {"family": {"members": ["parent", "child"]}},
            "households": {"home": {"members": ["parent", "child"]}},
        },
        reform={"gov.hmrc.income_tax.rates.uk[0].rate": {"2027": 0.19}},
    )

    def gain(source, *args, **kwargs):
        return pd.DataFrame(
            {
                "gain_to_work": [0.0, 0.0] if source is sim else [100.0, 100.0],
                "in_work_income": [100.0, 100.0],
                "out_of_work_income": [0.0, 0.0],
            }
        )

    monkeypatch.setattr(p, "calculate_gain_to_work", gain)
    result = p.apply_participation_responses(sim, 2027, count_adults=1, random_seed=10)
    assert result["participation_elasticity"].iloc[0] == pytest.approx(0.932)
    assert result["new_employment_income"].iloc[0] == 0
    assert sim.calculate("hours_worked", 2027).iloc[0] == 0
    assert sim.calculate("employment_income", 2025).iloc[0] == 20000
    assert np.asarray(sim.baseline.calculate("employment_income", 2027))[0] == 20000


@pytest.mark.parametrize("outlier", [10.0, -10.0])
def test_excluded_people_cannot_move_eligible_bins_or_surplus(monkeypatch, outlier):
    sim = controlled(monkeypatch, [100, 0, 100], [0.1, 0.2, 0.3], [0.5, 0, 0])
    before = p.apply_participation_responses(sim, 2025)
    sim = controlled(
        monkeypatch,
        [100, 0, 100, 999],
        [0.1, 0.2, 0.3, outlier],
        [0.5, 0, 0, 100],
        excluded=[False, False, False, True],
    )
    after = p.apply_participation_responses(sim, 2025)
    for name in (
        "elasticity_group",
        "surplus_participation_change",
        "participation_change",
        "new_employment_income",
        "participation_response",
    ):
        np.testing.assert_array_equal(after[name], before[name])
    np.testing.assert_array_equal(before["surplus_participation_change"], [0, 0, 0])
    assert sim.pay[2025].iloc[3] == 999
    assert sim.hours[2025].iloc[3] == 1000


def test_response_preserves_global_numpy_random_state(monkeypatch):
    sim = controlled(monkeypatch, [100, 0], [0.1, 0.2], [0, 0])
    original = np.random.get_state()
    try:
        np.random.seed(987)
        state = np.random.get_state()
        p.apply_participation_responses(sim, 2025, random_seed=42)
        after = np.random.get_state()
        assert state[0] == after[0]
        np.testing.assert_array_equal(state[1], after[1])
        assert state[2:] == after[2:]
    finally:
        np.random.set_state(original)


def test_requested_year_adult_role_controls_gain_and_restores_income():
    sim = PeriodSimulation([100, 0], roles={2025: [0, 1], 2027: [1, 0]})
    result = p.calculate_gain_to_work(
        sim, 2027, count_adults=1, impute_nonworker_wages=False
    )
    np.testing.assert_array_equal(result["gain_to_work"], [100, 0])
    np.testing.assert_array_equal(sim.pay[2027], [100, 0])
    np.testing.assert_array_equal(sim.pay[2025], [100, 0])


@pytest.mark.parametrize("seed", [0, 1, 42, 123])
@pytest.mark.parametrize("dtype", [np.float32, np.float64])
def test_local_draws_match_independent_legacy_loop_and_hours(monkeypatch, seed, dtype):
    pay = np.array([100, 0, 200, 0, 300, 0, 400, 0], dtype=dtype)
    hours = np.where(pay > 0, 1000, 0).astype(dtype)
    elasticities = np.arange(1, 9) / 10
    change = np.array([0, 1, -1, 0.5, -0.25, 2, 0, 1.0])
    imputed = np.array([0, 5000.123456, 0, 6000.321987, 0, 0, 0, -1.0])
    sim = controlled(
        monkeypatch,
        pay,
        elasticities,
        change / elasticities,
        imputed=imputed,
        dtype=dtype,
    )
    expected = pay.copy()
    flags = np.zeros(len(pay), dtype=bool)
    rng = np.random.RandomState(seed)
    # Independent scalar reference preserves the historical candidate draw order,
    # including zero probabilities and wages that cannot produce entry.
    for index, income in enumerate(pay):
        if income > 0:
            if rng.random_sample() < max(0, -change[index]):
                expected[index] = 0
                flags[index] = True
    for index, income in enumerate(pay):
        if income == 0:
            if rng.random_sample() < max(0, change[index]) and imputed[index] > 0:
                expected[index] = dtype(imputed[index])
                flags[index] = True
    expected_hours = hours.copy()
    expected_hours[(pay == 0) & (expected > 0)] = 977.6
    expected_hours[(pay > 0) & (expected == 0)] = 0
    assert WEEKS_IN_YEAR == 52
    result = p.apply_participation_responses(sim, 2025, random_seed=seed)
    np.testing.assert_allclose(
        result["direct_participation_change"], change, rtol=0, atol=1e-15
    )
    np.testing.assert_array_equal(result["surplus_participation_change"], np.zeros(8))
    np.testing.assert_array_equal(sim.pay[2025], expected)
    np.testing.assert_array_equal(result["participation_response"], flags)
    np.testing.assert_array_equal(sim.hours[2025], expected_hours)
    assert sim.pay[2025].dtype == np.dtype(dtype)
    np.testing.assert_array_equal(sim.baseline.pay[2025], pay)


def test_no_baseline_is_an_early_noop():
    sim = PeriodSimulation([100, 0])
    assert p.apply_participation_responses(sim, 2027).empty
    np.testing.assert_array_equal(sim.pay[2027], [100, 0])


def test_no_eligible_people_and_constant_bins_are_safe(monkeypatch):
    sim = controlled(monkeypatch, [100, 0], [0.2, 0.2], [1, -1], excluded=[True, True])
    assert p.apply_participation_responses(sim, 2025).empty
    np.testing.assert_array_equal(sim.pay[2025], [100, 0])
    sim = controlled(monkeypatch, [100, 0], [0.2, 0.2], [0, 0])
    result = p.apply_participation_responses(sim, 2025)
    assert result["elasticity_group"].nunique() == 1
    np.testing.assert_array_equal(result["participation_change"], [0, 0])


def test_omitted_year_retains_default_elasticity_contract():
    sim = Simulation(
        situation={
            "people": {"adult": {"age": 40, "gender": "MALE"}},
            "benunits": {"b": {"members": ["adult"]}},
            "households": {"h": {"members": ["adult"]}},
        }
    )
    np.testing.assert_array_equal(
        p.calculate_participation_elasticities(sim, np.array([3])), [0.136]
    )


@pytest.mark.parametrize("year, expected", [(2025, 0.453), (2027, 0.589)])
def test_cohabiting_parent_uses_requested_year_and_couple_group(year, expected):
    """Retain #2445 couple grouping and #1836 explicit-year demographics together.

    Existing OBR Table A1 third-quintile matrix: working-partner mothers use
    0.453 at child age2 and0.589 at age4. These are engineering routing oracles.
    """
    sim = Microsimulation(
        situation={
            "people": {
                "mother": {
                    "age": {"2025": 40, "2027": 42},
                    "gender": "FEMALE",
                    "employment_income": {"2025": 20000, "2027": 20000},
                },
                "partner": {
                    "age": {"2025": 40, "2027": 42},
                    "gender": "MALE",
                    "employment_income": {"2025": 25000, "2027": 25000},
                },
                "child": {"age": {"2025": 2, "2027": 4}},
            },
            "benunits": {
                "family": {
                    "members": ["mother", "partner", "child"],
                    "is_married": {"2025": False, "2027": False},
                }
            },
            "households": {"home": {"members": ["mother", "partner", "child"]}},
        }
    )
    assert sim.calculate("is_couple", year).iloc[0]
    assert not sim.calculate("is_married", year).iloc[0]
    actual = p.calculate_participation_elasticities(sim, np.array([3, 3, 3]), year)
    assert actual[0] == pytest.approx(expected)
