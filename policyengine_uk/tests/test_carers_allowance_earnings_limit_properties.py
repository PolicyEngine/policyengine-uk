"""Carer's Allowance earnings limit.

SSCBA 1992 s. 70(1)(b) bars a person who is gainfully employed, and reg. 8(1)
of the Social Security (Invalid Care Allowance) Regulations 1976 treats a
person as gainfully employed when their earnings exceed the limit (£204 a
week from 6 April 2026). Earnings are net of income tax, primary Class 1 (or,
for trading profit, Class 4) contributions and half of pension contributions
(Computation of Earnings Regulations 1996 regs. 10(4), 13 and 14; reg. 14(2)(a),
which deducted Class 2, was omitted from 6 April 2024).

A fraction of a penny counts in the claimant's favour (reg. 5): it is
disregarded in pay, profit and net earnings, and counts as a penny in each
deduction. So the half penny of half an odd-pence pension contribution (reg.
10(4)(b)) counts as a penny off earnings, as does the fraction of a penny in
a notional tax or Class 4 deduction. (PAYE and Class 1 are in law the amounts
actually deducted; the model's figures for them are rounded up the same way.)
carers_allowance_earnings applies that to each step, in float64 pence from the
whole pence each amount was entered as (stored_pence), so net earnings are
whole pence despite float32 storage. The test then reads back the whole
pence, disregarding any fraction in an amount entered directly, and compares
the whole pence a week, after dividing by 52 (regs. 8(1)(b)(iii) and
11(1)(a)) with the fraction disregarded, with the limit. _over_limit restates
the test in exact rational arithmetic.

Invariants, for a carer in England in 2026 caring 35 hours or more, with pay,
trading profit, employee pension contributions and unearned income drawn
freely:

1. Bounds: 0 <= carers_allowance_earnings <= pay + max(0, profit).
2. Differential: the test is passed exactly when _over_limit is false for the
   stored carers_allowance_earnings, and the allowance is the full rate then
   and nil otherwise.
3. Monotonic in steps of 2p: raising pay or profit by 2p or more never lowers
   net earnings, so a person over the limit stays over it. The deductions
   that rise with pay (PAYE and Class 1) or with profit (notional tax and
   Class 4) have marginal rates adding to at most a half, and each is rounded
   up, so a rise of R pence adds less than R / 2 + 2 pence to them, which is
   at most R when R >= 2. A rise of 1p can lower net earnings by 1p, when it
   takes both deductions to their next penny at once. That is reg. 5 working
   as intended, not an error (YAML Cases 30 and 31 pin one such pair).
4. Unearned income is not earnings: savings interest and pension income
   leave carers_allowance_earnings unchanged.

Invariants of the test itself, for every limit in every year from 2015 to
the parameter horizon, with carers_allowance_earnings entered directly:

5. Whole pence are judged exactly: annual earnings of A pence are over the
   limit L exactly when A // 52 > 100 x L, that is A >= 52 x (100 x L + 1),
   whatever float32 does to A. So 52 x L + £0.51 a year is within the limit
   and 52 x L + £0.52 (a penny a year more, and a penny a week over) is over
   it.
6. Exact arithmetic: for any stored amount, whole pence or not, the formula
   agrees with _over_limit.
7. Monotonic in earnings: more earnings never take a person from over the
   limit to within it.

And through the model, with pay or profit and a pension contribution entered
in whole pence:

8. Half of a pension contribution comes off pay, its half penny counting as a
   penny (regs. 10(4)(b) and 5): in each year up to the latest limit's first,
   pay of P pence below the personal allowance and the primary threshold,
   with a contribution of C pence, is over the limit L exactly when
   (P - ceil(C / 2)) // 52 > 100 x L.
9. Each deduction counts a fraction of a penny as a penny (reg. 5): with tax
   and Class 1 or Class 4 to pay, from 2024-25 (Class 2 nil, Class 1 at 8%),
   net earnings are P less each of the tax, the contributions and half the
   pension contribution, rounded up to a whole penny, exactly. Class 1 is 8%
   of P less 52 x £241.73, worked exactly here, not read from the model's
   float32 ni_class_1_employee, which can lie a hundredth of a penny from it.
10. A pension total entered directly as pension_contributions comes off
    earnings as the same amount entered as a programme does.

And for the amounts the deductions start from:

11. Class 1 is the amount the model calculates: where it calculated
    ni_class_1_employee with its own formula, as it does in every year from
    2015 to the horizon, including under a parameter reform, the deduction
    is that formula worked exactly. Where Class 1 (for the year or month by
    month) or its primary part was supplied as an input, or a reform
    neutralized or replaced the formula, the deduction is the stored amount,
    as the amount deducted (reg. 10(4)(a)), even within a fraction of a penny
    of what the formula would give.
12. Sums the model forms are read in whole pence: pay, NI income and pension
    contributions, which the model adds from other amounts in float32, are
    the exact sums of their whole-penny parts, and net earnings follow
    exact arithmetic on them.
13. An amount calculated by a formula in place of a sum is read as stored.
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
from policyengine_uk.model_api import GBP, MONTH, YEAR, Person, Reform, Variable
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
    with the limit for it: up to the year of the file's last value, the value
    in force on 30 April, after that year's April up-rating; after that, the
    model's, which may project the limit beyond the last legislated one."""
    limits = []
    for year in range(LIMIT_VALUES[0][0].year, last_year + 1):
        if year <= LIMIT_VALUES[-1][0].year:
            in_force = [
                v for date, v in LIMIT_VALUES if date <= datetime.date(year, 4, 30)
            ]
            limit = in_force[-1]
        else:
            limit = system.parameters(
                f"{year}-01-01"
            ).gov.dwp.carers_allowance.earnings_limit
        limits.append((year, limit))
    return limits


