"""Carer's Allowance earnings limit.

SSCBA 1992 s. 70(1)(b) bars a person who is gainfully employed, and reg. 8(1)
of the Social Security (Invalid Care Allowance) Regulations 1976 treats a
person as gainfully employed when their earnings exceed the limit (£204 a
week from 6 April 2026). Earnings are net of income tax, primary Class 1 (and
Class 2 and 4) contributions and half of pension contributions (Computation of
Earnings Regulations 1996 regs. 10(4) and 13).

Invariants, for a carer in England in 2026 caring 35 hours or more, with pay,
trading profit, employee pension contributions and unearned income drawn
freely:

1. Bounds: 0 <= carers_allowance_earnings <= pay + max(0, profit).
2. Differential: the test is passed exactly when
   carers_allowance_earnings / 52 <= 204, and the allowance is the full rate
   then and nil otherwise.
3. Monotonic: raising pay never lowers net earnings, so a person over the
   limit stays over it.
4. Unearned income is not earnings: savings interest and pension income
   leave carers_allowance_earnings unchanged.
"""

import numpy as np
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation

LIMIT = 204
RATE = 86.45
WEEKS = 52


def _person(pay, profit, pension, savings=0.0, private_pension=0.0):
    situation = {
        "people": {
            "carer": {
                "age": {"2026": 45},
                "employment_income": {"2026": pay},
                "self_employment_income": {"2026": profit},
                "employee_pension_contributions": {"2026": pension},
                "savings_interest_income": {"2026": savings},
                "private_pension_income": {"2026": private_pension},
                "care_hours": {"2026": 40},
            }
        },
        "benunits": {"benunit": {"members": ["carer"]}},
        "households": {
            "household": {"members": ["carer"], "country": {"2026": "ENGLAND"}}
        },
    }
    sim = Simulation(situation=situation)
    return {
        name: float(np.asarray(sim.calculate(name, 2026))[0])
        for name in (
            "carers_allowance_earnings",
            "is_gainfully_employed_for_carers_allowance",
            "carers_allowance",
        )
    }


money = st.floats(min_value=0, max_value=60_000, allow_nan=False)
profit_money = st.floats(min_value=-20_000, max_value=60_000, allow_nan=False)


@settings(
    max_examples=12,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
)
@given(pay=money, profit=profit_money, pension_share=st.floats(0, 0.3))
def test_bounds_and_differential(pay, profit, pension_share):
    pension = pay * pension_share
    result = _person(pay, profit, pension)
    earnings = result["carers_allowance_earnings"]
    assert -0.01 <= earnings <= pay + max(0, profit) + 0.01
    # Regulation 5: a fraction of a penny is disregarded.
    over = np.floor(earnings / WEEKS * 100 + 1e-6) / 100 > LIMIT
    assert bool(result["is_gainfully_employed_for_carers_allowance"]) == over
    expected = 0 if over else RATE * WEEKS
    assert abs(result["carers_allowance"] - expected) < 0.01


@settings(
    max_examples=8,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
)
@given(pay=money, rise=st.floats(min_value=1, max_value=20_000))
def test_net_earnings_never_fall_as_pay_rises(pay, rise):
    lower = _person(pay, 0, 0)
    higher = _person(pay + rise, 0, 0)
    assert (
        higher["carers_allowance_earnings"] >= lower["carers_allowance_earnings"] - 0.01
    )
    if lower["is_gainfully_employed_for_carers_allowance"]:
        assert higher["is_gainfully_employed_for_carers_allowance"]


@settings(
    max_examples=6,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
)
@given(
    pay=st.floats(min_value=0, max_value=15_000),
    savings=money,
    private_pension=money,
)
def test_unearned_income_is_not_earnings(pay, savings, private_pension):
    alone = _person(pay, 0, 0)
    with_unearned = _person(pay, 0, 0, savings=savings, private_pension=private_pension)
    assert (
        abs(
            alone["carers_allowance_earnings"]
            - with_unearned["carers_allowance_earnings"]
        )
        < 0.01
    )
