"""Spousal maintenance reaches the means tests; child maintenance does not.

Maintenance from a spouse, civil partner, former spouse or former civil
partner is Universal Credit unearned income (UC Regs 2013 reg. 66(1)(d)),
Pension Credit income (SPC Regs 2002 reg. 15(5)(d)) and Housing Benefit
income (HB Regs 2006 reg. 40; HB (SPC) Regs 2006 reg. 29(1)(o)). Child
maintenance is none of these. Both are market and HBAI income.
"""

import numpy as np
import pytest

from policyengine_uk import Simulation

YEAR = 2026
# age, employment income, private pension, tenure, rent
PEOPLE = [
    # Working age, no other income: on Universal Credit.
    (30, 0, 0, "RENT_PRIVATELY", 9_000),
    # Pension age, low pension: on guarantee credit.
    (80, 0, 6_000, "RENT_FROM_COUNCIL", 6_000),
    # A high earner on no benefit.
    (45, 80_000, 0, "OWNED_OUTRIGHT", 0),
]
MEANS_TESTS = (
    "uc_unearned_income",
    "pension_credit_income",
    "housing_benefit_applicable_income",
)


def simulation(maintenance_variable=None, amount=0):
    people, benunits, households = {}, {}, {}
    for i, (age, pay, pension, tenure, rent) in enumerate(PEOPLE):
        inputs = {
            "age": age,
            "employment_income": pay,
            "private_pension_income": pension,
            "state_pension": 0,
        }
        if maintenance_variable is not None:
            inputs[maintenance_variable] = amount
        people[f"p{i}"] = {k: {str(YEAR): v} for k, v in inputs.items()}
        benunits[f"b{i}"] = {"members": [f"p{i}"]}
        households[f"h{i}"] = {
            "members": [f"p{i}"],
            "country": "ENGLAND",
            "tenure_type": tenure,
            "rent": rent,
        }
    return Simulation(
        situation={"people": people, "benunits": benunits, "households": households}
    )


@pytest.fixture(scope="module")
def simulations():
    return {
        "none": simulation(),
        "spousal": simulation("spousal_maintenance_income", 1_200),
        "child": simulation("maintenance_income", 1_200),
    }


def values(sim, variable):
    return np.asarray(sim.calculate(variable, YEAR), dtype=float)


def change(simulations, kind, variable):
    return values(simulations[kind], variable) - values(simulations["none"], variable)


def test_uc_award_falls_by_spousal_maintenance(simulations):
    # £100 a month: the award falls by £100 a month.
    assert values(simulations["none"], "universal_credit")[0] > 1_200
    assert change(simulations, "spousal", "universal_credit")[0] == pytest.approx(
        -1_200, abs=0.01
    )


def test_guarantee_credit_falls_by_spousal_maintenance(simulations):
    assert values(simulations["none"], "guarantee_credit")[1] > 1_200
    assert change(simulations, "spousal", "guarantee_credit")[1] == pytest.approx(
        -1_200, abs=0.01
    )
    assert change(simulations, "spousal", "savings_credit_income")[1] == 0


def test_child_maintenance_changes_no_means_test(simulations):
    for name in MEANS_TESTS + (
        "universal_credit",
        "pension_credit",
        "housing_benefit",
    ):
        np.testing.assert_allclose(
            change(simulations, "child", name), 0, atol=0.01, err_msg=name
        )


@pytest.mark.parametrize("kind", ("spousal", "child"))
def test_both_kinds_are_market_and_hbai_income(simulations, kind):
    # The high earner gets no means-tested benefit, so HBAI income rises by
    # the whole payment, which is not taxable.
    for name in ("market_income", "household_market_income"):
        np.testing.assert_allclose(
            change(simulations, kind, name), 1_200, atol=0.01, err_msg=name
        )
    assert change(simulations, kind, "hbai_household_net_income")[2] == pytest.approx(
        1_200, abs=0.01
    )
