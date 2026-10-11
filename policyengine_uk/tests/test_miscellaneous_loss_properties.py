"""A miscellaneous loss is relieved only against miscellaneous income
(ITA 2007 s. 152(4)).

Invariants, for any pay, savings, dividends and pension income:

1. A miscellaneous loss leaves Income Tax and adjusted net income exactly as
   they are with no miscellaneous income.
2. taxable_miscellaneous_income is never negative and equals the income when
   it is positive.
"""

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation


def _calc(misc, pay, savings, dividends, pension):
    situation = {
        "people": {
            "p": {
                "age": {"2026": 50},
                "employment_income": {"2026": pay},
                "savings_interest_income": {"2026": savings},
                "dividend_income": {"2026": dividends},
                "private_pension_income": {"2026": pension},
                "miscellaneous_income": {"2026": misc},
            }
        },
        "benunits": {"b": {"members": ["p"]}},
        "households": {"h": {"members": ["p"], "country": {"2026": "ENGLAND"}}},
    }
    sim = Simulation(situation=situation)
    return {
        name: float(sim.calculate(name, 2026)[0])
        for name in (
            "income_tax",
            "adjusted_net_income",
            "taxable_miscellaneous_income",
        )
    }


amounts = st.floats(min_value=0, max_value=150_000, allow_nan=False)


@settings(max_examples=10, deadline=None, suppress_health_check=[HealthCheck.too_slow])
@given(
    loss=st.floats(min_value=1, max_value=500_000, allow_nan=False),
    pay=amounts,
    savings=st.floats(min_value=0, max_value=20_000),
    dividends=st.floats(min_value=0, max_value=20_000),
    pension=st.floats(min_value=0, max_value=40_000),
)
def test_a_miscellaneous_loss_changes_nothing_else(
    loss, pay, savings, dividends, pension
):
    with_loss = _calc(-loss, pay, savings, dividends, pension)
    without = _calc(0, pay, savings, dividends, pension)
    assert with_loss["taxable_miscellaneous_income"] == 0
    assert abs(with_loss["income_tax"] - without["income_tax"]) < 0.01
    assert abs(with_loss["adjusted_net_income"] - without["adjusted_net_income"]) < 0.01


@settings(max_examples=6, deadline=None, suppress_health_check=[HealthCheck.too_slow])
@given(income=st.floats(min_value=0, max_value=100_000, allow_nan=False), pay=amounts)
def test_positive_miscellaneous_income_is_taxable_in_full(income, pay):
    result = _calc(income, pay, 0, 0, 0)
    assert abs(result["taxable_miscellaneous_income"] - income) < 0.01
