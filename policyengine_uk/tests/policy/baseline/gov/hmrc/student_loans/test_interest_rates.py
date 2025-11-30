"""Tests for student loan interest rate variable.

Tests the student_loan_interest_rate variable which calculates the
applicable interest rate based on plan type and income.
"""

import pytest
from policyengine_uk import Simulation


class TestStudentLoanInterestRateVariable:
    """Test the student_loan_interest_rate variable formula."""

    def test_plan_1_rate(self):
        """Plan 1 should use the fixed Plan 1 rate."""
        sim = Simulation(
            situation={
                "people": {
                    "person": {
                        "student_loan_plan": {"2026": "PLAN_1"},
                        "adjusted_net_income": {"2026": 40000},
                    }
                }
            }
        )
        rate = sim.calculate("student_loan_interest_rate", 2026)
        assert rate[0] == pytest.approx(0.032, abs=0.001)

    def test_plan_2_low_income(self):
        """Plan 2 below lower threshold should get base rate only."""
        sim = Simulation(
            situation={
                "people": {
                    "person": {
                        "student_loan_plan": {"2026": "PLAN_2"},
                        "adjusted_net_income": {"2026": 25000},
                    }
                }
            }
        )
        rate = sim.calculate("student_loan_interest_rate", 2026)
        # Base rate only (3.2%)
        assert rate[0] == pytest.approx(0.032, abs=0.001)

    def test_plan_2_high_income(self):
        """Plan 2 above upper threshold should get base + full additional."""
        sim = Simulation(
            situation={
                "people": {
                    "person": {
                        "student_loan_plan": {"2026": "PLAN_2"},
                        "adjusted_net_income": {"2026": 60000},
                    }
                }
            }
        )
        rate = sim.calculate("student_loan_interest_rate", 2026)
        # Base (3.2%) + additional (3%) = 6.2%
        assert rate[0] == pytest.approx(0.062, abs=0.001)

    def test_plan_2_mid_income(self):
        """Plan 2 between thresholds should get tapered rate."""
        # Lower threshold: £28,470, Upper threshold: £51,245
        # Midpoint income: (28470 + 51245) / 2 = 39857.5
        sim = Simulation(
            situation={
                "people": {
                    "person": {
                        "student_loan_plan": {"2026": "PLAN_2"},
                        "adjusted_net_income": {"2026": 39857.5},
                    }
                }
            }
        )
        rate = sim.calculate("student_loan_interest_rate", 2026)
        # Base (3.2%) + half of additional (1.5%) = 4.7%
        assert rate[0] == pytest.approx(0.047, abs=0.001)

    def test_plan_4_rate(self):
        """Plan 4 should use the fixed Plan 4 rate (same as Plan 1)."""
        sim = Simulation(
            situation={
                "people": {
                    "person": {
                        "student_loan_plan": {"2026": "PLAN_4"},
                        "adjusted_net_income": {"2026": 40000},
                    }
                }
            }
        )
        rate = sim.calculate("student_loan_interest_rate", 2026)
        assert rate[0] == pytest.approx(0.032, abs=0.001)

    def test_plan_5_rate(self):
        """Plan 5 should use RPI only (no income-based component)."""
        sim = Simulation(
            situation={
                "people": {
                    "person": {
                        "student_loan_plan": {"2026": "PLAN_5"},
                        "adjusted_net_income": {"2026": 60000},
                    }
                }
            }
        )
        rate = sim.calculate("student_loan_interest_rate", 2026)
        # RPI only (3.2%) regardless of income
        assert rate[0] == pytest.approx(0.032, abs=0.001)

    def test_no_loan_zero_rate(self):
        """No student loan should return zero rate."""
        sim = Simulation(
            situation={
                "people": {
                    "person": {
                        "student_loan_plan": {"2026": "NONE"},
                        "adjusted_net_income": {"2026": 50000},
                    }
                }
            }
        )
        rate = sim.calculate("student_loan_interest_rate", 2026)
        assert rate[0] == 0
