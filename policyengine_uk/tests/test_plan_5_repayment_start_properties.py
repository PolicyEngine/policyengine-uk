"""Plan 5 student loan repayments start on 6 April 2026.

SI 2009/470 reg. 15(2BA), inserted by SI 2022/1335 reg. 15(9): "Despite
paragraphs (2), (2A) and (2B), a borrower is not required to repay any part of
a plan 5 loan on or before 5th April 2026." Reg. 15(2BB) omits (2BA) on 6 April
2026. The model reads year Y's parameters at 30 April of Y, so the years 2015
to 2025 carry no Plan 5 liability and 2026 onwards do.

Each property draws borrowers on every plan, batched into one Simulation per
example, and compares the model with ``reference_repayment``: the formula
without a Plan 5 start date, which charges the plan's rate on repayment income
above the plan's threshold, capped by a positive balance.

Invariants:

1. P1: a Plan 5 borrower repays nothing in each year from 2015 to 2025, for
   any income and any balance.
2. P2: from 2026, every borrower's repayment equals the reference.
3. P3: a borrower on any plan other than Plan 5 repays the reference amount in
   every year from 2015.
4. P4: a repayment never falls below nil and never exceeds a positive balance.
"""

from unittest.mock import patch

import numpy as np
import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation
from policyengine_uk.tax_benefit_system import system

_PROPERTY_SYSTEM = system.clone()
PROPERTY_SETTINGS = settings(
    max_examples=25,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)
PLANS = ("NONE", "PLAN_1", "PLAN_2", "PLAN_4", "PLAN_5", "POSTGRADUATE")
THRESHOLD_KEYS = {
    "PLAN_1": "plan_1",
    "PLAN_2": "plan_2",
    "PLAN_4": "plan_4",
    "PLAN_5": "plan_5",
    "POSTGRADUATE": "postgraduate",
}
FIRST_YEAR = 2015
PLAN_5_FIRST_YEAR = 2026
LAST_YEAR = 2035

borrowers = st.lists(
    st.tuples(
        st.sampled_from(PLANS),
        st.integers(0, 300_000),
        # Zero means no balance is known, so no cap applies.
        st.one_of(st.just(0), st.integers(1, 100_000)),
    ),
    min_size=1,
    max_size=8,
)
plan_5_borrowers = st.lists(
    st.tuples(
        st.just("PLAN_5"),
        st.integers(0, 1_000_000),
        st.one_of(st.just(0), st.integers(1, 200_000)),
    ),
    min_size=1,
    max_size=8,
)


def simulate(people, year):
    """One Simulation with each (plan, employment income, balance) its own
    household."""
    situation = {"people": {}, "benunits": {}, "households": {}}
    for i, (plan, income, balance) in enumerate(people):
        name = f"p{i}"
        situation["people"][name] = {
            "age": {year: 30},
            "employment_income": {year: income},
            "student_loan_plan": {year: plan},
            "student_loan_balance": {year: balance},
        }
        situation["benunits"][f"b{i}"] = {"members": [name]}
        situation["households"][f"h{i}"] = {"members": [name]}
    with patch(
        "policyengine_uk.simulation.CountryTaxBenefitSystem",
        side_effect=_PROPERTY_SYSTEM.clone,
    ):
        return Simulation(situation=situation)


def reference_repayment(sim, people, year):
    """Repayments from the plan's rate and threshold alone, with no Plan 5
    start date."""
    p = sim.tax_benefit_system.parameters(str(year)).gov.hmrc.student_loans
    net_income = sim.calculate("net_income", year)
    benefits = np.minimum(
        sim.calculate("taxable_employment_income", year),
        sim.calculate("benefits_in_kind", year),
    )
    income = np.maximum(net_income - benefits, 0)
    out = []
    for (plan, _, balance), person_income in zip(people, income):
        if plan == "NONE":
            out.append(0.0)
            continue
        threshold = p.thresholds[THRESHOLD_KEYS[plan]]
        rate = (
            p.postgraduate_repayment_rate
            if plan == "POSTGRADUATE"
            else p.repayment_rate
        )
        repayment = rate * max(0.0, person_income - threshold)
        out.append(min(repayment, balance) if balance > 0 else repayment)
    return np.array(out)


@pytest.fixture(scope="module", autouse=True)
def _release_simulation():
    yield
    _PROPERTY_SYSTEM.simulation = None


@PROPERTY_SETTINGS
@given(
    people=plan_5_borrowers,
    year=st.integers(FIRST_YEAR, PLAN_5_FIRST_YEAR - 1),
)
def test_p1_plan_5_borrowers_repay_nothing_before_2026_27(people, year):
    sim = simulate(people, year)
    repayment = sim.calculate("student_loan_repayment", year)
    assert np.all(repayment == 0)


@PROPERTY_SETTINGS
@given(people=borrowers, year=st.integers(PLAN_5_FIRST_YEAR, LAST_YEAR))
def test_p2_every_plan_follows_threshold_and_rate_from_2026_27(people, year):
    sim = simulate(people, year)
    repayment = sim.calculate("student_loan_repayment", year)
    np.testing.assert_allclose(
        repayment, reference_repayment(sim, people, year), rtol=1e-6, atol=0.01
    )


@PROPERTY_SETTINGS
@given(
    people=borrowers.map(
        lambda people: [person for person in people if person[0] != "PLAN_5"]
    ).filter(bool),
    year=st.integers(FIRST_YEAR, LAST_YEAR),
)
def test_p3_other_plans_unchanged_in_every_year(people, year):
    sim = simulate(people, year)
    repayment = sim.calculate("student_loan_repayment", year)
    np.testing.assert_allclose(
        repayment, reference_repayment(sim, people, year), rtol=1e-6, atol=0.01
    )


@PROPERTY_SETTINGS
@given(people=borrowers, year=st.integers(FIRST_YEAR, LAST_YEAR))
def test_p4_repayment_is_bounded_by_nil_and_balance(people, year):
    sim = simulate(people, year)
    repayment = sim.calculate("student_loan_repayment", year)
    balance = np.array([person[2] for person in people], dtype=float)
    assert np.all(repayment >= 0)
    capped = balance > 0
    assert np.all(repayment[capped] <= balance[capped] + 1e-6)
