"""
Test that reforms to basic State Pension parameters affect
microsimulation results.

Issue #1178: basic_state_pension reads parameters(data_year) instead of
parameters(period), so reforms to the parameter for the simulation year
have no budget impact.
"""

import pytest
from policyengine_uk import Microsimulation

YEAR = 2025


@pytest.fixture(scope="module")
def baseline():
    """Baseline microsimulation with current law."""
    return Microsimulation()


@pytest.fixture(scope="module")
def reform_halved():
    """Reform that halves the basic State Pension amount for 2025."""
    return Microsimulation(
        reform={
            "gov.dwp.state_pension.basic_state_pension.amount": {
                "2025-01-01": 84.75,
            }
        }
    )


@pytest.mark.microsimulation
def test_basic_state_pension_responds_to_reform(baseline, reform_halved):
    """
    Halving the basic State Pension parameter should significantly
    reduce the total basic_state_pension output.
    """
    baseline_total = baseline.calculate("basic_state_pension", YEAR).sum()
    reform_total = reform_halved.calculate("basic_state_pension", YEAR).sum()

    assert (
        baseline_total > 0
    ), "Baseline basic_state_pension should be positive"

    # Halving the parameter should reduce total by at least 10%
    assert reform_total < baseline_total * 0.9, (
        f"Halving the basic SP parameter should significantly reduce "
        f"total basic_state_pension. "
        f"Baseline: {baseline_total / 1e9:.3f}bn, "
        f"Reform: {reform_total / 1e9:.3f}bn"
    )
