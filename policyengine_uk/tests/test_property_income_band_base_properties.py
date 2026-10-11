"""Savings and dividends sit above all non-savings income (ITA 2007 s. 16).

Property income is non-savings income, so it fills the bands before savings
and dividends, as pay does.

Invariants, for single adults in 2026 with pay, property income, savings
interest and dividends drawn freely:

1. Differential: replacing property income with pay equal to its taxable
   amount leaves savings and dividend tax unchanged, in England and in
   Scotland. (The taxable amount, because the £1,000 property allowance can
   relieve small property income in full.)
2. Accounting: non_savings_taxable_income equals adjusted net income less
   savings, dividends and allowances, floored at nil.
3. Monotonic: more property income never lowers savings or dividend tax.
"""

import numpy as np
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation

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
        - v["taxable_savings_interest_income"]
        - v["taxable_dividend_income"]
        - v["allowances"],
    )
    np.testing.assert_allclose(v["non_savings_taxable_income"], expected, atol=0.01)


@SETTINGS
@given(rows=rows_strategy, rise=st.integers(min_value=1, max_value=100_000))
def test_more_property_income_never_lowers_savings_or_dividend_tax(rows, rise):
    before = _calculate(rows, "ENGLAND")
    after = _calculate(
        [(pay, prop + rise, s, d) for pay, prop, s, d in rows], "ENGLAND"
    )
    for name in ["savings_income_tax", "dividend_income_tax"]:
        assert np.all(after[name] >= before[name] - 0.01)
