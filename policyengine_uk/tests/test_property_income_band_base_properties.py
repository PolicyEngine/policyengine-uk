"""Savings and dividends sit above all non-savings income (ITA 2007 s. 16).

Property income is non-savings income, so it fills the bands before savings
and dividends, as pay does.

Invariants, for single adults in 2026 with pay, property income, savings
interest and dividends drawn freely:

1. Differential: replacing property income with pay equal to its taxable
   amount leaves savings and dividend tax unchanged, in England and in
   Scotland. (The taxable amount, because the £1,000 property allowance can
   relieve small property income in full.)
2. Accounting: with no Marriage Allowance, non_savings_taxable_income equals
   adjusted net income less the allowances and the savings and dividends left
   after the allowances set against them, floored at nil
   (earned_taxable_income also subtracts Marriage Allowance; #1947). Under
   ITA 2007 s. 25(2) the model can set allowances against savings or
   dividends while non-savings income is left, so the savings and dividends
   left, not their full amounts, sit above it.
3. Monotonic: more property income never lowers the income tax. Savings or
   dividend tax alone can fall, because under s. 25(2) the model can move
   allowances from property income to savings as property income rises.
   (Main passes this too; the differential and the higher-rate check below
   are what catch the bug.)
"""

import numpy as np
import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation

pytestmark = pytest.mark.usefixtures("cloned_uk_tax_benefit_system")

YEAR = 2026
PEOPLE = 10
amount = st.integers(min_value=0, max_value=200_000)
rows_strategy = st.lists(
    st.tuples(amount, amount, st.integers(0, 60_000), st.integers(0, 60_000)),
    min_size=PEOPLE,
    max_size=PEOPLE,
)
VARIABLES = [
    "taxable_property_income",
    "savings_income_tax",
    "dividend_income_tax",
    "non_savings_taxable_income",
    "adjusted_net_income",
    "taxable_savings_interest_income",
    "taxable_dividend_income",
    "allowances",
    "received_allowances_savings_income",
    "received_allowances_dividend_income",
    "income_tax",
]


def _calculate(rows, country):
    """rows: (pay, property, savings, dividends), one single adult each."""
    people, benunits, households = {}, {}, {}
    for i, (pay, prop, savings, dividends) in enumerate(rows):
        name = f"p{i}"
        people[name] = {
            "age": {YEAR: 45},
            "employment_income": {YEAR: pay},
            "property_income": {YEAR: prop},
            "savings_interest_income": {YEAR: savings},
            "dividend_income": {YEAR: dividends},
        }
        benunits[f"b{i}"] = {"members": [name]}
        households[f"h{i}"] = {"members": [name], "country": {YEAR: country}}
    simulation = Simulation(
        situation={"people": people, "benunits": benunits, "households": households}
    )
    return {v: np.asarray(simulation.calculate(v, YEAR)) for v in VARIABLES}


SETTINGS = settings(
    max_examples=8,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
)


@SETTINGS
@given(rows=rows_strategy, country=st.sampled_from(["ENGLAND", "SCOTLAND"]))
def test_moving_income_between_pay_and_property_leaves_savings_and_dividend_tax(
    rows, country
):
    as_property = _calculate(rows, country)
    taxable_property = as_property["taxable_property_income"]
    as_pay = _calculate(
        [
            (pay + float(taxable), 0, s, d)
            for (pay, _, s, d), taxable in zip(rows, taxable_property)
        ],
        country,
    )
    for name in [
        "savings_income_tax",
        "dividend_income_tax",
        "non_savings_taxable_income",
    ]:
        np.testing.assert_allclose(as_property[name], as_pay[name], atol=0.01)


@SETTINGS
@given(rows=rows_strategy)
def test_non_savings_taxable_income_is_the_rest_after_allowances(rows):
    v = _calculate(rows, "ENGLAND")
    expected = np.maximum(
        0,
        v["adjusted_net_income"]
        - (
            v["taxable_savings_interest_income"]
            - v["received_allowances_savings_income"]
        )
        - (v["taxable_dividend_income"] - v["received_allowances_dividend_income"])
        - v["allowances"],
    )
    np.testing.assert_allclose(v["non_savings_taxable_income"], expected, atol=0.01)


@SETTINGS
@given(rows=rows_strategy, rise=st.integers(min_value=1, max_value=100_000))
def test_more_property_income_never_lowers_income_tax(rows, rise):
    before = _calculate(rows, "ENGLAND")
    after = _calculate(
        [(pay, prop + rise, s, d) for pay, prop, s, d in rows], "ENGLAND"
    )
    assert np.all(after["income_tax"] >= before["income_tax"] - 0.01)


def test_savings_above_property_income_past_the_basic_rate_limit_pay_the_higher_rate():
    """£40,000 of property income and £20,000 of savings. Under ITA 2007
    s. 25(2) the model sets £2,300 of the Personal Allowance against the
    property income, which leaves it at the £37,700 basic rate limit, and the
    other £10,270 against savings. All the savings left, £9,730, sit above the
    limit: £500 at the nil rate (s. 12A) and £9,230 at 40%, £3,692. Main once
    banded the savings as if the property income were not there and charged
    £2,900."""
    v = _calculate([(0, 40_000, 20_000, 0)] + [(0, 0, 0, 0)] * (PEOPLE - 1), "ENGLAND")
    np.testing.assert_allclose(v["savings_income_tax"][0], 9_230 * 0.40, atol=0.01)
    np.testing.assert_allclose(v["income_tax"][0], 37_700 * 0.20 + 3_692, atol=0.01)
    # Non-savings taxable income comes to 37,700, not 60,000 - 20,000 - 12,570
    # = 27,430: invariant 2 subtracts only the savings left.
    np.testing.assert_allclose(v["non_savings_taxable_income"][0], 37_700, atol=0.01)


def test_more_property_income_can_lower_savings_tax():
    """More property income can lower savings tax while income tax rises.
    With £30,000 of property income and £20,000 of savings, taxable income of
    £37,430 stays within the basic rate band, so the savings allowance comes
    to £1,000 (s. 12B(4)) and no share changes the tax: £19,000 of savings at
    20%, £3,800. £10,000 more property income gives the £3,692 of the test
    above: savings tax falls by £108 while income tax rises from £7,286 to
    £11,232."""
    before = _calculate([(0, 30_000, 20_000, 0)] * PEOPLE, "ENGLAND")
    after = _calculate([(0, 40_000, 20_000, 0)] * PEOPLE, "ENGLAND")
    np.testing.assert_allclose(before["savings_income_tax"], 3_800, atol=0.01)
    np.testing.assert_allclose(after["savings_income_tax"], 3_692, atol=0.01)
    np.testing.assert_allclose(before["income_tax"], 17_430 * 0.20 + 3_800, atol=0.01)
    np.testing.assert_allclose(after["income_tax"], 7_540 + 3_692, atol=0.01)
