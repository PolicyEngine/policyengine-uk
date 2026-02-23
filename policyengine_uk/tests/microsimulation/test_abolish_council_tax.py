"""Test that abolishing council tax has a budgetary impact (#1153)."""

import pytest
from policyengine_uk import Microsimulation
from policyengine_uk.model_api import Scenario

YEAR = 2025
CT_AMOUNT = 2000

SITUATION = {
    "people": {
        "person": {
            "age": {YEAR: 30},
            "employment_income": {YEAR: 30000},
        },
    },
    "benunits": {"benunit": {"members": ["person"]}},
    "households": {
        "household": {
            "members": ["person"],
            "council_tax": {YEAR: CT_AMOUNT},
        },
    },
}


@pytest.fixture(scope="module")
def baseline_net_income():
    sim = Microsimulation(situation=SITUATION)
    return float(sim.calculate("household_net_income", YEAR).sum())


@pytest.fixture(scope="module")
def reform_net_income():
    scenario = Scenario(
        parameter_changes={
            "gov.contrib.abolish_council_tax": {str(YEAR): True}
        }
    )
    sim = Microsimulation(situation=SITUATION, scenario=scenario)
    return float(sim.calculate("household_net_income", YEAR).sum())


def test_abolish_council_tax_increases_net_income(
    baseline_net_income, reform_net_income
):
    diff = reform_net_income - baseline_net_income
    assert diff > 0


def test_abolish_council_tax_increases_by_council_tax_amount(
    baseline_net_income, reform_net_income
):
    diff = reform_net_income - baseline_net_income
    assert abs(diff - CT_AMOUNT) < 100
