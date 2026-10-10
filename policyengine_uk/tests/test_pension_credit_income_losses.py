"""A loss on one income source does not reduce Pension Credit income (#2255).

State Pension Credit Act 2002 s. 15(1) and the State Pension Credit
Regulations 2002 reg. 15 list the receipts that count as income. Nothing lets
a negative amount on one be set against another.
"""

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation

YEAR = 2026


def _pension_credit(pension: float, property_income: float) -> tuple[float, float]:
    sim = Simulation(
        situation={
            "people": {
                "person": {
                    "age": {YEAR: 75},
                    "private_pension_income": {YEAR: pension},
                    "property_income": {YEAR: property_income},
                }
            },
            "benunits": {"benunit": {"members": ["person"]}},
            "households": {
                "household": {
                    "members": ["person"],
                    "region": {YEAR: "WALES"},
                    "tenure_type": {YEAR: "OWNED_OUTRIGHT"},
                }
            },
        }
    )
    return (
        float(sim.calculate("pension_credit_income", YEAR)[0]),
        float(sim.calculate("pension_credit", YEAR)[0]),
    )


pensions = st.integers(min_value=0, max_value=40_000)
losses = st.integers(min_value=-100_000, max_value=0)
gains = st.integers(min_value=0, max_value=20_000)


@settings(max_examples=12, deadline=None)
@given(pension=pensions, loss=losses)
def test_a_property_loss_counts_as_nil(pension, loss):
    assert _pension_credit(pension, loss) == pytest.approx(
        _pension_credit(pension, 0), abs=0.01
    )


@settings(max_examples=12, deadline=None)
@given(pension=pensions, lower=losses, extra=gains)
def test_pension_credit_never_rises_with_property_income(pension, lower, extra):
    _, credit_lower = _pension_credit(pension, lower)
    _, credit_higher = _pension_credit(pension, lower + extra)
    assert credit_higher <= credit_lower + 0.01


def test_issue_2255_reproducer():
    income, credit = _pension_credit(20_000, -30_000)
    assert income == pytest.approx(18_514, abs=1)
    assert credit == 0
