"""Personal Savings Allowance, ITA 2007 s. 12B.

A Scottish taxpayer's higher- and additional-rate income is what would be
charged at those rates if they were not a Scottish taxpayer (s. 12B(8)(a)(iv)
and (b)(iv)), so the allowance follows the rest-of-UK bands for everyone.

Invariants, for single adults in 2026 with pay, savings interest and
dividends drawn freely:

1. Country: the allowance is the same for a Scottish and an English taxpayer
   with the same income.
2. Differential: it equals the statute computed independently here: £1,000
   when taxable income is at or under the £37,700 basic rate limit, £500 at
   or under the £125,140 higher rate limit, and nil above (ITA 2007 s. 10(2)-
   (3)), with taxable income as total income less the personal allowance,
   tapered by £1 for every £2 of income over £100,000.
3. Monotonic: a higher pay never raises the allowance.
"""

import numpy as np
from hypothesis import HealthCheck, example, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation

YEAR = 2026
PEOPLE = 12
money = st.integers(min_value=0, max_value=300_000)
small = st.integers(min_value=0, max_value=20_000)
incomes = st.lists(st.tuples(money, small, small), min_size=PEOPLE, max_size=PEOPLE)


def _allowances(rows, country):
    """One single-adult household per row, all in one simulation."""
    people, benunits, households = {}, {}, {}
    for i, (pay, savings, dividends) in enumerate(rows):
        name = f"p{i}"
        people[name] = {
            "age": {YEAR: 40},
            "employment_income": {YEAR: pay},
            "savings_interest_income": {YEAR: savings},
            "dividend_income": {YEAR: dividends},
        }
        benunits[f"b{i}"] = {"members": [name]}
        households[f"h{i}"] = {"members": [name], "country": {YEAR: country}}
    simulation = Simulation(
        situation={"people": people, "benunits": benunits, "households": households}
    )
    return np.asarray(simulation.calculate("savings_allowance", YEAR))


BOUNDARY_ROWS = [
    (49_270, 1_000, 0),  # taxable 37,700: at the basic rate limit
    (49_271, 1_000, 0),  # taxable 37,701
    (124_140, 1_000, 0),  # taxable 125,140 (allowance tapered to nil)
    (124_141, 1_000, 0),  # taxable 125,141
] + [(0, 0, 0)] * (PEOPLE - 4)


def _statute(pay, savings, dividends):
    income = pay + savings + dividends
    allowance = max(0, 12_570 - max(0, income - 100_000) / 2)
    taxable = income - allowance
    if taxable > 125_140:
        return 0
    if taxable > 37_700:
        return 500
    return 1_000


@settings(
    max_examples=10,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
)
@given(rows=incomes)
@example(rows=BOUNDARY_ROWS)
def test_scottish_and_english_taxpayers_get_the_same_allowance(rows):
    scottish = _allowances(rows, "SCOTLAND")
    english = _allowances(rows, "ENGLAND")
    assert np.array_equal(scottish, english)
    assert list(scottish) == [_statute(*row) for row in rows]


@settings(
    max_examples=10,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
)
@given(rows=incomes, rise=st.integers(min_value=1, max_value=100_000))
def test_a_higher_pay_never_raises_the_allowance(rows, rise):
    before = _allowances(rows, "SCOTLAND")
    after = _allowances([(pay + rise, s, d) for pay, s, d in rows], "SCOTLAND")
    assert np.all(after <= before)
