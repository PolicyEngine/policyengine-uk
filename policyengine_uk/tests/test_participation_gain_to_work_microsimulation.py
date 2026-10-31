"""`calculate_gain_to_work` runs on a Microsimulation (#1836 follow-up).

A Microsimulation returns MicroSeries. The function used to assign into one
MicroSeries with a MicroSeries mask, which raised "Cannot propagate weights
unambiguously". It now works on plain arrays, so a Microsimulation and a
Simulation built from the same household give the same gain to work.
"""

import numpy as np
import pandas as pd

from policyengine_uk import Microsimulation, Simulation
from policyengine_uk.dynamics import participation as p

YEAR = 2025


def situation():
    """One couple: an earner and a non-earner, plus a child."""
    return {
        "people": {
            "earner": {
                "age": {str(YEAR): 34},
                "employment_income": {str(YEAR): 28_000},
                "hours_worked": {str(YEAR): 1_800},
            },
            "carer": {
                "age": {str(YEAR): 31},
                "employment_income": {str(YEAR): 0},
                "hours_worked": {str(YEAR): 0},
            },
            "child": {"age": {str(YEAR): 3}},
        },
        "benunits": {"family": {"members": ["earner", "carer", "child"]}},
        "households": {"home": {"members": ["earner", "carer", "child"]}},
    }


def gain_to_work(sim):
    result = p.calculate_gain_to_work(sim, YEAR, count_adults=2)
    return pd.DataFrame(result).reset_index(drop=True).astype(float)


def test_gain_to_work_runs_on_microsimulation_and_matches_simulation():
    micro = gain_to_work(Microsimulation(situation=situation()))
    plain = gain_to_work(Simulation(situation=situation()))
    pd.testing.assert_frame_equal(micro, plain)
    # Both adults gain from work; the child is not an adult and gains nothing.
    assert (micro["gain_to_work"].iloc[:2] > 0).all()
    assert micro["gain_to_work"].iloc[2] == 0


def test_microsimulation_employment_income_is_restored():
    sim = Microsimulation(situation=situation())
    before = np.asarray(sim.calculate("employment_income", YEAR)).copy()
    p.calculate_gain_to_work(sim, YEAR, count_adults=2)
    after = np.asarray(sim.calculate("employment_income", YEAR))
    np.testing.assert_array_equal(after, before)
