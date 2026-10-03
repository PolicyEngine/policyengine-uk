"""The labour supply dynamics split benefit units at age 18 explicitly.

The OBR elasticity groups do not define a child, so the dynamics modules keep
an explicit age band instead of reading the deprecated generic child and adult
variables. This checks the helper reproduces those variables exactly.
"""

import numpy as np

from policyengine_uk import Simulation
from policyengine_uk.dynamics.demographics import benunit_age_18_composition

SITUATION = {
    "people": {
        "parent": {"age": {"2025": 40}},
        "student": {"age": {"2025": 18}},
        "child_1": {"age": {"2025": 10}},
        "child_2": {"age": {"2025": 3}},
        "lodger": {"age": {"2025": 30}},
        "teen_head": {"age": {"2025": 17}},
    },
    "benunits": {
        "family": {"members": ["parent", "student", "child_1", "child_2"]},
        "lodger": {"members": ["lodger"]},
        "teen": {"members": ["teen_head"]},
    },
    "households": {
        "household": {
            "members": [
                "parent",
                "student",
                "child_1",
                "child_2",
                "lodger",
                "teen_head",
            ]
        }
    },
}


class _DefaultPeriod:
    """Simulation.calculate with a default period, as the dynamics call it."""

    def __init__(self, sim, period):
        self.sim, self.period = sim, period
        self.populations = sim.populations

    def calculate(self, variable, period=None, **kwargs):
        return self.sim.calculate(variable, period or self.period, **kwargs)


def test_composition_matches_the_deprecated_age_18_variables():
    sim = Simulation(situation=SITUATION)
    composition = benunit_age_18_composition(_DefaultPeriod(sim, 2025))
    np.testing.assert_array_equal(
        composition["count_under_18"].values,
        sim.calculate("benunit_count_children", 2025, map_to="person"),
    )
    np.testing.assert_array_equal(
        composition["youngest_under_18_age"].values,
        sim.calculate("youngest_child_age", 2025, map_to="person"),
    )
    np.testing.assert_array_equal(
        composition["count_aged_18_or_over"].values,
        sim.calculate("benunit_count_adults", 2025, map_to="person"),
    )


def test_composition_values():
    sim = Simulation(situation=SITUATION)
    composition = benunit_age_18_composition(_DefaultPeriod(sim, 2025))
    assert composition["count_under_18"].tolist() == [2, 2, 2, 2, 0, 1]
    assert composition["youngest_under_18_age"].tolist() == [
        3,
        3,
        3,
        3,
        np.inf,
        17,
    ]
    assert composition["count_aged_18_or_over"].tolist() == [2, 2, 2, 2, 1, 0]
