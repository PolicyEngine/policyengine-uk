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


CTR_SITUATION = {
    "people": {
        "person": {
            "age": {YEAR: 40},
            "employment_income": {YEAR: 8000},
            "council_tax_benefit_reported": {YEAR: 800},
        }
    },
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
def test_abolish_council_tax_nets_out_council_tax_benefit():
    """CTR recipient should see net-CT saving, not gross-CT saving.

    Pre-reform: household pays £2,000 gross council tax and receives £800
    CTR, so out-of-pocket is £1,200 (the net bill). Abolishing council
    tax saves them the £1,200, not the £2,000 — because the £800 CTR
    rebate disappears alongside the council tax it was rebating.
    """
    baseline = Microsimulation(situation=CTR_SITUATION)
    reform = Microsimulation(
        situation=CTR_SITUATION,
        reform={"gov.contrib.abolish_council_tax": True},
    )

    baseline_hbai = baseline.calculate("hbai_household_net_income", YEAR).sum()
    reform_hbai = reform.calculate("hbai_household_net_income", YEAR).sum()
    baseline_gov_balance = baseline.calculate("gov_balance", YEAR).sum()
    reform_gov_balance = reform.calculate("gov_balance", YEAR).sum()

    # Net council tax = £2,000 - £800 CTR = £1,200 saving.
    assert reform_hbai == pytest.approx(baseline_hbai + 1200, abs=1)
    # Government loses net council tax revenue (gross - CTR forgone).
    assert reform_gov_balance == pytest.approx(baseline_gov_balance - 1200, abs=1)
