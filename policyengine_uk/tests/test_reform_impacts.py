"""
Tests that key parametric reforms produce non-zero impacts.

These tests catch silent failures where a reform runs without error
but produces the same result as the baseline (e.g., due to a
parameter path being wrong or a formula not picking up the change).
"""

import pytest
from policyengine_uk.model_api import Scenario
from policyengine_uk import Microsimulation

YEAR = 2025

BASE_SITUATION = {
    "people": {
        "adult": {
            "age": {YEAR: 35},
            "employment_income": {YEAR: 40_000},
            "hours_worked": {YEAR: 40},
        },
        "child": {
            "age": {YEAR: 5},
        },
    },
    "benunits": {
        "benunit": {
            "members": ["adult", "child"],
        },
    },
    "households": {
        "household": {
            "members": ["adult", "child"],
            "region": {YEAR: "LONDON"},
        },
    },
}


def _reform_changes_variable(parameter_changes, variable, situation=None):
    """Check that applying a parameter reform changes a variable's value."""
    sit = situation or BASE_SITUATION
    baseline = Microsimulation(situation=sit)
    scenario = Scenario(parameter_changes=parameter_changes)
    reformed = Microsimulation(situation=sit, scenario=scenario)

    baseline_val = baseline.calculate(variable, YEAR).values[0]
    reformed_val = reformed.calculate(variable, YEAR).values[0]
    return baseline_val != reformed_val


class TestReformImpacts:
    """Verify that common parametric reforms produce non-zero impacts."""

    def test_income_tax_rate_reform(self):
        """Changing the basic rate of income tax should affect income tax."""
        assert _reform_changes_variable(
            {"gov.hmrc.income_tax.rates.uk[0].rate": {str(YEAR): 0.30}},
            "income_tax",
        )

    def test_personal_allowance_reform(self):
        """Changing the personal allowance should affect income tax."""
        assert _reform_changes_variable(
            {
                "gov.hmrc.income_tax.allowances.personal_allowance.amount": {
                    str(YEAR): 15_000
                }
            },
            "income_tax",
        )

    def test_ni_rate_reform(self):
        """Changing the NI employee rate should affect national insurance."""
        assert _reform_changes_variable(
            {
                "gov.hmrc.national_insurance.class_1.rates.employee.main": {
                    str(YEAR): 0.20
                }
            },
            "national_insurance",
        )

    def test_child_benefit_reform(self):
        """Changing the eldest child benefit amount should affect child benefit."""
        assert _reform_changes_variable(
            {
                "gov.hmrc.child_benefit.amount.eldest": {
                    str(YEAR): 30
                }
            },
            "child_benefit",
        )

    def test_uc_standard_allowance_reform(self):
        """Changing UC standard allowance should affect universal credit."""
        low_income_situation = {
            "people": {
                "adult": {
                    "age": {YEAR: 30},
                    "employment_income": {YEAR: 5_000},
                    "hours_worked": {YEAR: 10},
                },
            },
            "benunits": {
                "benunit": {
                    "members": ["adult"],
                    "would_claim_uc": {YEAR: True},
                },
            },
            "households": {
                "household": {
                    "members": ["adult"],
                    "region": {YEAR: "LONDON"},
                },
            },
        }
        assert _reform_changes_variable(
            {
                "gov.dwp.universal_credit.standard_allowance.amount.SINGLE_OLD": {
                    str(YEAR): 500
                }
            },
            "universal_credit",
            situation=low_income_situation,
        )

    def test_fuel_duty_reform(self):
        """Changing fuel duty should affect fuel duty paid."""
        driver_situation = {
            "people": {
                "adult": {
                    "age": {YEAR: 35},
                    "employment_income": {YEAR: 30_000},
                },
            },
            "benunits": {
                "benunit": {
                    "members": ["adult"],
                },
            },
            "households": {
                "household": {
                    "members": ["adult"],
                    "region": {YEAR: "NORTH_EAST"},
                    "petrol_spending": {YEAR: 2_000},
                },
            },
        }
        assert _reform_changes_variable(
            {
                "gov.hmrc.fuel_duty.petrol_and_diesel": {
                    str(YEAR): 1.0
                }
            },
            "fuel_duty",
            situation=driver_situation,
        )
