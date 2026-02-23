"""
Test that abolishing council tax has a budgetary impact.

Regression test for GitHub issue #1153: setting abolish_council_tax
to True previously had no effect because both household_tax and
pre_budget_change_household_tax applied the same abolish check,
making the reform-vs-baseline delta zero.
"""

import pytest
from policyengine_uk import Microsimulation
from policyengine_uk.model_api import Scenario


YEAR = 2025
COUNCIL_TAX_AMOUNT = 2_000

SITUATION = {
    "people": {
        "person": {
            "age": {YEAR: 30},
            "employment_income": {YEAR: 30_000},
        },
    },
    "benunits": {"benunit": {"members": ["person"]}},
    "households": {
        "household": {
            "members": ["person"],
            "council_tax": {YEAR: COUNCIL_TAX_AMOUNT},
        },
    },
}


@pytest.fixture(scope="module")
def baseline_net_income():
    sim = Microsimulation(situation=SITUATION)
    return float(
        sim.calculate("household_net_income", YEAR).sum()
    )


@pytest.fixture(scope="module")
def reform_net_income():
    scenario = Scenario(
        parameter_changes={
            "gov.contrib.abolish_council_tax": {
                str(YEAR): True,
            },
        },
    )
    sim = Microsimulation(
        situation=SITUATION, scenario=scenario
    )
    return float(
        sim.calculate("household_net_income", YEAR).sum()
    )


def test_abolish_council_tax_increases_net_income(
    baseline_net_income,
    reform_net_income,
):
    """Abolishing council tax should increase household net income."""
    diff = reform_net_income - baseline_net_income
    assert diff > 0, (
        f"Abolishing council tax should increase net income, "
        f"but diff is {diff:.2f} "
        f"(baseline={baseline_net_income:.2f}, "
        f"reform={reform_net_income:.2f})"
    )


def test_abolish_council_tax_increases_by_council_tax_amount(
    baseline_net_income,
    reform_net_income,
):
    """Net income increase should approximate the council tax amount."""
    diff = reform_net_income - baseline_net_income
    assert abs(diff - COUNCIL_TAX_AMOUNT) < 100, (
        f"Net income increase ({diff:.2f}) should be close to "
        f"council tax amount ({COUNCIL_TAX_AMOUNT})"
    )
