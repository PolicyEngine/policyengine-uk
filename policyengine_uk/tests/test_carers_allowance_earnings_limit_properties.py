"""Carer's Allowance earnings limit.

SSCBA 1992 s. 70(1)(b) bars a person who is gainfully employed, and reg. 8(1)
of the Social Security (Invalid Care Allowance) Regulations 1976 treats a
person as gainfully employed when their earnings exceed the limit (£204 a
week from 6 April 2026). Earnings are net of income tax, primary Class 1 (or,
for trading profit, Class 4) contributions and half of pension contributions
(Computation of Earnings Regulations 1996 regs. 10(4), 13 and 14; reg. 14(2)(a),
which deducted Class 2, was omitted from 6 April 2024).

A fraction of a penny is disregarded where counting it would not favour the
claimant (reg. 5). Net earnings are whole pence less half of pension
contributions (reg. 10(4)(b)), so a whole number of half pence, and the half
penny of an odd-pence contribution counts as a penny off earnings, which
favours the claimant. The model holds annual earnings in float32, so the
formula first takes them to the nearest half penny, disregards a half penny,
then compares the whole pence a week, after dividing by 52 (reg. 8(1)(b)(iii))
with the fraction disregarded, with the limit. _over_limit restates that rule
in exact rational arithmetic.

Invariants, for a carer in England in 2026 caring 35 hours or more, with pay,
trading profit, employee pension contributions and unearned income drawn
freely:

1. Bounds: 0 <= carers_allowance_earnings <= pay + max(0, profit).
2. Differential: the test is passed exactly when _over_limit is false for the
   stored carers_allowance_earnings, and the allowance is the full rate then
   and nil otherwise.
3. Monotonic: raising pay never lowers net earnings, so a person over the
   limit stays over it.
4. Unearned income is not earnings: savings interest and pension income
   leave carers_allowance_earnings unchanged.

Invariants of the test itself, for every limit in earnings_limit.yaml in every
year it applies, with carers_allowance_earnings entered directly:

5. Whole pence are judged exactly: annual earnings of A pence are over the
   limit L exactly when A // 52 > 100 x L, that is A >= 52 x (100 x L + 1),
   whatever float32 does to A. So 52 x L + £0.51 a year is within the limit
   and 52 x L + £0.52 (a penny a year more, and a penny a week over) is over
   it.
6. Exact arithmetic: for any stored amount, whole pence or not, the formula
   agrees with _over_limit.
7. Monotonic in earnings: more earnings never take a person from over the
   limit to within it.

And with pay and an employee pension contribution entered, in whole pence,
in each year up to the latest limit's first, where pay near the limit pays no
tax or NI:

8. Half of a pension contribution comes off pay, its half penny counting as a
   penny (regs. 10(4)(b) and 5): pay of P pence with a contribution of C
   pence is over the limit L exactly when (P - ceil(C / 2)) // 52 > 100 x L.
"""

import datetime
import math
from fractions import Fraction
from pathlib import Path

import numpy as np
import pytest
import yaml
from hypothesis import HealthCheck, example, given, settings
from hypothesis import strategies as st

import policyengine_uk
from policyengine_uk import Simulation
from policyengine_uk.system import system
from policyengine_uk.utils.class_2 import class_2_contribution_weeks

LIMIT = 204
RATE = 86.45
WEEKS = 52
LIMIT_FILE = (
    Path(policyengine_uk.__file__).parent
    / "parameters/gov/dwp/carers_allowance/earnings_limit.yaml"
)


LIMIT_VALUES = sorted(
    (date, entry["value"])
    for date, entry in yaml.safe_load(LIMIT_FILE.read_text())["values"].items()
)
# The last year the parameter tree lists a value for.
HORIZON = max(
    int(value.instant_str[:4])
    for value in system.parameters.gov.dwp.carers_allowance.earnings_limit.values_list
)


def _limits_by_year(last_year):
    """Each year from the first limit in earnings_limit.yaml to last_year,
    with the limit the file sets for it: the value in force on 30 April, after
    that year's April up-rating."""
    limits = []
    for year in range(LIMIT_VALUES[0][0].year, last_year + 1):
        in_force = [v for date, v in LIMIT_VALUES if date <= datetime.date(year, 4, 30)]
        limits.append((year, in_force[-1]))
    return limits


