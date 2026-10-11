"""High Income Child Benefit Charge rounding (ITEPA 2003 s. 681C(3)).

The charge is the appropriate percentage of the Child Benefit concerned:
(ANI - L) / X percent, capped at 100% (s. 681C(2); L = £60,000 and X = £200
from 2024-25). Subsection (3) rounds the Child Benefit total and the charge
down to whole pounds, and the percentage down to a whole number.

Invariants, for any finite, nonnegative adjusted net income and Child Benefit:

1. The charge is a whole number of pounds.
2. Bounds: 0 <= charge <= Child Benefit rounded down to pounds.
3. Differential: the charge equals floor(points / 100 x floor(CB)), where
   points = min(100, max(0, floor((ANI - L) / X))), computed here from the
   statute in integer arithmetic.
4. Monotonic: with the Child Benefit fixed, a higher income never lowers the
   charge.
5. Precision: every exact £200 step, held as float32 as in a microsimulation,
   gives exactly that many points.
6. The model's charge from a full simulation matches the statute, with one to
   four children.
"""

import numpy as np
from hypothesis import given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation
from policyengine_uk.utils.scenario import Scenario
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
@given(pay=st.integers(min_value=55_000, max_value=90_000), children=st.integers(1, 4))
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


def test_every_exact_step_gives_exactly_its_points_in_float32():
    for points in range(0, 101):
        income = np.array([L + X * points], dtype=np.float32)
        assert child_benefit_charge_percentage(income, L, END)[0] == points / 100


def test_a_float32_annual_amount_is_taken_to_the_penny_first():
    # Four children's £4,199 accumulated by month and stored as float32.
    assert round_down_to_pounds(np.float32(4198.99951171875)) == 4199
    assert round_down_to_pounds(np.float32(1406.5999755859375)) == 1406


# Structural reforms are chosen when the simulation is built, so the switch has
# to be set before data load.
HOUSEHOLD_BASED = Scenario(
    applied_before_data_load=True,
    parameter_changes={"gov.contrib.conservatives.cb_hitc_household": {"2025": True}},
)


def _charge(pay: list[int], scenario=None) -> float:
    people = {
        f"parent{i}": {"age": {2026: 40}, "employment_income": {2026: p}}
        for i, p in enumerate(pay)
    }
    people["child"] = {"age": {2026: 5}}
    situation = {
        "people": people,
        "benunits": {"family": {"members": list(people)}},
        "households": {"home": {"members": list(people), "country": {2026: "ENGLAND"}}},
    }
    return float(
        Simulation(situation=situation, scenario=scenario)
        .calculate("CB_HITC", 2026)
        .sum()
    )


def test_the_household_based_reform_rounds_as_the_baseline_does():
    """A single parent's household income is their own, so the reform charges
    what the baseline does: 99% of £1,406 at £79,800 is £1,391, not £1,392.53."""
    assert _charge([79_800]) == 1_391
    assert _charge([79_800], HOUSEHOLD_BASED) == 1_391


def test_the_household_based_reform_charges_on_combined_income():
    """A couple on £50,000 and £30,000 pay nothing in the baseline; on £80,000
    combined the reform takes the whole Child Benefit, in whole pounds."""
    assert _charge([50_000, 30_000]) == 0
    assert _charge([50_000, 30_000], HOUSEHOLD_BASED) == 1_406
