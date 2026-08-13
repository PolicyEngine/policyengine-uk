"""Tests for Universal Credit deduction assignment and reform levers."""

import numpy as np
import pytest
from policyengine_core.enums import EnumArray

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

    def test_draws_default_to_one(self):
        # 1.0 never falls below any incidence, so calculators get no
        # deductions in any region unless set explicitly.
        sim = Simulation(situation=make_situation())
        assert sim.calculate("uc_deduction_random_draw", YEAR)[0] == 1.0


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
        # The JRF-style case: the benefit cap plus deductions far exceed 15%
        # of the standard allowance; the floor limits the combined
        # reductions to (1 - 0.85) x standard allowance.
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
        assert reform.calculate("universal_credit", YEAR)[0] == pytest.approx(
            6_000 - 0.15 * sa
        )

    def test_zeroing_a_type_mean_does_not_crash(self):
        situation = make_situation(
            uc_latent_deduction_rate={YEAR: 0.10},
            uc_deduction_combination={YEAR: "ADVANCE_ONLY"},
        )
        reform = Simulation(
            situation=situation,
            reform={
                "gov.simulation.uc_deductions.mean_monthly_amount_by_type.ADVANCE": {
                    "2025-01-01.2025-12-31": 0
                }
            },
        )
        assert reform.calculate("uc_deductions", YEAR)[0] == 0

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

    def test_protected_floor_binds_on_the_above_cap_excess(self):
        # Latent demand of 30% is 15% cappable plus a 15% last resort excess
        # that current law exempts from the cap, giving a 20% deduction rate
        # under the 15% cap. The modeled floor limits combined reductions
        # regardless of category, so it cuts into that excess. JRF's briefing
        # does not say whether their floor exempts last resort and child
        # maintenance deductions; this pins the modeling choice.
        situation = make_situation(
            uc_latent_deduction_rate={YEAR: 0.30},
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
        assert baseline.calculate("uc_deduction_rate", YEAR)[0] == pytest.approx(0.20)
        assert reform.calculate("universal_credit", YEAR)[0] == pytest.approx(
            6_000 - 0.15 * sa
        )

    def test_zeroing_every_type_share_leaves_a_valid_enum_array(self):
        situation = make_situation(
            uc_deduction_random_draw={YEAR: 0.0},
            uc_latent_deduction_rate={YEAR: 0.10},
        )
        reform = Simulation(
            situation=situation,
            reform={
                f"gov.simulation.uc_deductions.type_combination.{key}": {
                    "2025-01-01.2025-12-31": 0
                }
                for key in [
                    "ADVANCE_ONLY",
                    "THIRD_PARTY_ONLY",
                    "GOVERNMENT_ONLY",
                    "ADVANCE_AND_GOVERNMENT",
                    "ADVANCE_AND_THIRD_PARTY",
                    "THIRD_PARTY_AND_GOVERNMENT",
                    "ALL_THREE",
                ]
            },
        )
        assert reform.calculate("uc_deduction_combination", YEAR)[0] == "NONE"
        # The zero-total branch must encode like the normal branch, so
        # downstream enum comparisons still work.
        stored = reform.get_holder("uc_deduction_combination").get_array(str(YEAR))
        assert isinstance(stored, EnumArray)
        assert reform.calculate("uc_deductions", YEAR)[0] == 0

    def test_zeroing_all_combination_shares_degrades_gracefully(self):
        # With every combination share reformed to zero, the combination
        # falls back to NONE and deductions compute to zero without error.
        situation = make_situation(
            uc_latent_deduction_rate={YEAR: 0.10},
        )
        prefix = "gov.simulation.uc_deductions.type_combination"
        reform = Simulation(
            situation=situation,
            reform={
                f"{prefix}.{combo}": {"2025-01-01.2025-12-31": 0}
                for combo in [
                    "ADVANCE_ONLY",
                    "THIRD_PARTY_ONLY",
                    "GOVERNMENT_ONLY",
                    "ADVANCE_AND_GOVERNMENT",
                    "ADVANCE_AND_THIRD_PARTY",
                    "THIRD_PARTY_AND_GOVERNMENT",
                    "ALL_THREE",
                ]
            },
        )
        assert reform.calculate("uc_deductions", YEAR)[0] == 0

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
