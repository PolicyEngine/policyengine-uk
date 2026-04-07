import numpy as np
import pytest

import policyengine_uk.scenarios.uc_reform as uc_reform
from policyengine_uk import Simulation

BASELINE_YEAR = 2025


def _uc_claimant(age: int) -> dict:
    return {
        "people": {
            "person": {
                "age": {year: age for year in range(2025, 2030)},
                "employment_income": {year: 0 for year in range(2025, 2030)},
                "uc_limited_capability_for_WRA": {
                    year: True for year in range(2025, 2030)
                },
            }
        },
        "benunits": {"benunit": {"members": ["person"]}},
        "households": {"household": {"members": ["person"]}},
    }


class _FixedRng:
    def __init__(self, values):
        self.values = np.array(values, dtype=float)

    def random(self, size):
        assert size == len(self.values)
        return self.values


def _force_uc_seed(monkeypatch, values):
    monkeypatch.setattr(
        uc_reform.np.random, "default_rng", lambda seed: _FixedRng(values)
    )


def _cpi_protected_uc_award_monthly(
    sim: Simulation, year: int, claimant_type: str
) -> float:
    parameters = sim.tax_benefit_system.parameters
    baseline = parameters(str(BASELINE_YEAR))
    current = parameters(str(year))
    cpi_factor = float(current.gov.benefit_uprating_cpi) / float(
        baseline.gov.benefit_uprating_cpi
    )
    baseline_standard_allowance = float(
        baseline.gov.dwp.universal_credit.standard_allowance.amount[claimant_type]
    )
    baseline_health_element = float(
        baseline.gov.dwp.universal_credit.elements.disabled.amount
    )
    return (baseline_standard_allowance + baseline_health_element) * cpi_factor


def _rebalanced_standard_allowance_monthly(
    sim: Simulation, year: int, claimant_type: str
) -> float:
    current = sim.tax_benefit_system.parameters(str(year))
    return float(
        current.gov.dwp.universal_credit.standard_allowance.amount[claimant_type]
    ) * (
        1
        + float(current.gov.dwp.universal_credit.rebalancing.standard_allowance_uplift)
    )


def test_existing_single_over_25_claimant_combined_award_tracks_cpi(monkeypatch):
    _force_uc_seed(monkeypatch, [0.99])
    sim = Simulation(situation=_uc_claimant(30))

    for year in range(2026, 2030):
        standard_allowance = sim.calculate("uc_standard_allowance", year)[0] / 12
        health_element = sim.calculate("uc_LCWRA_element", year)[0] / 12
        expected_total = _cpi_protected_uc_award_monthly(sim, year, "SINGLE_OLD")
        expected_health = expected_total - _rebalanced_standard_allowance_monthly(
            sim, year, "SINGLE_OLD"
        )

        assert standard_allowance + health_element == pytest.approx(expected_total)
        assert health_element == pytest.approx(expected_health)


def test_existing_single_under_25_claimant_gets_extra_topup(monkeypatch):
    _force_uc_seed(monkeypatch, [0.99])
    sim = Simulation(situation=_uc_claimant(22))

    for year in range(2026, 2030):
        standard_allowance = sim.calculate("uc_standard_allowance", year)[0] / 12
        health_element = sim.calculate("uc_LCWRA_element", year)[0] / 12
        expected_total = _cpi_protected_uc_award_monthly(sim, year, "SINGLE_YOUNG")
        baseline_rebalanced_standard_allowance = _rebalanced_standard_allowance_monthly(
            sim, year, "SINGLE_YOUNG"
        )

        assert standard_allowance + health_element == pytest.approx(expected_total)
        assert standard_allowance > baseline_rebalanced_standard_allowance


def test_new_claimants_use_fixed_health_element(monkeypatch):
    _force_uc_seed(monkeypatch, [0.0])
    sim = Simulation(situation=_uc_claimant(30))

    for year in range(2026, 2030):
        health_element = sim.calculate("uc_LCWRA_element", year)[0] / 12
        expected_health = float(
            sim.tax_benefit_system.parameters(
                str(year)
            ).gov.dwp.universal_credit.rebalancing.new_claimant_health_element
        )

        assert health_element == pytest.approx(expected_health)