# Every year each limit applies, the last one up to the horizon.
LIMITS_BY_YEAR = _limits_by_year(HORIZON)
# The same, up to the year the last limit took effect.
SET_YEARS = _limits_by_year(LIMIT_VALUES[-1][0].year)


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
    # Keep each stored value as the formula reads it (float32 for amounts).
    # Tolerance checks convert with float(), which is exact.
    return {
        name: np.asarray(sim.calculate(name, 2026))[0]
        for name in (
            "carers_allowance_earnings",
            "is_gainfully_employed_for_carers_allowance",
            "carers_allowance",
        )
    }


def _over_limit(earnings, limit=LIMIT):
    # The formula's rule in exact rational arithmetic, on the stored value:
    # the nearest half penny a year (an exact quarter penny down), a half
    # penny disregarded, then whole pence a week, a fraction of a penny
    # disregarded (reg. 5), compared with the limit. £10,608.52 a year, stored
    # as 10,608.51953125, is 1,060,852 pence a year and 20,401 pence (£204.01)
    # a week, a penny over £204. £7,852.515 (pay of £7,852.52 less half of a
    # 1p contribution), stored as 7,852.51513671875, is 785,251 pence a year
    # and 15,100 pence (£151.00) a week, within £151.
    half_pence = math.ceil(Fraction(float(earnings)) * 200 - Fraction(1, 2))
    return half_pence // 2 // WEEKS > Fraction(str(limit)) * 100


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
# One penny a week over it (10,608.52 / 52 = 204.01), stored just below
# £10,608.52 as described in _over_limit: gainfully employed.
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
    (£204.00 a week in exact arithmetic), and the formula recovers the
    £10,608.52 by taking the nearest penny; see #2541."""
    result = _person(pay, 0, 0)
    assert bool(result["is_gainfully_employed_for_carers_allowance"]) == gainful
    expected = 0 if gainful else RATE * WEEKS
    assert abs(float(result["carers_allowance"]) - expected) < 0.01


def _carers(variable, amounts_by_year, reform=None):
    """One carer in England per amount, aged 45 and caring 40 hours a week,
    with ``variable`` set to that amount in each year."""
    years = list(amounts_by_year)
    count = len(amounts_by_year[years[0]])
    people = {
        f"carer_{i}": {
            "age": {year: 45 for year in years},
            "care_hours": {year: 40 for year in years},
            variable: {year: amounts_by_year[year][i] for year in years},
        }
        for i in range(count)
    }
    return Simulation(
        situation={
            "people": people,
            "benunits": {f"b{i}": {"members": [f"carer_{i}"]} for i in range(count)},
            "households": {
                f"h{i}": {
                    "members": [f"carer_{i}"],
                    "country": {year: "ENGLAND" for year in years},
                }
                for i in range(count)
            },
        },
        reform=reform,
    )


# A year's earnings at each limit, a penny a year short of £0.01 a week over
# it, and £0.01 a week over it: 52 x L + £0.51 is L + £0.0098 a week, which
# reg. 5 takes down to L.
PENNY_STEPS = ((0.0, False), (0.51, False), (0.52, True))


def _penny_steps_misjudged(variable, limits_by_year):
    amounts = {
        year: [WEEKS * limit + step for step, _ in PENNY_STEPS]
        for year, limit in limits_by_year
    }
    simulation = _carers(variable, amounts)
    misjudged = []
    for year, limit in limits_by_year:
        assert (
            system.parameters(f"{year}-01-01").gov.dwp.carers_allowance.earnings_limit
            == limit
        )
        earnings = simulation.calculate("carers_allowance_earnings", year)
        gainful = simulation.calculate(
            "is_gainfully_employed_for_carers_allowance", year
        )
        allowance = simulation.calculate("carers_allowance", year)
        for (step, over), amount, stored, judged, paid in zip(
            PENNY_STEPS, amounts[year], earnings, gainful, allowance
        ):
            # Earnings are the amount entered, as float32 holds it.
            assert stored == np.float32(amount), (year, amount, stored)
            if bool(judged) != over or (paid == 0) != over:
                misjudged.append((year, limit, amount, bool(judged), float(paid)))
    return misjudged


def test_a_penny_a_week_over_each_limit_is_over_it_in_every_year():
    """Reg. 8(1), after reg. 5, for every limit in earnings_limit.yaml in every
    year it applies, with carers_allowance_earnings entered directly. Before
    #2541 the formula counted pence in float32 and treated 52 x L + £0.52 as
    within the 2020-21 to 2024-25 limits (£128, £132, £139 and £151)."""
    assert {limit for _, limit in LIMITS_BY_YEAR} == {v for _, v in LIMIT_VALUES}
    assert _penny_steps_misjudged("carers_allowance_earnings", LIMITS_BY_YEAR) == []


