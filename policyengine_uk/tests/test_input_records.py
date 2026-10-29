"""A simulation exports as inputs only the values supplied to it.

policyengine-core records each (variable, branch, period) that ``set_input``
stores, and ``to_input_dict`` exports the recorded values. Rebuilding the
populations keeps the record of inputs the rebuild drops
(policyengine-core#605). ``Simulation.delete_arrays`` forgets such a record,
so a value the engine later carries into that period is not exported as an
input. ``Simulation.build_from_populations`` keeps only the records of values
the new populations hold, and takes the records of populations from another
simulation along with them.
"""

import pytest
from policyengine_core.periods import period

from policyengine_uk import Simulation
from policyengine_uk.utils.supplied_inputs import supplied_input

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


def test_rebuilt_populations_export_their_own_inputs():
    sim = Simulation(situation=situation({2025: 500}))
    sim.build_from_populations(
        Simulation(situation=situation({2026: 1_000})).populations
    )
    assert sim.to_input_dict()["hours_worked"] == {"2026": [1_000]}


def test_rebuilt_populations_record_an_input_set_later():
    # The holder comes from another simulation; the input is set here.
    sim = Simulation(situation=situation({2025: 500}))
    sim.build_from_populations(
        Simulation(situation=situation({2025: 1_000})).populations
    )
    sim.set_input("hours_worked", 2026, [700])
    assert sim.to_input_dict()["hours_worked"] == {"2025": [1_000], "2026": [700]}
    assert sim.clone().to_input_dict()["hours_worked"] == {
        "2025": [1_000],
        "2026": [700],
    }


def income_situation(adjusted_net_income=None):
    person = {"age": {2026: 40}, "employment_income": {2026: 30_000}}
    if adjusted_net_income is not None:
        person["adjusted_net_income"] = {2026: adjusted_net_income}
    return {
        "people": {"person": person},
        "benunits": {"benunit": {"members": ["person"]}},
        "households": {"household": {"members": ["person"]}},
    }


def test_rebuilt_populations_keep_an_input_supplied_to_their_simulation():
    sim = Simulation(situation=income_situation())
    donor = Simulation(situation=income_situation(50_000))
    sim.build_from_populations(donor.populations)
    person = sim.populations["person"]
    assert supplied_input(person, "adjusted_net_income", period(2026)).tolist() == [
        50_000
    ]
    # Net income reads the supplied adjusted net income, as the variable does.
    assert sim.calculate("net_income", 2026).tolist() == [50_000]


def test_rebuilt_populations_keep_a_value_their_simulation_calculated():
    sim = Simulation(situation=income_situation(50_000))
    donor = Simulation(situation=income_situation())
    donor.calculate("adjusted_net_income", 2026)
    sim.build_from_populations(donor.populations)
    person = sim.populations["person"]
    assert supplied_input(person, "adjusted_net_income", period(2026)) is None
    assert sim.calculate("net_income", 2026).tolist() == [30_000]
