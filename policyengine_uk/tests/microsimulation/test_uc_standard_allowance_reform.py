"""Test UC standard allowance reforms are respected (#1472)."""

from policyengine_uk import Simulation

YEAR = 2026

SITUATION = {
    "people": {"person": {"age": {YEAR: 30}}},
    "benunits": {"benunit": {"members": ["person"]}},
    "households": {"household": {"members": ["person"]}},
}

REFORM = {
    "gov.dwp.universal_credit.standard_allowance.amount.SINGLE_OLD": {
        "2025-01-01.2100-12-31": 800,
    },
}


def test_uc_standard_allowance_responds_to_reform():
    baseline = Simulation(situation=SITUATION)
    b = baseline.calculate("uc_standard_allowance", YEAR)[0]
    reformed = Simulation(situation=SITUATION, reform=REFORM)
    r = reformed.calculate("uc_standard_allowance", YEAR)[0]
    assert r / b > 1.5
