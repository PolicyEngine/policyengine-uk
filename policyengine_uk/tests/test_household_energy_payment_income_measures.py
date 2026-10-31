"""The Household Energy Payment in the income measures.

The £100 payment (Budget 2026, paragraph 6.24) raises household net income
and HBAI income alike: HBAI counted the 2022 Council Tax Rebate and the
Energy Bills Support Scheme, the same kind of one-off support, as
miscellaneous income (HBAI quality and methodology report FYE 2023).
"""

import pytest

from policyengine_uk import Simulation

pytestmark = pytest.mark.usefixtures("cloned_uk_tax_benefit_system")

YEAR = 2026
WITHOUT_PAYMENT = {"gov.treasury.household_energy_payment.amount": {str(YEAR): 0}}
SITUATION = {
    "people": {"adult": {"age": {YEAR: 40}, "employment_income": {YEAR: 30_000}}},
    "benunits": {"benunit": {"members": ["adult"]}},
    "households": {
        "household": {
            "members": ["adult"],
            "region": {YEAR: "NORTH_WEST"},
            "council_tax_band": {YEAR: "B"},
        }
    },
}


def measures(reform=None):
    sim = Simulation(situation=SITUATION, reform=reform)
    return {
        v: float(sim.calculate(v, YEAR)[0])
        for v in [
            "household_energy_payment",
            "household_net_income",
            "hbai_household_net_income",
        ]
    }


def test_payment_raises_net_income_and_hbai_income_by_100():
    law, without = measures(), measures(WITHOUT_PAYMENT)
    assert law["household_energy_payment"] == 100
    assert without["household_energy_payment"] == 0
    for income in ("household_net_income", "hbai_household_net_income"):
        assert law[income] - without[income] == pytest.approx(100, abs=0.01)
