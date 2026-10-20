"""Carer's Allowance earnings limit.

SSCBA 1992 s. 70(1)(b) bars a person who is gainfully employed, and reg. 8(1)
of the Social Security (Invalid Care Allowance) Regulations 1976 treats a
person as gainfully employed when their earnings exceed the limit (£204 a
week from 6 April 2026). Earnings are net of income tax, primary Class 1 (or,
for trading profit, Class 4) contributions and half of pension contributions
(Computation of Earnings Regulations 1996 regs. 10(4), 13 and 14; reg. 14(2)(a),
which deducted Class 2, was omitted from 6 April 2024).

Invariants, for a carer in England in 2026 caring 35 hours or more, with pay,
trading profit, employee pension contributions and unearned income drawn
freely:

1. Bounds: 0 <= carers_allowance_earnings <= pay + max(0, profit).
2. Differential: the test is passed exactly when
   carers_allowance_earnings / 52, with a fraction of a penny disregarded
   (Computation of Earnings Regulations 1996 reg. 5), is at most 204, and the
   allowance is the full rate then and nil otherwise. The pence are counted
   in the precision the model stores earnings in (float32), as the formula
   counts them.
3. Monotonic: raising pay never lowers net earnings, so a person over the
   limit stays over it.
4. Unearned income is not earnings: savings interest and pension income
   leave carers_allowance_earnings unchanged.
"""

import numpy as np
import pytest
from hypothesis import HealthCheck, example, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation
from policyengine_uk.utils.class_2 import class_2_contribution_weeks

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
    # Keep each variable's stored dtype: the reg. 5 check must count pence in
    # the precision the formula does. Tolerance checks convert with float().
    return {
        name: np.asarray(sim.calculate(name, 2026))[0]
        for name in (
            "carers_allowance_earnings",
            "is_gainfully_employed_for_carers_allowance",
            "carers_allowance",
        )
    }


def _over_limit(earnings):
    # Regulation 5: a fraction of a penny is disregarded. ``earnings`` is the
    # stored value, so this counts the pence as
    # is_gainfully_employed_for_carers_allowance does, in float32: promoting
    # to float64 first floors 10,608.52 a year, stored as 10,608.51953125, to
    # 204.00 a week instead of 204.01.
    return np.floor(earnings / WEEKS * 100 + 1e-6) / 100 > LIMIT


money = st.floats(min_value=0, max_value=60_000, allow_nan=False)
profit_money = st.floats(min_value=-20_000, max_value=60_000, allow_nan=False)


@settings(
    max_examples=12,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow],
)
@given(pay=money, profit=profit_money, pension_share=st.floats(0, 0.3))
# Exactly at the 2026-27 limit (10,608 / 52 = 204.00): not gainfully employed.
@example(pay=10_608.0, profit=0.0, pension_share=0.0)
# One penny a week over it (10,608.52 / 52 = 204.01), on the float32 boundary
# described in _over_limit: gainfully employed.
@example(pay=10_608.52, profit=0.0, pension_share=0.0)
# A trading loss, with earnings below the limit: the derandomized draws have
# neither.
@example(pay=8_000.0, profit=-5_000.0, pension_share=0.1)
def test_bounds_and_differential(pay, profit, pension_share):
    pension = pay * pension_share
    result = _person(pay, profit, pension)
    earnings = result["carers_allowance_earnings"]
    assert -0.01 <= float(earnings) <= pay + max(0, profit) + 0.01
    over = _over_limit(earnings)
    assert bool(result["is_gainfully_employed_for_carers_allowance"]) == over
    expected = 0 if over else RATE * WEEKS
    assert abs(float(result["carers_allowance"]) - expected) < 0.01


@pytest.mark.parametrize("pay, gainful", [(10_608.00, False), (10_608.52, True)])
def test_a_penny_a_week_over_the_2026_limit_ends_entitlement(pay, gainful):
    """£10,608 a year is £204.00 a week, at the limit; £10,608.52 is £204.01, a
    penny over it. This pins the outcome for the amount entered, not only
    agreement with _over_limit. The model stores £10,608.52 as 10,608.51953125
    (£204.00 a week in exact arithmetic) and reaches £204.01 through float32
    rounding; see #2541."""
    result = _person(pay, 0, 0)
    assert bool(result["is_gainfully_employed_for_carers_allowance"]) == gainful
    expected = 0 if gainful else RATE * WEEKS
    assert abs(float(result["carers_allowance"]) - expected) < 0.01


@settings(
    max_examples=8,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow],
)
@given(pay=money, rise=st.floats(min_value=1, max_value=20_000))
def test_net_earnings_never_fall_as_pay_rises(pay, rise):
    lower = _person(pay, 0, 0)
    higher = _person(pay + rise, 0, 0)
    assert (
        float(higher["carers_allowance_earnings"])
        >= float(lower["carers_allowance_earnings"]) - 0.01
    )
    if lower["is_gainfully_employed_for_carers_allowance"]:
        assert higher["is_gainfully_employed_for_carers_allowance"]


@settings(
    max_examples=6,
    deadline=None,
    derandomize=True,
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
            float(alone["carers_allowance_earnings"])
            - float(with_unearned["carers_allowance_earnings"])
        )
        < 0.01
    )


@pytest.mark.parametrize("year", [2016, 2017, 2018, 2026])
@pytest.mark.parametrize("country", ["ENGLAND", "SCOTLAND"])
def test_trading_profit_takes_the_basic_rate_in_every_year(year, country):
    """Reg. 14(1): the basic rate, or for a Scottish taxpayer the Scottish
    basic rate, which were both 20% in each of these years. Before 2018-19 the
    Scottish scale has no starter rate, so reading its second bracket by
    position at an instant would pick the higher rate. Before 2024-25 reg.
    14(2)(a) also deducted Class 2: £30,000 is above the small profits
    threshold in each year, so a full year of the flat rate."""
    profit = 30_000
    simulation = Simulation(
        situation={
            "people": {
                "carer": {
                    "age": {year: 45},
                    "self_employment_income": {year: profit},
                    "care_hours": {year: 40},
                }
            },
            "benunits": {"family": {"members": ["carer"]}},
            "households": {"home": {"members": ["carer"], "country": {year: country}}},
        }
    )
    hmrc = simulation.tax_benefit_system.parameters(year).gov.hmrc
    allowance = hmrc.income_tax.allowances.personal_allowance.amount
    class_4 = hmrc.national_insurance.class_4
    class_2 = hmrc.national_insurance.class_2
    class_2_weeks = class_2_contribution_weeks(year)
    expected = (
        profit
        - 0.20 * (profit - allowance)
        - class_2.flat_rate * class_2_weeks
        - class_4.rates.main
        * (
            min(profit, class_4.thresholds.upper_profits_limit)
            - class_4.thresholds.lower_profits_limit
        )
    )
    assert bool(simulation.calculate("pays_scottish_income_tax", year)[0]) == (
        country == "SCOTLAND"
    )
    assert simulation.calculate("carers_allowance_earnings", year)[0] == pytest.approx(
        expected, abs=0.01
    )
