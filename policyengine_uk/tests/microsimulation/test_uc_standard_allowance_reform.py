"""Test UC standard allowance reforms are respected (#1472)."""

from policyengine_uk import Simulation

YEAR = 2026

SITUATION = {
    "people": {"person": {"age": {YEAR: 30}}},
    "benunits": {"benunit": {"members": ["person"]}},
    "households": {"household": {"members": ["person"]}},
}


def test_uc_standard_allowance_responds_to_reform():
    baseline = Simulation(situation=SITUATION)
    baseline_sa = float(
        baseline.calculate("uc_standard_allowance", YEAR)[0]
    )

    reform = {
        "gov.dwp.universal_credit.standard_allowance.amount.SINGLE_OLD": {
            "2025-01-01.2100-12-31": 800,
        },
    }

    reformed = Simulation(situation=SITUATION, reform=reform)
    reformed_sa = float(
        reformed.calculate("uc_standard_allowance", YEAR)[0]
    )

    ratio = reformed_sa / baseline_sa
    assert ratio > 1.5
