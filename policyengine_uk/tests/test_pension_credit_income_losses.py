"""A loss on one income source does not reduce Pension Credit income (#2255).

State Pension Credit Act 2002 ss. 15 to 16 and the State Pension Credit
Regulations 2002 regs. 15 to 18 say what counts as income. Nothing in them
lets a negative amount on one source be set against another, and for earnings
the Computation of Earnings Regulations 1996 reg. 13(12), applied by SPC
Regulations reg. 17B(5)(b), says so: "any loss incurred in any one of his
employments shall not be offset against his earnings in any other of his
employments".
"""

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation

YEAR = 2026
INPUTS = (
    "private_pension_income",
    "property_income",
    "employment_income",
    "self_employment_income",
)


def _pension_credit(cases: list[dict]) -> list[tuple[float, float]]:
    """Pension Credit income and award for single pensioners, one per case.

    Each case gives annual amounts for any of INPUTS; the rest are nil. All
    the cases go into one simulation, which costs about the same as one.
    """
    people, benunits, households = {}, {}, {}
    for i, case in enumerate(cases):
        people[f"person_{i}"] = {
            "age": {YEAR: 75},
            **{name: {YEAR: case.get(name, 0)} for name in INPUTS},
        }
        benunits[f"benunit_{i}"] = {"members": [f"person_{i}"]}
        households[f"household_{i}"] = {
            "members": [f"person_{i}"],
            "region": {YEAR: "WALES"},
            "tenure_type": {YEAR: "OWNED_OUTRIGHT"},
        }
    sim = Simulation(
        situation={
            "people": people,
            "benunits": benunits,
            "households": households,
        }
    )
    income = sim.calculate("pension_credit_income", YEAR)
    credit = sim.calculate("pension_credit", YEAR)
    return [(float(a), float(b)) for a, b in zip(income, credit)]


amounts = st.integers(min_value=0, max_value=40_000)
losses = st.integers(min_value=-100_000, max_value=0)
property_incomes = st.integers(min_value=-100_000, max_value=20_000)


def batches(*strategies):
    return st.lists(st.tuples(*strategies), min_size=1, max_size=8)


def _paired(cases: list[dict], baselines: list[dict]):
    """Results for each case beside its baseline, from one simulation."""
    results = _pension_credit(cases + baselines)
    return zip(results[: len(cases)], results[len(cases) :])


@settings(max_examples=5, deadline=None)
@given(batch=batches(amounts, losses))
def test_a_property_loss_counts_as_nil(batch):
    pairs = _paired(
        [
            {"private_pension_income": pension, "property_income": loss}
            for pension, loss in batch
        ],
        [{"private_pension_income": pension} for pension, _ in batch],
    )
    for with_loss, without in pairs:
        assert with_loss == pytest.approx(without, abs=0.01)


@settings(max_examples=5, deadline=None)
@given(batch=batches(amounts, property_incomes))
def test_pension_credit_is_never_higher_than_with_no_property_income(batch):
    # Not monotonicity in general: the model's property allowance makes
    # Pension Credit step up between two positive property incomes.
    pairs = _paired(
        [
            {"private_pension_income": pension, "property_income": amount}
            for pension, amount in batch
        ],
        [{"private_pension_income": pension} for pension, _ in batch],
    )
    for (_, credit), (_, credit_without) in pairs:
        assert credit <= credit_without + 0.01


@settings(max_examples=5, deadline=None)
@given(batch=batches(amounts, amounts, losses))
def test_a_self_employment_loss_counts_as_nil(batch):
    pairs = _paired(
        [
            {
                "private_pension_income": pension,
                "employment_income": wages,
                "self_employment_income": loss,
            }
            for pension, wages, loss in batch
        ],
        [
            {"private_pension_income": pension, "employment_income": wages}
            for pension, wages, _ in batch
        ],
    )
    for with_loss, without in pairs:
        assert with_loss == pytest.approx(without, abs=0.01)


def test_issue_2255_reproducers():
    (property_loss, trading_loss) = _pension_credit(
        [
            {"private_pension_income": 20_000, "property_income": -30_000},
            {"employment_income": 10_000, "self_employment_income": -8_000},
        ]
    )
    # 20,000 less income tax of 20% of (20,000 - 12,570).
    assert property_loss == (pytest.approx(18_514, abs=1), 0)
    # 238 x 52 = 12,376, less wages of 10,000.
    assert trading_loss == (
        pytest.approx(10_000, abs=1),
        pytest.approx(2_376, abs=1),
    )
