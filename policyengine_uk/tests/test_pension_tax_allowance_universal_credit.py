"""The Pension Tax Allowance in Universal Credit.

Universal Credit deducts the income tax paid on earnings (UC Regulations 2013
reg. 55(5)(b) and 57(2)), which it works out from the rates less the Step 6
reductions in gov.hmrc.income_tax.income_tax_subtractions. The allowance is
on that list, so for a mixed-age couple whose older partner works, it raises
earned income and UC takes back the taper share of it. UC counts pension
income before tax (reg. 66), so there the allowance leaves UC unchanged.

The working case is Pavel Makarchuk's on uk-autumn-budget-dashboard-2026 #290:
an unmarried couple aged 70 and 60 renting in the North West in 2027-28, the
older partner earning £13,036.40 with the State Pension deferred.
"""

import pytest

from policyengine_uk import Simulation

pytestmark = pytest.mark.usefixtures("cloned_uk_tax_benefit_system")

YEAR = 2027
WITHOUT_PTA = {
    "gov.hmrc.income_tax.reliefs.pension_tax_allowance.in_effect": {str(YEAR): False}
}


def couple(older_income):
    return {
        "people": {
            "older": {
                "age": {YEAR: 70},
                **{k: {YEAR: v} for k, v in older_income.items()},
            },
            "younger": {"age": {YEAR: 60}},
        },
        "benunits": {
            "benunit": {
                "members": ["older", "younger"],
                # Unmarried, so no Marriage Allowance transfer
                "is_married": {YEAR: False},
            }
        },
        "households": {
            "household": {
                "members": ["older", "younger"],
                "region": {YEAR: "NORTH_WEST"},
                "tenure_type": {YEAR: "RENT_PRIVATELY"},
                "rent": {YEAR: 7_200},
            }
        },
    }


def results(situation, reform=None):
    sim = Simulation(situation=situation, reform=reform)
    return {
        "pension_tax_allowance": float(sim.calculate("pension_tax_allowance", YEAR)[0]),
        "universal_credit": float(sim.calculate("universal_credit", YEAR)[0]),
        "household_net_income": float(sim.calculate("household_net_income", YEAR)[0]),
        "taper": sim.tax_benefit_system.parameters.gov.dwp.universal_credit.means_test.reduction_rate(
            f"{YEAR}-04-30"
        ),
    }


def test_uc_takes_back_the_taper_share_of_the_allowance_on_earnings():
    situation = couple({"employment_income": 13_036.40})
    law, without = results(situation), results(situation, WITHOUT_PTA)
    assert law["pension_tax_allowance"] == pytest.approx(93.28, abs=0.01)
    assert without["universal_credit"] > 0
    uc_change = law["universal_credit"] - without["universal_credit"]
    # 55% x 93.28 = 51.30, leaving the couple 41.97 better off
    assert uc_change == pytest.approx(-law["taper"] * 93.28, abs=0.01)
    assert uc_change == pytest.approx(-51.30, abs=0.01)
    assert law["household_net_income"] - without["household_net_income"] == (
        pytest.approx(41.97, abs=0.01)
    )


def test_uc_ignores_the_allowance_on_pension_income():
    situation = couple({"private_pension_income": 13_036.40})
    law, without = results(situation), results(situation, WITHOUT_PTA)
    assert law["pension_tax_allowance"] == pytest.approx(93.28, abs=0.01)
    assert law["universal_credit"] == pytest.approx(
        without["universal_credit"], abs=0.01
    )
    assert law["household_net_income"] - without["household_net_income"] == (
        pytest.approx(93.28, abs=0.01)
    )
