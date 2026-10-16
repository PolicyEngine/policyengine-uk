"""Tests for Universal Credit deduction assignment and reform levers."""

import numpy as np
import pytest
from policyengine_core.enums import EnumArray

from policyengine_uk import Simulation
from policyengine_uk.utils.stochastic import splitmix64_uniform

YEAR = 2025

FLOOR_85 = {
    "gov.dwp.universal_credit.deductions.protected_floor": {
        "2025-01-01.2025-12-31": 0.85
    }
}


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
        # Latent demand of 30% is 25% cappable (cut to 15% by the cap) plus a
        # 5% last resort excess that current law exempts from the cap, giving
        # a 20% deduction rate. The modeled floor limits combined reductions
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

    def test_floor_components_reconcile_with_the_reduction_applied(self):
        # uc_deductions and uc_benefit_cap_reduction are what the award
        # actually loses, so they must sum to the entitlement forgone. Before
        # the floor was pushed into the components, they reported £960 and
        # £1,000 against a £720 reduction actually applied.
        situation = make_situation(
            benefit_cap_reduction={YEAR: 1_000},
            uc_latent_deduction_rate={YEAR: 0.30},
            uc_deduction_combination={YEAR: "ADVANCE_ONLY"},
        )
        reform = Simulation(
            situation=situation,
            reform={
                "gov.dwp.universal_credit.deductions.protected_floor": {
                    "2025-01-01.2025-12-31": 0.85
                }
            },
        )
        sa = reform.calculate("uc_standard_allowance", YEAR)[0]
        deductions = reform.calculate("uc_deductions", YEAR)[0]
        cap_reduction = reform.calculate("uc_benefit_cap_reduction", YEAR)[0]
        universal_credit = reform.calculate("universal_credit", YEAR)[0]
        assert deductions + cap_reduction == pytest.approx(0.15 * sa)
        assert deductions + cap_reduction == pytest.approx(6_000 - universal_credit)
        # The gross benefit cap reduction is unchanged: it also drives
        # Housing Benefit, which the Universal Credit floor does not protect.
        assert reform.calculate("benefit_cap_reduction", YEAR)[0] == 1_000

    def test_the_benefit_cap_reduction_absorbs_the_floor_first(self):
        # Deductions of 10% of the standard allowance fit inside a 15% floor
        # allowance, so they survive intact and the cap reduction keeps only
        # the 5% left. test_jrf_2026_example_keeps_a_full_rate_deduction
        # covers JRF's own example, where a 15% deduction fills the allowance.
        situation = make_situation(
            benefit_cap_reduction={YEAR: 2_500},
            uc_latent_deduction_rate={YEAR: 0.10},
            uc_deduction_combination={YEAR: "ADVANCE_ONLY"},
        )
        reform = Simulation(
            situation=situation,
            reform={
                "gov.dwp.universal_credit.deductions.protected_floor": {
                    "2025-01-01.2025-12-31": 0.85
                }
            },
        )
        sa = reform.calculate("uc_standard_allowance", YEAR)[0]
        assert reform.calculate("uc_deductions", YEAR)[0] == pytest.approx(0.10 * sa)
        assert reform.calculate("uc_benefit_cap_reduction", YEAR)[0] == pytest.approx(
            0.05 * sa
        )

    def test_jrf_2026_example_keeps_a_full_rate_deduction(self):
        # JRF's September 2026 briefing: standard allowance £98 a week, a
        # Fair Repayment Rate deduction of £15 and a benefit cap reduction of
        # £80; an 85% floor limits the total reduction to £15 and the
        # household gains £80. Latent demand of 25% is cut to the 15% cap,
        # which exactly fills the floor allowance, so the deduction survives
        # whole and the cap reduction falls to zero.
        situation = make_situation(
            uc_latent_deduction_rate={YEAR: 0.25},
            uc_deduction_combination={YEAR: "ADVANCE_ONLY"},
        )
        sa = Simulation(situation=situation).calculate("uc_standard_allowance", YEAR)[0]
        situation["benunits"]["benunit"]["benefit_cap_reduction"] = {YEAR: 80 / 98 * sa}
        reform = Simulation(situation=situation, reform=FLOOR_85)
        assert reform.calculate("uc_deductions", YEAR)[0] == pytest.approx(0.15 * sa)
        assert reform.calculate("uc_benefit_cap_reduction", YEAR)[0] == pytest.approx(
            0, abs=0.01
        )
        assert reform.calculate("universal_credit", YEAR)[0] == pytest.approx(
            6_000 - 0.15 * sa
        )

    @pytest.mark.parametrize("gross_cap_reduction", [5_500, 5_900])
    def test_heavy_capping_does_not_squeeze_the_deduction(self, gross_cap_reduction):
        # Under the gross cap the penny rule leaves room for only £499.88 or
        # £99.88 of deductions. The floor removes all but the allowance, so
        # the deduction is met in full from the protected award and the cap
        # reduction absorbs the floor: £720.25 and £0, not £499.88/£220.37
        # or £99.88/£620.37.
        situation = make_situation(
            benefit_cap_reduction={YEAR: gross_cap_reduction},
            uc_latent_deduction_rate={YEAR: 0.30},
            uc_deduction_combination={YEAR: "ADVANCE_ONLY"},
        )
        reform = Simulation(situation=situation, reform=FLOOR_85)
        sa = reform.calculate("uc_standard_allowance", YEAR)[0]
        assert reform.calculate("uc_deductions", YEAR)[0] == pytest.approx(0.15 * sa)
        assert reform.calculate("uc_benefit_cap_reduction", YEAR)[0] == 0
        assert reform.calculate("universal_credit", YEAR)[0] == pytest.approx(
            6_000 - 0.15 * sa
        )
        assert reform.calculate("benefit_cap_reduction", YEAR)[0] == gross_cap_reduction

    @pytest.mark.parametrize("floor", [0, 0.85])
    def test_applied_cap_never_exceeds_the_award_lost(self, floor):
        # A £1,000 gross cap reduction on a £500 award takes £500, not £1,000
        # (no floor) or the £720.25 floor allowance. The gross figure, which
        # Housing Benefit reads, is unchanged.
        situation = make_situation(
            universal_credit_pre_benefit_cap={YEAR: 500},
            benefit_cap_reduction={YEAR: 1_000},
        )
        reform = Simulation(
            situation=situation,
            reform={
                "gov.dwp.universal_credit.deductions.protected_floor": {
                    "2025-01-01.2025-12-31": floor
                }
            },
        )
        assert reform.calculate("uc_deductions", YEAR)[0] == 0
        assert reform.calculate("uc_benefit_cap_reduction", YEAR)[0] == 500
        assert reform.calculate("universal_credit", YEAR)[0] == 0
        assert reform.calculate("benefit_cap_reduction", YEAR)[0] == 1_000

    def test_floor_changes_nothing_where_it_does_not_bind(self):
        # A £700 award, a £1,000 gross cap and deduction demand above the
        # floor allowance: the cap already takes the whole award, which is
        # less than the £720.25 allowance, so the floor leaves the current-law
        # split alone rather than moving the loss from the cap to deductions.
        situation = make_situation(
            universal_credit_pre_benefit_cap={YEAR: 700},
            benefit_cap_reduction={YEAR: 1_000},
            uc_latent_deduction_rate={YEAR: 0.30},
            uc_deduction_combination={YEAR: "ADVANCE_ONLY"},
        )
        reform = Simulation(situation=situation, reform=FLOOR_85)
        assert reform.calculate("uc_deductions", YEAR)[0] == 0
        assert reform.calculate("uc_benefit_cap_reduction", YEAR)[0] == 700
        assert reform.calculate("universal_credit", YEAR)[0] == 0

    def test_a_floor_above_the_standard_allowance_adds_nothing(self):
        # (1 - floor) x standard allowance goes negative above a floor of 1;
        # subtracting it added £960 to a £6,000 award. The allowance clamps
        # at zero, where the floor protects the standard allowance entirely.
        situation = make_situation(
            benefit_cap_reduction={YEAR: 1_000},
            uc_latent_deduction_rate={YEAR: 0.25},
            uc_deduction_combination={YEAR: "ADVANCE_ONLY"},
        )
        reform = Simulation(
            situation=situation,
            reform={
                "gov.dwp.universal_credit.deductions.protected_floor": {
                    "2025-01-01.2025-12-31": 1.2
                }
            },
        )
        assert reform.calculate("uc_deductions", YEAR)[0] == 0
        assert reform.calculate("uc_benefit_cap_reduction", YEAR)[0] == 0
        assert reform.calculate("universal_credit", YEAR)[0] == pytest.approx(6_000)

    def test_no_deductions_without_a_universal_credit_claim(self):
        # Datasets are meant to impute uc_latent_deduction_rate directly, at
        # which point nothing else gates deductions on the claim.
        sim = Simulation(
            situation=make_situation(
                would_claim_uc={YEAR: False},
                uc_latent_deduction_rate={YEAR: 0.30},
                uc_deduction_combination={YEAR: "ADVANCE_ONLY"},
            )
        )
        assert sim.calculate("universal_credit", YEAR)[0] == 0
        assert sim.calculate("uc_deductions", YEAR)[0] == 0
        assert sim.calculate("uc_benefit_cap_reduction", YEAR)[0] == 0

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
