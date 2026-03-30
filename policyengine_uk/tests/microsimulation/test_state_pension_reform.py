"""Test state pension parameter reforms affect microsimulation outputs."""

import pytest

from policyengine_uk import Microsimulation

YEAR = 2025


@pytest.fixture(scope="module")
def baseline():
    return Microsimulation()


@pytest.fixture(scope="module")
def reform_halved():
    return Microsimulation(
        reform={
            "gov.dwp.state_pension.basic_state_pension.amount": {
                "2025-01-01": 84.75,
            }
        }
    )


@pytest.mark.microsimulation
def test_basic_state_pension_responds_to_reform(baseline, reform_halved):
    baseline_total = baseline.calculate("basic_state_pension", YEAR).sum()
    reform_total = reform_halved.calculate("basic_state_pension", YEAR).sum()

    assert baseline_total > 0
    assert reform_total < baseline_total * 0.9
