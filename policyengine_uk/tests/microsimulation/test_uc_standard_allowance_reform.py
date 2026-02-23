"""
Test that reforms to Universal Credit standard allowance parameters
are respected and not overridden by rebalancing set_input.

See: https://github.com/PolicyEngine/policyengine-uk/issues/1472
"""

from policyengine_uk import Simulation


YEAR = 2026

# A single person aged 30 is a SINGLE_OLD claimant (over 25).
SITUATION = {
    "people": {"person": {"age": {YEAR: 30}}},
    "benunits": {"benunit": {"members": ["person"]}},
    "households": {"household": {"members": ["person"]}},
}


def test_uc_standard_allowance_responds_to_reform():
    """
    Doubling the UC standard allowance parameter should
    approximately double the calculated uc_standard_allowance.
    """
    baseline = Simulation(situation=SITUATION)
    baseline_sa = float(
        baseline.calculate("uc_standard_allowance", YEAR)[0]
    )

    # Double every claimant-type amount from 2025 onward.
    reform = {
        "gov.dwp.universal_credit.standard_allowance.amount.SINGLE_OLD": {
            "2025-01-01.2100-12-31": 800,
        },
    }

    reformed = Simulation(situation=SITUATION, reform=reform)
    reformed_sa = float(
        reformed.calculate("uc_standard_allowance", YEAR)[0]
    )

    # With the bug the two values are identical because set_input
    # bakes the baseline before the reform is applied.
    ratio = reformed_sa / baseline_sa
    assert ratio > 1.5, (
        f"Reformed UC SA ({reformed_sa:.2f}) should be roughly "
        f"double the baseline ({baseline_sa:.2f}), "
        f"but ratio is {ratio:.2f}. "
        f"Reform to standard_allowance parameter is being ignored."
    )
