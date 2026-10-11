"""High Income Child Benefit Charge rounding (ITEPA 2003 s. 681C(3)).

The charge is the appropriate percentage of the Child Benefit concerned:
(ANI - L) / X percent, capped at 100% (s. 681C(2); L = £60,000 and X = £200
from 2024-25). Subsection (3) rounds the Child Benefit total and the charge
down to whole pounds, and the percentage down to a whole number.

Invariants, for any adjusted net income and Child Benefit:

1. The charge is a whole number of pounds.
2. Bounds: 0 <= charge <= Child Benefit rounded down to pounds.
3. Differential: the charge equals floor(floor((ANI - L) / X) / 100 x floor(CB))
   with the percentage capped at 100, computed here from the statute in
   integer arithmetic.
4. Monotonic: a higher income never lowers the charge.
5. The model's charge from a full simulation matches the statute.
"""

import numpy as np
from hypothesis import given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation
from policyengine_uk.utils.child_benefit import (
    child_benefit_charge_percentage,
    round_down_to_pounds,
)

L = 60_000
X = 200
END = L + 100 * X


def statutory_charge(ani_pounds: int, child_benefit_pence: int) -> int:
    """s. 681C in integer arithmetic: whole pounds, whole percentage points."""
    if ani_pounds <= L:
        return 0
    points = min(100, (ani_pounds - L) // X)
    pounds = child_benefit_pence // 100
    return (points * pounds) // 100


def model_charge(ani: float, child_benefit: float) -> float:
    percentage = child_benefit_charge_percentage(np.array([ani]), L, END)
    return float(
        round_down_to_pounds(percentage * round_down_to_pounds(child_benefit))[0]
    )


incomes = st.integers(min_value=0, max_value=200_000)
benefit_pence = st.integers(min_value=0, max_value=1_000_000)


@settings(max_examples=500, deadline=None)
@given(ani=incomes, cb_pence=benefit_pence)
def test_charge_matches_the_statute(ani, cb_pence):
    child_benefit = cb_pence / 100
    charge = model_charge(ani, child_benefit)
    assert charge == int(charge)
    assert 0 <= charge <= cb_pence // 100
    assert charge == statutory_charge(ani, cb_pence)


@settings(max_examples=300, deadline=None)
@given(
    ani=incomes, rise=st.integers(min_value=0, max_value=50_000), cb_pence=benefit_pence
)
def test_a_higher_income_never_lowers_the_charge(ani, rise, cb_pence):
    child_benefit = cb_pence / 100
    assert model_charge(ani + rise, child_benefit) >= model_charge(ani, child_benefit)


@settings(max_examples=8, deadline=None)
@given(pay=st.integers(min_value=55_000, max_value=90_000), children=st.integers(1, 3))
def test_simulated_charge_matches_the_statute(pay, children):
    people = {"parent": {"age": {"2026": 40}, "employment_income": {"2026": pay}}}
    for i in range(children):
        people[f"child{i}"] = {"age": {"2026": 3 + i}}
    members = list(people)
    sim = Simulation(
        situation={
            "people": people,
            "benunits": {"b": {"members": members}},
            "households": {"h": {"members": members, "country": {"2026": "ENGLAND"}}},
        }
    )
    ani = float(sim.calculate("adjusted_net_income", 2026)[0])
    child_benefit = float(sim.calculate("child_benefit", 2026)[0])
    charge = float(sim.calculate("CB_HITC", 2026)[0])
    assert charge == statutory_charge(int(ani), round(child_benefit * 100))
