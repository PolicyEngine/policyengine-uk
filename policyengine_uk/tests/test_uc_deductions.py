"""Tests for Universal Credit deduction assignment and reform levers."""

import numpy as np
import pytest

from policyengine_uk import Simulation
from policyengine_uk.utils.stochastic import splitmix64_uniform

YEAR = 2025


def make_situation(**benunit_overrides):
    benunit = {
        "members": ["person"],
        "would_claim_uc": {YEAR: True},
        "universal_credit_pre_benefit_cap": {YEAR: 6_000},
        "benefit_cap_reduction": {YEAR: 0},
        **benunit_overrides,
    }
    return {
        "people": {"person": {"age": {YEAR: 30}}},
        "benunits": {"benunit": benunit},
        "households": {"household": {"members": ["person"]}},
    }


class TestSplitmixUniform:
    def test_deterministic(self):
        ids = np.arange(10_000)
        assert np.array_equal(splitmix64_uniform(ids), splitmix64_uniform(ids))

    def test_uniform_on_unit_interval(self):
        draws = splitmix64_uniform(np.arange(100_000))
        assert draws.min() >= 0
        assert draws.max() < 1
        assert abs(draws.mean() - 0.5) < 0.01
        # Deciles should each hold ~10% of draws.
        counts = np.histogram(draws, bins=10, range=(0, 1))[0]
        assert np.all(abs(counts / 100_000 - 0.1) < 0.01)

    def test_salts_give_independent_streams(self):
        ids = np.arange(100_000)
        a = splitmix64_uniform(ids, salt=0)
        b = splitmix64_uniform(ids, salt=1)
        assert abs(np.corrcoef(a, b)[0, 1]) < 0.01


class TestCalculatorMode:
    def test_no_deductions_by_default(self):
        sim = Simulation(situation=make_situation())
        assert sim.calculate("uc_deductions", YEAR)[0] == 0

    def test_draws_default_to_half(self):
        sim = Simulation(situation=make_situation())
        assert sim.calculate("uc_deduction_random_draw", YEAR)[0] == 0.5


class TestReformLevers:
    def test_raising_the_cap_restores_pre_frr_deductions(self):
        situation = make_situation(
            uc_latent_deduction_rate={YEAR: 0.25},
            uc_deduction_combination={YEAR: "ADVANCE_ONLY"},
        )
        baseline = Simulation(situation=situation)
        reform = Simulation(
            situation=situation,
            reform={
                "gov.dwp.universal_credit.deductions.cap": {
                    "2025-01-01.2025-12-31": 0.25
                }
            },
        )
        sa = baseline.calculate("uc_standard_allowance", YEAR)[0]
        assert baseline.calculate("uc_deductions", YEAR)[0] == pytest.approx(0.15 * sa)
        assert reform.calculate("uc_deductions", YEAR)[0] == pytest.approx(0.25 * sa)

    def test_abolishing_a_type_scales_by_its_amount_share(self):
        situation = make_situation(
            uc_latent_deduction_rate={YEAR: 0.10},
            uc_deduction_combination={YEAR: "ADVANCE_AND_GOVERNMENT"},
        )
        baseline = Simulation(situation=situation)
        reform = Simulation(
            situation=situation,
            reform={
                "gov.dwp.universal_credit.deductions.abolish.government": {
                    "2025-01-01.2025-12-31": True
                }
            },
        )
        sa = baseline.calculate("uc_standard_allowance", YEAR)[0]
        assert baseline.calculate("uc_deductions", YEAR)[0] == pytest.approx(0.10 * sa)
        # Advances are 41/(41+59) of this combination's deductions.
        assert reform.calculate("uc_deductions", YEAR)[0] == pytest.approx(
            0.10 * (41 / 100) * sa
        )

    def test_protected_floor_limits_combined_reductions(self):
        # The JRF-style case: the benefit cap plus deductions would push the
        # award far below 85% of the standard allowance; the floor stops the
        # combined reductions there.
        situation = make_situation(
            benefit_cap_reduction={YEAR: 2_500},
            uc_latent_deduction_rate={YEAR: 0.25},
            uc_deduction_combination={YEAR: "ADVANCE_ONLY"},
        )
        baseline = Simulation(situation=situation)
        reform = Simulation(
            situation=situation,
            reform={
                "gov.dwp.universal_credit.deductions.protected_floor": {
                    "2025-01-01.2025-12-31": 0.85
                }
            },
        )
        sa = baseline.calculate("uc_standard_allowance", YEAR)[0]
        deductions = baseline.calculate("uc_deductions", YEAR)[0]
        assert baseline.calculate("universal_credit", YEAR)[0] == pytest.approx(
            6_000 - 2_500 - deductions
        )
        assert reform.calculate("universal_credit", YEAR)[0] == pytest.approx(0.85 * sa)

    def test_protected_floor_inactive_when_reductions_stay_above_it(self):
        # Deductions alone under the 15% cap leave the award above an 85%
        # floor here, so the floor changes nothing.
        situation = make_situation(
            uc_latent_deduction_rate={YEAR: 0.25},
            uc_deduction_combination={YEAR: "ADVANCE_ONLY"},
        )
        baseline = Simulation(situation=situation)
        reform = Simulation(
            situation=situation,
            reform={
                "gov.dwp.universal_credit.deductions.protected_floor": {
                    "2025-01-01.2025-12-31": 0.85
                }
            },
        )
        assert reform.calculate("universal_credit", YEAR)[0] == pytest.approx(
            baseline.calculate("universal_credit", YEAR)[0]
        )

    def test_abolishing_all_types_removes_deductions(self):
        situation = make_situation(
            uc_latent_deduction_rate={YEAR: 0.25},
            uc_deduction_combination={YEAR: "ALL_THREE"},
        )
        reform = Simulation(
            situation=situation,
            reform={
                "gov.dwp.universal_credit.deductions.abolish.advance": {
                    "2025-01-01.2025-12-31": True
                },
                "gov.dwp.universal_credit.deductions.abolish.third_party": {
                    "2025-01-01.2025-12-31": True
                },
                "gov.dwp.universal_credit.deductions.abolish.government": {
                    "2025-01-01.2025-12-31": True
                },
            },
        )
        assert reform.calculate("uc_deductions", YEAR)[0] == 0