def test_pay_a_penny_a_week_over_each_limit_ends_entitlement():
    """The same steps entered as pay, in each year up to the latest limit's
    first. 52 x L + £0.52 is below the personal allowance and the primary
    threshold in each of these years, so earnings are the pay itself, as the
    test checks. This is #2541's reproducer."""
    assert _penny_steps_misjudged("employment_income", SET_YEARS) == []


def _pay_less_pension(year, pairs):
    """Pay and an employee pension contribution for one carer each."""
    people = {
        f"carer_{i}": {
            "age": {year: 45},
            "care_hours": {year: 40},
            "employment_income": {year: pay},
            "employee_pension_contributions": {year: contribution},
        }
        for i, (pay, contribution) in enumerate(pairs)
    }
    simulation = Simulation(
        situation={
            "people": people,
            "benunits": {
                f"b{i}": {"members": [f"carer_{i}"]} for i in range(len(pairs))
            },
            "households": {
                f"h{i}": {"members": [f"carer_{i}"], "country": {year: "ENGLAND"}}
                for i in range(len(pairs))
            },
        }
    )
    earnings = simulation.calculate("carers_allowance_earnings", year)
    gainful = simulation.calculate("is_gainfully_employed_for_carers_allowance", year)
    return earnings, gainful


# Pay and an odd-pence pension contribution: (extra pay over 52 x L, the
# contribution, over the limit). Half of the contribution comes off pay
# (reg. 10(4)(b)), and its half penny counts as a penny (reg. 5), so the
# first three leave 52 x L + £0.51 and the last two 52 x L + £0.52.
ODD_PENCE_CONTRIBUTIONS = (
    (0.52, 0.01, False),
    (0.53, 0.03, False),
    (48.00, 94.97, False),
    (0.53, 0.01, True),
    (0.54, 0.03, True),
)


def test_half_an_odd_pence_pension_contribution_counts_as_a_penny_off():
    """Regs. 10(4)(b) and 5, for every limit in earnings_limit.yaml in each
    year up to the latest limit's first. Pay of 52 x L + £0.52 less half of a
    1p contribution is 52 x L + £0.515, which reg. 5 takes to 52 x L + £0.51,
    within the limit. Float32 holds that half penny just above it for most
    limits (£7,852.515 as 7,852.51513671875), so taking the nearest penny
    instead of the nearest half penny would put it over."""
    misjudged = []
    for year, limit in SET_YEARS:
        pairs = [(WEEKS * limit + extra, c) for extra, c, _ in ODD_PENCE_CONTRIBUTIONS]
        earnings, gainful = _pay_less_pension(year, pairs)
        for (pay, contribution), (_, _, over), stored, judged in zip(
            pairs, ODD_PENCE_CONTRIBUTIONS, earnings, gainful
        ):
            # Earnings are pay less half of the contribution, to within
            # float32's rounding of the inputs and the subtraction.
            assert abs(float(stored) - (pay - contribution / 2)) < 0.002, (
                year,
                pay,
                contribution,
                float(stored),
            )
            if bool(judged) != over:
                misjudged.append((year, limit, pay, contribution, bool(judged)))
    assert misjudged == []


@st.composite
def pay_and_contributions_around_a_limit(draw):
    year, limit = draw(st.sampled_from(SET_YEARS))
    # The least pence of earnings a year that is over the limit.
    over = WEEKS * (limit * 100 + 1)
    pairs = []
    for _ in range(draw(st.integers(1, 30))):
        contribution = draw(st.integers(0, 20_000))
        # Pay within a few pence of the boundary after the deduction, or
        # anywhere within £500 a year of the limit. Either way pay is below
        # the personal allowance and the primary threshold, so no tax or NI.
        boundary = over + math.ceil(contribution / 2)
        near = st.integers(boundary - 3, boundary + 3)
        anywhere = st.integers(
            WEEKS * limit * 100 - 50_000, WEEKS * limit * 100 + 50_000
        )
        pairs.append((draw(st.one_of(near, anywhere)), contribution))
    return year, limit, pairs


