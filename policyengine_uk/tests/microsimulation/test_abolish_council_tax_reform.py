"""Test abolishing council tax affects household and government balances."""

import pytest

from policyengine_uk import Microsimulation

YEAR = 2025

SITUATION = {
    "people": {"person": {"age": {YEAR: 40}, "employment_income": {YEAR: 30000}}},
    "benunits": {"benunit": {"members": ["person"]}},
    "households": {
        "household": {
            "members": ["person"],
            "council_tax": {YEAR: 2000},
            "council_tax_band": {YEAR: "C"},
        }
    },
}


@pytest.mark.microsimulation
def test_abolish_council_tax_removes_budget_impact():
    baseline = Microsimulation(situation=SITUATION)
    reform = Microsimulation(
        situation=SITUATION,
        reform={"gov.contrib.abolish_council_tax": True},
    )

    baseline_household_tax = baseline.calculate("household_tax", YEAR).sum()
    reform_household_tax = reform.calculate("household_tax", YEAR).sum()
    baseline_gov_balance = baseline.calculate("gov_balance", YEAR).sum()
    reform_gov_balance = reform.calculate("gov_balance", YEAR).sum()
    baseline_hbai = baseline.calculate("hbai_household_net_income", YEAR).sum()
    reform_hbai = reform.calculate("hbai_household_net_income", YEAR).sum()

    assert reform_household_tax == baseline_household_tax - 2000
    assert reform_gov_balance == baseline_gov_balance - 2000
    assert reform_hbai == baseline_hbai + 2000
