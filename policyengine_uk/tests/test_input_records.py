"""A simulation exports as inputs only the values supplied to it.

policyengine-core records each (variable, branch, period) that ``set_input``
stores, and ``to_input_dict`` exports the recorded values. Rebuilding the
populations keeps the record of inputs the rebuild drops
(policyengine-core#605). ``Simulation.delete_arrays`` forgets such a record,
so a value the engine later carries into that period is not exported as an
input.
"""

import pytest

from policyengine_uk import Simulation

pytestmark = pytest.mark.usefixtures("cloned_uk_tax_benefit_system")


def situation(hours):
    return {
        "people": {"person": {"age": {2025: 40}, "hours_worked": hours}},
        "benunits": {"benunit": {"members": ["person"]}},
        "households": {"household": {"members": ["person"]}},
    }


def test_deleting_after_a_rebuild_does_not_export_a_carried_over_input():
    sim = Simulation(situation=situation({2025: 1_000, 2026: 500}))
    sim.build_from_situation(situation({2025: 1_000}))
    sim.delete_arrays("hours_worked", 2026)
    # The engine carries 2025's hours into 2026; they are not an input.
    assert sim.calculate("hours_worked", 2026).tolist() == [1_000]
    assert sim.to_input_dict()["hours_worked"] == {"2025": [1_000]}