@settings(
    max_examples=10,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow],
)
@given(case=pay_and_contributions_around_a_limit())
# Odd-pence contributions on either side of the boundary in 2024-25.
@example(case=(2024, 151, [(785_252, 1), (785_253, 1), (785_253, 3), (785_254, 3)]))
def test_pay_less_half_a_pension_contribution_is_judged_as_the_law_says(case):
    """Invariant 8."""
    year, limit, pairs = case
    _, gainful = _pay_less_pension(year, [(p / 100, c / 100) for p, c in pairs])
    for (pay, contribution), judged in zip(pairs, gainful):
        net = pay - math.ceil(contribution / 2)
        assert bool(judged) == (net // WEEKS > limit * 100), (year, pay, contribution)


def test_a_limit_in_pounds_and_pence_is_read_exactly():
    """A reformed limit of £204.10 is 20,410 pence, not the 20,409.999...
    that 204.1 x 100 gives in floating point: £204.10 a week is within it and
    £204.11 is over it."""
    reform = {
        "gov.dwp.carers_allowance.earnings_limit": {"2026-01-01.2026-12-31": 204.1}
    }
    amounts = [WEEKS * 204.1, WEEKS * 204.1 + 0.51, WEEKS * 204.1 + 0.52]
    simulation = _carers("carers_allowance_earnings", {2026: amounts}, reform)
    gainful = simulation.calculate("is_gainfully_employed_for_carers_allowance", 2026)
    assert list(gainful) == [False, False, True]


@st.composite
def whole_pence_around_a_limit(draw):
    year, limit = draw(st.sampled_from(LIMITS_BY_YEAR))
    # The least number of pence a year that is over the limit.
    over = WEEKS * (limit * 100 + 1)
    near = st.integers(over - 3 * WEEKS, over + 3 * WEEKS)
    # Up to £131,071.99, below which float32 holds every whole-pence amount
    # to within half a penny.
    anywhere = st.integers(0, 2**17 * 100 - 1)
    pence = draw(st.lists(st.one_of(near, anywhere), min_size=1, max_size=40))
    return year, limit, pence


@settings(
    max_examples=10,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow],
)
@given(case=whole_pence_around_a_limit())
# Either side of the boundary in 2020-21 and 2024-25, where float32 pence
# misjudged the penny over (#2541).
@example(case=(2020, 128, [665_651, 665_652]))
@example(case=(2022, 132, [686_451, 686_452]))
@example(case=(2023, 139, [722_851, 722_852]))
@example(case=(2024, 151, [785_251, 785_252]))
def test_whole_pence_are_judged_exactly(case):
    """Invariant 5."""
    year, limit, pence = case
    simulation = _carers("carers_allowance_earnings", {year: [p / 100 for p in pence]})
    gainful = simulation.calculate("is_gainfully_employed_for_carers_allowance", year)
    for amount, judged in zip(pence, gainful):
        assert bool(judged) == (amount // WEEKS > limit * 100), (year, amount)


def _float32_either_side(amount):
    nearest = np.float32(amount)
    below = np.nextafter(nearest, np.float32(-np.inf))
    above = np.nextafter(nearest, np.float32(np.inf))
    return [float(below), float(nearest), float(above)]


EDGES = {
    limit: _float32_either_side(WEEKS * limit + 0.515)
    + _float32_either_side(WEEKS * limit + 0.5175)
    for limit in (139, 204)
}


@st.composite
def amounts_around_a_limit(draw):
    year, limit = draw(st.sampled_from(LIMITS_BY_YEAR))
    over = WEEKS * limit + 0.52
    near = st.floats(over - 0.05, over + 0.05)
    anywhere = st.floats(0, 100_000, allow_nan=False)
    amounts = draw(st.lists(st.one_of(near, anywhere), min_size=2, max_size=40))
    return year, limit, amounts


@settings(
    max_examples=10,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow],
)
@given(case=amounts_around_a_limit())
# 2022-23: £6,864.51 (within the £132 limit) and £6,864.52 (a penny a week
# over it), with amounts a tenth of a penny off them.
@example(case=(2022, 132, [6_864.509, 6_864.51, 6_864.511, 6_864.52, 6_864.521]))
# The stored amounts either side of 52L + £0.515 (a half penny, within the
# limit) and 52L + £0.5175 (where the nearest half penny turns from £0.515 to
# £0.52, over it), for a limit #2541 affected and one it did not.
@example(case=(2023, 139, EDGES[139]))
@example(case=(2026, 204, EDGES[204]))
def test_the_formula_matches_exact_arithmetic_and_rises_with_earnings(case):
    """Invariants 6 and 7, for amounts with any fraction of a penny."""
    year, limit, amounts = case
    simulation = _carers("carers_allowance_earnings", {year: amounts})
    stored = simulation.calculate("carers_allowance_earnings", year)
    gainful = simulation.calculate("is_gainfully_employed_for_carers_allowance", year)
    for value, judged in zip(stored, gainful):
        assert bool(judged) == _over_limit(value, limit), (year, float(value))
    in_order = gainful[np.argsort(stored, kind="stable")].astype(int)
    assert np.all(np.diff(in_order) >= 0), (year, amounts)


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