# Every year from the first limit to the horizon.
LIMITS_BY_YEAR = _limits_by_year(HORIZON)
# The same, up to the year the last legislated limit took effect.
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


def _stored_pence(value):
    """A stored float32 amount in exact pence: the whole pence it lies within
    half a float32 step of, or else its exact value."""
    pence = Fraction(float(value)) * 100
    whole = round(pence)
    if abs(pence - whole) <= Fraction(float(np.spacing(np.float32(value)))) * 50:
        return Fraction(whole)
    return pence


def _over_limit(earnings, limit=LIMIT):
    # The formula's rule in exact rational arithmetic, on the stored value:
    # the whole pence a year it lies within half a float32 step of, or else
    # its pence with the fraction disregarded, then whole pence a week, the
    # fraction disregarded (reg. 5), compared with the limit. £10,608.52 a
    # year, stored as 10,608.51953125, is 1,060,852 pence a year and 20,401
    # pence (£204.01) a week, a penny over £204. 10,608.517578125 (the
    # float32 just below it) is more than half a step from any whole penny,
    # so 1,060,851 pence and £204.00 a week, within £204.
    annual = math.floor(_stored_pence(earnings))
    return annual // WEEKS > Fraction(str(limit)) * 100


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
# no real loss and no earnings between a few pence and the limit.
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
    £10,608.52, the only whole pence within half a float32 step; see #2541."""
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
    year it applies, and the model's limit in each later year to the horizon,
    with carers_allowance_earnings entered directly. Before #2541 the formula
    counted pence in float32 and treated 52 x L + £0.52 as within the 2020-21
    to 2024-25 limits (£128, £132, £139 and £151)."""
    assert {limit for _, limit in SET_YEARS} == {v for _, v in LIMIT_VALUES}
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
    1p contribution is 52 x L + £0.515, and reg. 5 counts the half penny
    deducted as a penny, leaving 52 x L + £0.51, within the limit. Float32
    would hold £7,852.515 as 7,852.51513671875, just above it, so earnings
    taken to the nearest penny after the deduction would be over."""
    misjudged = []
    for year, limit in SET_YEARS:
        pairs = [(WEEKS * limit + extra, c) for extra, c, _ in ODD_PENCE_CONTRIBUTIONS]
        earnings, gainful = _pay_less_pension(year, pairs)
        for (pay, contribution), (_, _, over), stored, judged in zip(
            pairs, ODD_PENCE_CONTRIBUTIONS, earnings, gainful
        ):
            # Earnings are pay less half of the contribution rounded up to a
            # whole penny, as float32 holds them.
            net = round(pay * 100) - math.ceil(round(contribution * 100) / 2)
            assert stored == np.float32(net / 100), (
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


def _with_fractions(route, year):
    """Whole-pence pay or profit P and pension contributions C (odd and even
    pence) whose net earnings, deductions unrounded, lie from 4p below to 2p
    above the threshold B = 52 x (100 L + 1) pence a year. Returns B and
    (P, C) pairs in pence. Trading: profit above the personal allowance and
    the lower profits limit, so notional basic-rate tax and Class 4 at the
    main rate. Employee: pay above the primary threshold, less a contribution
    that leaves it below the personal allowance, so Class 1 and no PAYE (an
    employee paying PAYE is over every limit, each below the personal
    allowance)."""
    hmrc = system.parameters(f"{year}-01-01").gov.hmrc
    limit = system.parameters(f"{year}-01-01").gov.dwp.carers_allowance.earnings_limit
    threshold = WEEKS * (round(limit * 100) + 1)
    pa = Fraction(str(hmrc.income_tax.allowances.personal_allowance.amount)) * 100
    class_4 = hmrc.national_insurance.class_4
    lpl = Fraction(str(class_4.thresholds.lower_profits_limit)) * 100
    basic = Fraction(str(hmrc.income_tax.rates.uk.rates[0]))
    main = Fraction(str(class_4.rates.main))
    # Class 1 at 8% of pay above £12,570, to choose pay near the threshold.
    pt, class_1 = 1_257_000, Fraction(8, 100)
    if route == "trading":
        keep = 1 - basic - main
        first = 2 * (keep * max(pa, lpl) + basic * pa + main * lpl - threshold)
        offset = basic * pa + main * lpl
    else:
        keep = 1 - class_1
        first = 2 * (pt - threshold)
        offset = class_1 * pt
    pairs = []
    for contribution in range(
        math.ceil(first) + 1_001, math.ceil(first) + 401_000, 9_973
    ):
        const = offset - Fraction(contribution, 2)
        low = math.ceil((threshold - 4 - const) / keep)
        high = math.floor((threshold + 2 - const) / keep)
        pairs += [(p, contribution) for p in range(low, high + 1)]
    return threshold, pairs


# Pairs found in review of #2543, in pence. C1 (juaristi22): a trader within
# the limit whom the earlier nearest-half-penny rule put over it. The
# employees' Class 1 is a whole number of pence (£175.56, £235.38, £1.14,
# £1.26, £2.28) that the model's float32 sum of twelve months holds more than
# half a step out, so reading it with stored_pence and rounding up deducted a
# penny too much and put each of them, exactly a penny a week over, within
# the limit.
REVIEW_PAIRS = {
    ("trading", 2026): [(1_400_001, 603_938)],
    ("employee", 2024): [(1_476_446, 1_347_276), (1_551_221, 1_484_862)],
    ("employee", 2026): [
        (1_476_446, 796_076),
        (1_551_221, 933_662),
        (1_258_421, 394_910),
        (1_258_571, 395_186),
        (1_259_846, 397_532),
    ],
}


@pytest.mark.parametrize("route", ["trading", "employee"])
@pytest.mark.parametrize("year", [2024, 2026])
def test_each_deduction_counts_a_fraction_of_a_penny_as_a_penny(route, year):
    """Invariant 9, through the model: net earnings are P less each
    deduction rounded up to a whole penny (reg. 5), exactly, and the person
    is over the limit exactly when that reaches the threshold. Class 1 is
    worked exactly from its rate and threshold. Rounding only the total, or
    not at all, misjudges some of these pairs, and so does rounding up the
    model's float32 Class 1 (REVIEW_PAIRS)."""
    threshold, pairs = _with_fractions(route, year)
    review_pairs = REVIEW_PAIRS.get((route, year), [])
    pairs += review_pairs
    gross, contribution = (
        ("self_employment_income", "personal_pension_contributions")
        if route == "trading"
        else ("employment_income", "employee_pension_contributions")
    )
    people = {
        f"carer_{i}": {
            "age": {year: 45},
            "care_hours": {year: 40},
            gross: {year: p / 100},
            contribution: {year: c / 100},
        }
        for i, (p, c) in enumerate(pairs)
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
    class_1 = simulation.calculate("ni_class_1_employee", year)
    hmrc = system.parameters(f"{year}-01-01").gov.hmrc
    pa = Fraction(str(hmrc.income_tax.allowances.personal_allowance.amount)) * 100
    lpl = (
        Fraction(str(hmrc.national_insurance.class_4.thresholds.lower_profits_limit))
        * 100
    )
    basic = Fraction(str(hmrc.income_tax.rates.uk.rates[0]))
    main = Fraction(str(hmrc.national_insurance.class_4.rates.main))
    # Class 1 at 8% above 52 weeks of £241.73 (the model's £12,569.96), as
    # employee_scale.yaml sets for both years.
    employee_scale = hmrc.national_insurance.class_1.employee_scale
    assert employee_scale.components[1].rate == 0.08
    assert employee_scale.components[1].threshold == 241.73
    class_1_rate, primary_threshold = Fraction(8, 100), WEEKS * 24_173
    fractions = 0
    for (p, c), stored, judged, ni in zip(pairs, earnings, gainful, class_1):
        if route == "trading":
            assert max(pa, lpl) <= p and ni == 0, (p, c)
            deductions = [basic * (p - pa), main * (p - lpl)]
        else:
            assert p - c < pa and ni > 0, (p, c)
            deductions = [class_1_rate * (p - primary_threshold)]
        deductions.append(Fraction(c, 2))
        net = p - sum(math.ceil(d) for d in deductions)
        fractions += any(d.denominator > 1 for d in deductions)
        assert stored == np.float32(net / 100), (p, c, float(stored), net)
        assert bool(judged) == (net >= threshold), (p, c, net)
    # Most pairs carry a fraction of a penny in some deduction.
    assert fractions > len(pairs) // 2
    if route == "employee":
        # Each review pair is exactly the threshold: a penny a week over.
        for (p, c), judged in zip(
            review_pairs, gainful[len(pairs) - len(review_pairs) :]
        ):
            net = (
                p
                - math.ceil(class_1_rate * (p - primary_threshold))
                - math.ceil(Fraction(c, 2))
            )
            assert net == threshold and judged, (p, c, net)
    if route == "trading" and year == 2026:
        # C1: £14,000.01 of profit and a £6,039.38 premium. Tax £286.002 and
        # Class 4 £85.8006 round up to £286.01 and £85.81, and half the
        # premium is £3,019.69, leaving £10,608.50: £204.00 a week, within the
        # limit, so the full £4,495.40 a year is paid.
        assert float(earnings[-1]) == 10_608.5 and not gainful[-1]
        allowance = simulation.calculate("carers_allowance", year)[-1]
        assert abs(float(allowance) - RATE * WEEKS) < 0.01


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


# The stored amounts either side of 52L + £0.52, the least whole pence a year
# over the limit: the float32 nearest it is those pence, and the one below it
# is more than half a step away, so a fraction of a penny short.
EDGES = {limit: _float32_either_side(WEEKS * limit + 0.52) for limit in (139, 204)}


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
# The stored amounts either side of 52L + £0.52, for a limit #2541 affected
# and one it did not.
@example(case=(2023, 139, EDGES[139]))
@example(case=(2026, 204, EDGES[204]))
# 2026-27: 10,608.515625 and 10,608.517578125, a fraction of a penny short of
# £10,608.52 (the second is the earnings of juaristi22's review case under
# the earlier nearest-half-penny rule), and 10,608.5205078125, just over it.
@example(case=(2026, 204, [10_608.515625, 10_608.517578125, 10_608.5205078125]))
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


def _net_pence(variable, pence, other=None):
    """carers_allowance_earnings in whole pence in 2026, one carer in England
    per amount of ``variable`` (in pence), with ``other`` amounts as well."""
    amounts = {2026: [p / 100 for p in pence]}
    simulation = _carers(variable, amounts)
    for name, value in (other or {}).items():
        simulation.set_input(name, 2026, np.full(len(pence), value))
    earnings = simulation.calculate("carers_allowance_earnings", 2026)
    gainful = simulation.calculate("is_gainfully_employed_for_carers_allowance", 2026)
    return np.round(earnings.astype(np.float64) * 100).astype(int), gainful


# Every penny across the points where a deduction starts or changes rate in
# 2026-27: the personal allowance and Class 1 primary threshold and lower
# profits limit (£12,570), the higher rate, upper earnings limit and upper
# profits limit (£50,270) and the additional rate (£125,140); and, for
# profit, the boundary pair of YAML Cases 30 and 31.
MONOTONIC_RANGES = {
    "employment_income": [
        (1_255_000, 1_259_000),
        (5_025_000, 5_029_000),
        (12_512_000, 12_516_000),
    ],
    "self_employment_income": [(1_255_000, 1_259_000), (5_025_000, 5_029_000)],
}


@pytest.mark.parametrize("variable", list(MONOTONIC_RANGES))
def test_net_earnings_never_fall_for_a_rise_of_two_pence_or_more(variable):
    """Invariant 3, for every penny in each range: net earnings at P + R are
    at least those at P for every R >= 2p, and a 1p rise lowers them by at
    most 1p. Some 1p rises do, as reg. 5 intends."""
    one_penny_falls = 0
    for start, end in MONOTONIC_RANGES[variable]:
        pence = list(range(start, end))
        net, _ = _net_pence(variable, pence)
        # The least net earnings at any P + R, R >= 2, for each P.
        later_minimum = np.minimum.accumulate(net[::-1])[::-1]
        assert np.all(later_minimum[2:] >= net[:-2]), (variable, start)
        steps = np.diff(net)
        assert steps.min() >= -1, (variable, start)
        one_penny_falls += int(np.sum(steps == -1))
    if variable == "self_employment_income":
        assert one_penny_falls > 0


def test_a_penny_more_profit_can_lower_net_earnings_by_a_penny():
    """The intended exception to invariant 3, with a premium of £3,923.70:
    £12,570.50 of profit takes notional tax of 10p and Class 4 of 3p, leaving
    £10,608.52, a penny a week over the limit; £12,570.51 takes 10.2p and
    3.06p, which count as 11p and 4p (reg. 5), leaving £10,608.51, within
    it. Pinned also as YAML Cases 30 and 31."""
    net, gainful = _net_pence(
        "self_employment_income",
        [1_257_050, 1_257_051],
        {"personal_pension_contributions": 3_923.70},
    )
    assert list(net) == [1_060_852, 1_060_851]
    assert list(gainful) == [True, False]


@pytest.mark.parametrize(
    "pay, total",
    [(1_100_000, 100_000), (1_100_103, 99_201), (785_253, 1), (1_060_853, 1)],
)
def test_a_pension_total_entered_directly_counts_like_a_programme(pay, total):
    """Invariant 10: pension_contributions entered as a total comes off
    earnings, half of it with the half penny counted as a penny, exactly as
    the same amount entered as personal_pension_contributions (which, like the
    total, leaves PAYE alone)."""
    results = []
    for name in ("pension_contributions", "personal_pension_contributions"):
        net, gainful = _net_pence("employment_income", [pay], {name: total / 100})
        results.append((int(net[0]), bool(gainful[0])))
    assert results[0] == results[1]
    if pay < 1_257_000:
        assert results[0][0] == pay - math.ceil(total / 2)


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


def _earnings_of(rows, reform=None, year=2026):
    """Net earnings in whole pence, and whether each is over the limit, for
    one carer in England per dict in ``rows``: inputs by variable, each an
    amount for ``year`` or a dict of amounts by period."""
    people = {}
    for i, row in enumerate(rows):
        person = {"age": {year: 45}, "care_hours": {year: 40}}
        for name, value in row.items():
            person[name] = value if isinstance(value, dict) else {year: value}
        people[f"carer_{i}"] = person
    simulation = Simulation(
        situation={
            "people": people,
            "benunits": {
                f"b{i}": {"members": [f"carer_{i}"]} for i in range(len(rows))
            },
            "households": {
                f"h{i}": {"members": [f"carer_{i}"], "country": {year: "ENGLAND"}}
                for i in range(len(rows))
            },
        },
        reform=reform,
    )
    earnings = simulation.calculate("carers_allowance_earnings", year)
    gainful = simulation.calculate("is_gainfully_employed_for_carers_allowance", year)
    return [int(round(float(e) * 100)) for e in earnings], [bool(g) for g in gainful]


# The 2026-27 threshold: 52 x (£204 + 1p) a year, a penny a week over.
THRESHOLD_2026 = WEEKS * (LIMIT * 100 + 1)
MONTHS_2026 = [f"2026-{month:02d}" for month in range(1, 13)]


def _class_1(pence):
    """Class 1 at 8% of pay above the model's £12,569.96 in 2026, exactly."""
    return Fraction(8, 100) * max(0, pence - WEEKS * 24_173)


@pytest.mark.parametrize(
    "class_1_input",
    [
        {"ni_class_1_employee": 0},
        {"ni_class_1_employee": {month: 0 for month in MONTHS_2026}},
        {"ni_class_1_employee_primary": {month: 0 for month in MONTHS_2026}},
    ],
    ids=["year", "months", "primary part"],
)
def test_class_1_supplied_as_an_input_is_deducted_as_supplied(class_1_input):
    """Invariant 11, for an input. £12,569.97 of pay is a penny above the
    model's primary threshold, so its formula gives Class 1 of 0.08p, which
    counts as a penny. Entered as nil, nil is deducted (reg. 10(4)(a)): with
    a £3,922.90 contribution, £12,569.97 less £1,961.45 leaves £10,608.52, a
    penny a week over the limit."""
    pay, contribution = 1_256_997, 392_290
    row = {
        "employment_income": pay / 100,
        "employee_pension_contributions": contribution / 100,
    }
    # Separate simulations: an input set for one person is set for each.
    calculated, calculated_over = _earnings_of([row])
    supplied, supplied_over = _earnings_of([{**row, **class_1_input}])
    assert calculated == [pay - math.ceil(_class_1(pay)) - contribution // 2]
    assert supplied == [pay - contribution // 2]
    assert calculated + supplied == [1_060_851, 1_060_852]
    assert calculated_over + supplied_over == [False, True]


def test_class_1_supplied_near_its_formula_is_deducted_as_supplied():
    """Invariant 11: £594.40 of Class 1 entered with £20,000 of pay, within a
    third of a penny of what the formula gives (£594.4032), is the amount
    deducted, not the formula's rounded up."""
    pay = 2_000_000
    paye = math.ceil(Fraction(20, 100) * (pay - 1_257_000))
    calculated, _ = _earnings_of([{"employment_income": pay / 100}])
    supplied, _ = _earnings_of(
        [{"employment_income": pay / 100, "ni_class_1_employee": 594.40}]
    )
    assert calculated == [pay - paye - math.ceil(_class_1(pay))]
    assert supplied == [pay - paye - 59_440]


class _NoClass1(Reform):
    def apply(self):
        self.neutralize_variable("ni_class_1_employee")


class _NoPrimaryClass1(Reform):
    """The primary part replaced by a formula giving nil."""

    def apply(self):
        class ni_class_1_employee_primary(Variable):
            label = "NI Class 1 employee-side primary contributions"
            entity = Person
            definition_period = MONTH
            value_type = float
            unit = GBP

            def formula(person, period, parameters):
                return person("ni_class_1_income", period) * 0

        self.replace_variable(ni_class_1_employee_primary)


@pytest.mark.parametrize("reform", [_NoClass1, _NoPrimaryClass1])
def test_class_1_under_a_reform_of_its_formula_is_the_amount_calculated(reform):
    """Invariant 11, for a reform: with Class 1 neutralized, or its primary
    part replaced by a nil formula, nothing is deducted, not the 0.08p (a
    penny) the model's own formula gives at £12,569.97 of pay."""
    row = {"employment_income": 12_569.97, "employee_pension_contributions": 3_922.90}
    net, gainful = _earnings_of([row], reform=reform)
    assert net == [1_060_852] and gainful == [True]


@pytest.mark.parametrize(
    "reform, rate",
    [
        # The upper earnings limit moved far above this pay: Class 1 is still
        # £175.56, which the model's float32 sum holds as 175.5600128.
        (
            {
                "gov.hmrc.national_insurance.class_1.employee_scale[2].threshold": {
                    "2026-01-01.2100-12-31": 1_000
                }
            },
            Fraction(8, 100),
        ),
        # A main rate of 10%: £219.45 exactly.
        (
            {
                "gov.hmrc.national_insurance.class_1.employee_scale[1].rate": {
                    "2026-01-01.2100-12-31": 0.1
                }
            },
            Fraction(10, 100),
        ),
    ],
    ids=["upper earnings limit", "main rate"],
)
def test_class_1_under_a_parameter_reform_is_worked_exactly(reform, rate):
    """Invariant 11: a parameter reform changes the formula's parameters, not
    the formula, so Class 1 is still worked exactly, with them."""
    pay = 1_476_446
    paye = math.ceil(Fraction(20, 100) * (pay - 1_257_000))
    class_1 = math.ceil(rate * (pay - WEEKS * 24_173))
    net, _ = _earnings_of([{"employment_income": pay / 100}], reform=reform)
    assert net == [pay - paye - class_1]


class _NIIncomeFormula(Reform):
    """ni_class_1_income calculated by a formula rather than as a sum."""

    def apply(self):
        class ni_class_1_income(Variable):
            label = "NI Class 1 income"
            entity = Person
            definition_period = YEAR
            value_type = float
            unit = GBP

            def formula(person, period, parameters):
                return person("employment_income", period)

        self.replace_variable(ni_class_1_income)


def test_a_formula_in_place_of_a_sum_is_read_as_stored():
    """Invariant 13 (found in review): with ni_class_1_income calculated by a
    formula giving the same amount, £14,764.46 of pay still leaves
    £14,764.46 less PAYE of £438.90 and Class 1 of £175.56."""
    net, _ = _earnings_of([{"employment_income": 14_764.46}], reform=_NIIncomeFormula)
    assert net == [1_415_000]


def test_the_model_calculates_class_1_with_its_own_formula_in_every_year():
    """Invariant 11, for the baseline: in every year from 2015 to the
    horizon, no reform the model applies by default changes how Class 1 is
    calculated, so the deduction is its formula worked exactly. The formula
    is restated here in exact arithmetic, month by month, from the same
    parameters: the main rate between the primary threshold and the upper
    earnings limit and the additional rate above it, weekly thresholds as
    52 / 12 of a week a month. NI income is the pay entered plus the
    haircut the model calculates from 2029 (salary sacrifice cap costs
    spread over all pay), read as stored."""
    from policyengine_core.periods import MONTH as month_unit
    from policyengine_core.periods import period as make_period

    from policyengine_uk.variables.gov.dwp.carers_allowance_earnings import (
        _class_1_calculated,
        _primary_class_1,
    )

    pays = [1_476_446, 6_000_000, 15_000_017]
    for year in range(2015, HORIZON + 1):
        simulation = _carers("employment_income", {year: [p / 100 for p in pays]})
        person = simulation.populations["person"]
        period = make_period(year)
        simulation.calculate("ni_class_1_employee", year)
        assert _class_1_calculated(person, period), year
        worked = _primary_class_1(
            person, period, simulation.tax_benefit_system.parameters
        )
        haircuts = simulation.calculate("salary_sacrifice_broad_base_haircut", year)
        for pay, haircut, value in zip(pays, haircuts, worked):
            income = pay + Fraction(float(haircut)) * 100
            exact = Fraction(0)
            for month in period.get_subperiods(month_unit):
                scale = simulation.tax_benefit_system.parameters(
                    month
                ).gov.hmrc.national_insurance.class_1.employee_scale
                monthly = income / 12
                pt, uel = (
                    Fraction(str(scale.components[i].threshold)) * 100 * WEEKS / 12
                    for i in (1, 2)
                )
                main, additional = (
                    Fraction(str(scale.components[i].rate)) for i in (1, 2)
                )
                exact += main * (min(max(monthly, pt), uel) - pt) + additional * max(
                    monthly - uel, 0
                )
            # Within 10^-5p: a haircut within half a float32 step of a whole
            # penny is read as that penny, which moves Class 1 by far less.
            assert abs(Fraction(float(value)) - exact) < Fraction(1, 10**5), (
                year,
                pay,
                float(value),
                float(exact),
            )


def _natural_rows(rng, count, above_threshold):
    """Inputs the model sums, in whole pence, chosen so that the legal net
    earnings lie within 3p of the 2026-27 threshold: pay before labour supply
    responses a, salary sacrifice returned to pay b (also a member
    contribution), reported employee contributions r, personal contributions
    q and statutory sick pay s (NI income, not pay). Below the primary
    threshold there is no PAYE or Class 1; above it, Class 1 on a + b + s."""
    rows, nets = [], []
    while len(rows) < count:
        b, s = int(rng.integers(0, 200_000)), int(rng.integers(0, 50_000))
        r, q = int(rng.integers(0, 300_000)), int(rng.integers(0, 100_000))
        target = THRESHOLD_2026 + int(rng.integers(-3, 4))
        # Pay that leaves net earnings at the target, given the deductions.
        half = math.ceil(Fraction(r + b + q, 2))
        pay = target + half
        if above_threshold:
            # Net = pay - ceil(8% of (pay + s - PT)) - half, with no PAYE
            # while pay less member contributions stays below the allowance.
            pay = math.ceil(
                (target + half - Fraction(8, 100) * (WEEKS * 24_173 - s))
                / Fraction(92, 100)
            )
        a = pay - b
        if a <= 0:
            continue
        employee = r + b
        if above_threshold and not (
            pay + s > WEEKS * 24_173 and pay - employee < 1_257_000
        ):
            continue
        if not above_threshold and (pay + s > WEEKS * 24_173 or pay > 1_257_000):
            continue
        net = pay - math.ceil(_class_1(pay + s)) - half
        rows.append(
            {
                "employment_income_before_lsr": a / 100,
                "salary_sacrifice_returned_to_income": b / 100,
                "employee_pension_contributions_reported": r / 100,
                "personal_pension_contributions": q / 100,
                "statutory_sick_pay": s / 100,
            }
        )
        nets.append(net)
    return rows, nets


@pytest.mark.parametrize("above_threshold", [False, True], ids=["no NI", "Class 1"])
def test_sums_the_model_forms_are_read_in_whole_pence(above_threshold):
    """Invariant 12: pay (employment_income, which adds pay before labour
    supply responses and returned salary sacrifice), NI income (which adds
    statutory sick pay), employee pension contributions (reported plus
    returned salary sacrifice) and pension_contributions (the programmes) are
    the exact sums of their whole-penny parts, however float32 rounds the
    model's sums, and the limit test follows net earnings exactly."""
    rows, nets = _natural_rows(np.random.default_rng(2543), 600, above_threshold)
    if not above_threshold:
        # From review: returned pay and contributions of 20p, and of £1,435.15.
        rows += [
            {
                "employment_income_before_lsr": 10_608.96,
                "salary_sacrifice_returned_to_income": 0.20,
                "employee_pension_contributions_reported": 1.08,
            },
            {
                "employment_income_before_lsr": 10_794.69,
                "salary_sacrifice_returned_to_income": 1_435.15,
                "employee_pension_contributions_reported": 1_807.49,
            },
            # Pay of £11,692.11, which float32 holds as 11,692.109375.
            {
                "employment_income_before_lsr": 10_276.42,
                "salary_sacrifice_returned_to_income": 1_415.69,
                "employee_pension_contributions_reported": 751.49,
            },
        ]
        nets += [THRESHOLD_2026] * 3
    net, gainful = _earnings_of(rows)
    wrong = [(row, n, e) for row, n, e in zip(rows, net, nets) if n != e]
    assert not wrong, wrong[:3]
    assert gainful == [n >= THRESHOLD_2026 for n in nets]
