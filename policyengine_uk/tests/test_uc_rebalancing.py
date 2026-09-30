import numpy as np
import pytest

import policyengine_uk.scenarios.uc_reform as uc_reform
from policyengine_uk import Simulation

YEARS = range(2025, 2036)


def _uc_claimant(age_2025: int) -> dict:
    return {
        "people": {
            "person": {
                "age": {year: age_2025 + year - 2025 for year in YEARS},
                "employment_income": {year: 0 for year in YEARS},
                "uc_limited_capability_for_WRA": {year: True for year in YEARS},
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


def _benefit_uprating_factor(sim: Simulation, year: int) -> float:
    parameters = sim.tax_benefit_system.parameters
    current_index = float(parameters(str(year)).gov.benefit_uprating_cpi)
    baseline_index = float(parameters("2025").gov.benefit_uprating_cpi)
    return current_index / baseline_index


def _rebalanced_standard_allowance_monthly(
    sim: Simulation, year: int, claimant_type: str
) -> float:
    current = sim.tax_benefit_system.parameters(str(year))
    return float(
        current.gov.dwp.universal_credit.standard_allowance.amount[claimant_type]
    )


def _cpi_protected_uc_award_monthly(
    sim: Simulation, year: int, claimant_type: str
) -> float:
    baseline = sim.tax_benefit_system.parameters("2025").gov.dwp.universal_credit
    baseline_standard_allowance = float(
        baseline.standard_allowance.amount[claimant_type]
    )
    baseline_health_element = float(baseline.elements.disabled.amount)
    return _benefit_uprating_factor(sim, year) * (
        baseline_standard_allowance + baseline_health_element
    )


@pytest.mark.parametrize("age_2025", [20, 30])
def test_existing_claimants_keep_combined_award_cpi_protected(monkeypatch, age_2025):
    """Universal Credit Act 2025 s4(2): for every standard allowance, standard
    allowance plus the protected LCWRA amount keeps pace with September CPI.
    Regulation 36 has one protected amount, so claimants of every age get
    the same amount and the combined award is at least the CPI path."""
    _force_uc_seed(monkeypatch, [0.99])
    sim = Simulation(situation=_uc_claimant(age_2025))
    claimant_type = "SINGLE_YOUNG" if age_2025 < 25 else "SINGLE_OLD"

    for year in range(2026, 2030):
        standard_allowance = sim.calculate("uc_standard_allowance", year)[0] / 12
        health_element = sim.calculate("uc_LCWRA_element", year)[0] / 12
        new_claimant_health_element = float(
            sim.tax_benefit_system.parameters(
                str(year)
            ).gov.dwp.universal_credit.rebalancing.new_claimant_health_element
        )

        assert health_element > new_claimant_health_element
        assert health_element == pytest.approx(
            uc_reform._protected_existing_health_element_monthly(sim, year)
        )
        assert standard_allowance + health_element >= (
            _cpi_protected_uc_award_monthly(sim, year, claimant_type) - 1e-6
        )


def test_protected_amount_never_falls_and_resumes_cpi_uprating_in_2030():
    """s3 freezes the amount (it cannot fall) to 2029-30; section 150
    uprating resumes from April 2030."""
    sim = Simulation(situation=_uc_claimant(30))
    protected = {
        year: uc_reform._protected_existing_health_element_monthly(sim, year)
        for year in range(2026, 2036)
    }
    for year in range(2027, 2036):
        assert protected[year] >= protected[year - 1]
    for year in range(2030, 2036):
        assert protected[year] / protected[year - 1] == pytest.approx(
            _benefit_uprating_factor(sim, year)
            / _benefit_uprating_factor(sim, year - 1)
        )


def test_existing_claimants_stay_protected_after_2029_30(monkeypatch):
    """No cliff in April 2030: pre-2026 claimants keep the protected amount,
    uprated by September CPI, rather than falling to the new-claimant rate."""
    _force_uc_seed(monkeypatch, [0.99])
    sim = Simulation(situation=_uc_claimant(30))
    for year in (2030, 2031, 2035):
        health_element = sim.calculate("uc_LCWRA_element", year)[0] / 12
        assert health_element == pytest.approx(
            uc_reform._protected_existing_health_element_monthly(sim, year)
        )
        assert health_element > 400


def test_new_claimants_use_fixed_health_element(monkeypatch):
    _force_uc_seed(monkeypatch, [0.0])
    sim = Simulation(situation=_uc_claimant(30))

    for year in (2026, 2027, 2028, 2029, 2030, 2033):
        health_element = sim.calculate("uc_LCWRA_element", year)[0] / 12
        expected_health = float(
            sim.tax_benefit_system.parameters(
                str(year)
            ).gov.dwp.universal_credit.rebalancing.new_claimant_health_element
        )

        assert health_element == pytest.approx(expected_health)


def test_standard_allowance_reforms_still_change_standard_allowance(monkeypatch):
    _force_uc_seed(monkeypatch, [0.99])
    baseline = Simulation(situation=_uc_claimant(30))
    reformed = Simulation(
        situation=_uc_claimant(30),
        reform={
            "gov.dwp.universal_credit.standard_allowance.amount.SINGLE_OLD": {
                "2025-01-01.2100-12-31": 800
            }
        },
    )

    baseline_standard_allowance = baseline.calculate("uc_standard_allowance", 2026)[0]
    reformed_standard_allowance = reformed.calculate("uc_standard_allowance", 2026)[0]

    assert reformed_standard_allowance / baseline_standard_allowance > 1.5
