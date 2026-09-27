"""Property tests for the trading allowance (ITTOIA 2005 Part 7A, Chapter 1).

self_employment_income is profit after actual expenses. The allowance is an
alternative to those expenses, so the model may only add the part of the
allowance that actual deductions have not already used. These tests check
that invariant against an independent statutory reference, plus bounds and
monotonicity, over many generated cases in one reusable simulation.
"""

import numpy as np
import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation

YEAR = 2027
ALLOWANCE = 1_000
OTHER_EMPLOYMENT_INCOME = [0, 8_000, 30_000, 60_000, 110_000, 200_000]
CASES = 24  # Each case is simulated twice: as drawn, and with more profit.
PEOPLE = 2 * CASES

amount = st.one_of(
    st.floats(min_value=0, max_value=2_500),
    st.floats(min_value=0, max_value=300_000),
    st.sampled_from([0.0, 999.99, 1_000.0, 1_000.01, 12_570.0, 50_270.0]),
)
case = st.tuples(
    amount,  # profit, net of actual expenses
    amount,  # actual expenses
    st.sampled_from([0.0, 0.0, 150.0, 900.0, 5_000.0]),  # capital allowances
    st.booleans(),  # whether gross receipts are supplied
    st.floats(min_value=0, max_value=20_000),  # extra profit for monotonicity
)
cases = st.lists(case, min_size=CASES, max_size=CASES)


@pytest.fixture(scope="module")
def sim():
    people = {
        f"person_{i}": {
            "age": {YEAR: 40},
            "employment_income": {
                YEAR: OTHER_EMPLOYMENT_INCOME[i % CASES % len(OTHER_EMPLOYMENT_INCOME)]
            },
            "self_employment_income": {YEAR: 0},
            "self_employment_gross_receipts": {YEAR: 0},
            "capital_allowances": {YEAR: 0},
        }
        for i in range(PEOPLE)
    }
    return Simulation(
        situation={
            "people": people,
            "benunits": {
                f"benunit_{i}": {"members": [f"person_{i}"]} for i in range(PEOPLE)
            },
            "households": {
                f"household_{i}": {"members": [f"person_{i}"]} for i in range(PEOPLE)
            },
        }
    )


def run(sim, drawn):
    profit, expenses, capital_allowances, known, extra = map(np.array, zip(*drawn))
    profit = np.concatenate([profit, profit + extra])
    expenses = np.concatenate([expenses, expenses])
    capital_allowances = np.concatenate([capital_allowances, capital_allowances])
    known = np.concatenate([known, known])
    receipts = np.where(known, profit + expenses, 0)
    sim.set_input("self_employment_income", YEAR, profit)
    sim.set_input("self_employment_gross_receipts", YEAR, receipts)
    sim.set_input("capital_allowances", YEAR, capital_allowances)
    sim.reset_calculations()
    # Compare against the stored (float32) inputs, not the float64 draws.
    profit = sim.calculate("self_employment_income", YEAR).astype(float)
    receipts = sim.calculate("self_employment_gross_receipts", YEAR).astype(float)
    capital_allowances = sim.calculate("capital_allowances", YEAR).astype(float)
    return dict(
        profit=profit,
        expenses=np.maximum(receipts - profit, 0),
        capital_allowances=capital_allowances,
        receipts=receipts,
        known=receipts > 0,
        relief=sim.calculate("trading_allowance_deduction", YEAR),
        taxable=sim.calculate("taxable_self_employment_income", YEAR),
        income_tax=sim.calculate("income_tax", YEAR),
    )


def statutory_taxable_profit(receipts, expenses, capital_allowances):
    """Taxable trade profit under Part 7A when receipts are known.

    Receipts within the allowance are fully relieved. Above it, the person
    takes the better of actual deductions (expenses and capital allowances)
    and the allowance; the two never stack.
    """
    return np.where(
        receipts <= ALLOWANCE,
        0,
        np.maximum(0, receipts - np.maximum(expenses + capital_allowances, ALLOWANCE)),
    )


def unknown_receipts_taxable_profit(profit, capital_allowances):
    """Fallback when receipts are unknown: full relief only for a profit
    within the allowance; a larger profit is taxed as reported."""
    return np.where(profit <= ALLOWANCE, 0, np.maximum(0, profit - capital_allowances))


def tolerance(*values):
    """A penny plus float32 rounding on the amounts involved."""
    return 0.01 + 1e-6 * sum(np.abs(v) for v in values)


SETTINGS = settings(
    max_examples=40,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
)


@SETTINGS
@given(cases)
def test_relief_is_bounded_by_allowance_and_profit(sim, drawn):
    r = run(sim, drawn)
    assert (r["relief"] >= 0).all()
    assert (r["relief"] <= ALLOWANCE + tolerance(ALLOWANCE)).all()
    assert (r["relief"] <= r["profit"] + tolerance(r["profit"])).all()


@SETTINGS
@given(cases)
def test_taxable_profit_matches_statutory_reference(sim, drawn):
    r = run(sim, drawn)
    expected = np.where(
        r["known"],
        statutory_taxable_profit(r["receipts"], r["expenses"], r["capital_allowances"]),
        unknown_receipts_taxable_profit(r["profit"], r["capital_allowances"]),
    )
    assert (
        np.abs(r["taxable"] - expected) <= tolerance(r["receipts"], r["profit"])
    ).all()


@SETTINGS
@given(cases)
def test_allowance_never_stacks_on_actual_deductions(sim, drawn):
    r = run(sim, drawn)
    known = r["known"] & (r["receipts"] > ALLOWANCE)
    deducted_from_receipts = r["receipts"] - r["taxable"]
    actual_deductions = r["expenses"] + r["capital_allowances"]
    limit = np.maximum(actual_deductions, ALLOWANCE) + tolerance(r["receipts"])
    assert (deducted_from_receipts[known] <= limit[known]).all()


@SETTINGS
@given(cases)
def test_income_tax_is_non_decreasing_in_profit(sim, drawn):
    r = run(sim, drawn)
    base, more = r["income_tax"][:CASES], r["income_tax"][CASES:]
    assert (more >= base - tolerance(base)).all()
