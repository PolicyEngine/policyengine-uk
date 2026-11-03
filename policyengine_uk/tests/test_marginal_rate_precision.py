"""Tests for marginal rates at large gains and earnings, issue #1979.

Marginal rates are finite differences: add a step to an input in a branch,
recompute household net income and divide the change by the step. Inputs and
net income are float32, whose spacing doubles with each power of two, so a
fixed £1,000 step read the 24% main rate of capital gains tax as 24.8% at
£185m of gains and 23.2% at £561m. The step is now £1,000 or 0.1% of the
input, whichever is larger, and the change in net income is divided by the
step as stored.

The per-case readings live in the YAML tests next to each variable. This file
covers what those cannot: a sweep across sizes of gain, the retention rate
change between a reform and its baseline, and the labour supply derivative.
"""

import math

import numpy as np
import pytest

from policyengine_uk import Microsimulation, Simulation
from policyengine_uk.dynamics.progression import calculate_derivative
from policyengine_uk.model_api import Scenario

YEAR = 2026

# A reading is now exact up to a few float32 roundings of the household's
# income, each at most 6e-5 of a 0.1% step: over 3,000 gains from £1m to
# £10bn the worst reading is 2e-4 off. The £1,000 step was 8e-3 off at £185m.
TOLERANCE = 3e-4

# Gains above the basic rate band, on the main schedule.
CGT_MAIN_RATE = 0.24


def simulate(rows, scenario=None, simulation_class=Simulation):
    """One single-adult London household per row of 2026 inputs."""
    people, benunits, households = {}, {}, {}
    for i, row in enumerate(rows):
        person = {"age": {YEAR: 50}}
        for variable, value in row.items():
            person[variable] = {YEAR: value}
        people[f"person_{i}"] = person
        benunits[f"benunit_{i}"] = {"members": [f"person_{i}"]}
        households[f"household_{i}"] = {
            "members": [f"person_{i}"],
            "region": {YEAR: "LONDON"},
        }
    situation = {"people": people, "benunits": benunits, "households": households}
    return simulation_class(situation=situation, scenario=scenario)


def test_capital_gains_main_rate_at_every_size_of_gain():
    """One adult on £200k of earnings, so every marginal pound of gains is
    charged at the 24% main rate.

    Net income has spacing changes of its own, at gains other than powers of
    two. The £1,000 step missed by more than the tolerance at 98 of these 200
    gains, the smallest £89m, and above £1bn read anything from -2.4% to 48.8%.
    """
    rows = [
        {"employment_income": 200_000, "capital_gains": float(gains)}
        for gains in np.geomspace(1e6, 1e10, 200)
    ]
    readings = simulate(rows).calculate("marginal_tax_rate_on_capital_gains", YEAR)
    assert np.abs(readings - CGT_MAIN_RATE).max() < TOLERANCE


@pytest.mark.parametrize("reformed_rate", [0.25, 0.45])
def test_retention_rate_change_at_large_gains(reformed_rate):
    """A rise from 24% on £561m of gains.

    The £1,000 step read 23.2% under both 24% and 25%, so no change at all
    for the 1-point rise, and ln(544 / 768) for the rise to 45%.
    """
    changes = {
        f"gov.hmrc.cgt.{rate}": {str(YEAR): reformed_rate}
        for rate in ("higher_rate", "additional_rate")
    }
    sim = simulate(
        [{"employment_income": 200_000, "capital_gains": 561e6}],
        scenario=Scenario(parameter_changes=changes),
    )
    change = sim.calculate("relative_capital_gains_retention_rate_change", YEAR)
    expected = math.log((1 - reformed_rate) / (1 - CGT_MAIN_RATE))
    # Each rate is good to TOLERANCE, so each log retention rate is good to
    # TOLERANCE over the retention rate.
    tolerance = TOLERANCE / (1 - reformed_rate) + TOLERANCE / (1 - CGT_MAIN_RATE)
    assert change[0] == pytest.approx(expected, abs=tolerance)


def test_labour_supply_derivative_at_large_earnings():
    """A marginal pound of earnings above the additional rate threshold keeps
    53p after 45% income tax and 2% NI.

    The £1,000 step read 0.532 at £100m, 0.544 at £561m and 0.576 at £1bn.
    """
    rows = [{"employment_income": e} for e in (100e6, 561e6, 1e9)]
    sim = simulate(rows, simulation_class=Microsimulation)
    derivative = np.asarray(calculate_derivative(sim, year=YEAR))
    assert derivative == pytest.approx([0.53] * 3, abs=TOLERANCE)
