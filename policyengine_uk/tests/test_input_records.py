"""A simulation exports as inputs only the values supplied to it.

policyengine-core records each (variable, branch, period) that ``set_input``
stores, and ``to_input_dict`` exports the recorded values. Rebuilding the
populations keeps the record of inputs the rebuild drops
(policyengine-core#605). ``Simulation.delete_arrays`` forgets such a record,
so a value the engine later carries into that period is not exported as an
input. ``Simulation.build_from_populations`` keeps only the records of values
the new populations hold. It copies populations from another simulation, with
that simulation's records of the inputs they hold, so the two simulations do
not share holders.
"""

import sys
from types import ModuleType

import numpy as np
import pytest
from policyengine_core.experimental.memory_config import MemoryConfig
from policyengine_core.periods import period

from policyengine_uk import Simulation
from policyengine_uk.utils.aggregate_impact.guard import (
    _guard_snapshot,
    _restore,
    _set_guard_value,
    snapshot_inputs,
)
from policyengine_uk.utils import supplied_inputs
from policyengine_uk.utils.household_subset import household_subset
from policyengine_uk.utils.supplied_inputs import (
    CalculatedValue,
    record_model_value,
    same_array,
    set_model_value,
    stored_as_input,
    supplied_input,
)

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


def disk_backed(hours):
    # With no memory to spare, a simulation stores its values on disk.
    sim = Simulation(situation=situation(hours))
    sim.memory_config = MemoryConfig(max_memory_occupation=0)
    sim.build_from_situation(situation(hours))
    return sim


def test_rebuilt_populations_take_inputs_from_a_simulation_storing_on_disk():
    # This simulation has no memory configuration.
    sim = Simulation(situation=situation({2025: 500}))
    sim.build_from_populations(disk_backed({2025: 1_000}).populations)
    sim.set_input("hours_worked", 2026, [700])
    assert sim.calculate("hours_worked", 2026).tolist() == [700]
    assert sim.to_input_dict()["hours_worked"] == {"2025": [1_000], "2026": [700]}


def test_rebuilt_populations_store_values_where_this_simulation_does():
    sim = disk_backed({2025: 500})
    sim.build_from_populations(
        Simulation(situation=situation({2025: 1_000})).populations
    )
    sim.set_input("hours_worked", 2026, [700])
    disk = sim.get_holder("hours_worked")._disk_storage
    assert disk.get(period(2026)).tolist() == [700]


def test_rebuilt_populations_keep_an_input_a_cache_hides():
    # A value cached in memory hides the input stored on disk.
    donor = disk_backed({2025: 1_000})
    donor.memory_config = MemoryConfig(max_memory_occupation=1)
    donor.get_holder("hours_worked").put_in_cache(np.array([999.0]), period(2025))
    sim = Simulation(situation=situation({2025: 500}))
    sim.build_from_populations(donor.populations)
    assert sim.to_input_dict()["hours_worked"] == {"2025": [1_000]}
    assert sim.calculate("hours_worked", 2025).tolist() == [1_000]


def test_rebuilt_populations_keep_a_model_value_a_cache_hides():
    # The model's own value, stored on disk, under a value cached in memory.
    donor = disk_backed({2025: 1_000})
    set_model_value(donor, "adjusted_net_income", period(2026), [50_000])
    donor.memory_config = MemoryConfig(max_memory_occupation=1)
    holder = donor.get_holder("adjusted_net_income")
    holder.put_in_cache(np.array([999.0]), period(2026))
    sim = Simulation(situation=situation({2025: 500}))
    sim.build_from_populations(donor.populations)
    for copy in (sim, sim.clone(), sim.get_branch("copy")):
        assert copy.calculate("adjusted_net_income", 2026).tolist() == [50_000]
        person = copy.populations["person"]
        assert supplied_input(person, "adjusted_net_income", period(2026)) is None


def test_rebuilt_populations_leave_their_simulation_as_it_was():
    donor = Simulation(situation=situation({2025: 520}))
    sim = Simulation(situation=situation({2025: 100}))
    sim.build_from_populations(donor.populations)
    assert donor.calculate("weekly_hours", 2025).tolist() == [10]
    assert sim.calculate("weekly_hours", 2025).tolist() == [10]
    # Each recalculates from its own inputs; neither's changes reach the other.
    donor.set_input("hours_worked", 2025, [1_040])
    assert donor.calculate("weekly_hours", 2025).tolist() == [20]
    assert sim.calculate("weekly_hours", 2025).tolist() == [10]
    sim.set_input("hours_worked", 2025, [260])
    assert sim.calculate("weekly_hours", 2025).tolist() == [5]
    assert donor.calculate("weekly_hours", 2025).tolist() == [20]
    assert donor.to_input_dict()["hours_worked"] == {"2025": [1_040]}
    assert sim.to_input_dict()["hours_worked"] == {"2025": [260]}


def test_rebuilt_populations_forget_the_inputs_they_replace():
    data = situation({2025: 500})
    data["people"]["person"]["adjusted_net_income"] = {2026: 50_000}
    sim = Simulation(situation=data)
    sim.build_from_populations(
        Simulation(situation=situation({2025: 1_000})).populations
    )
    # A value cached in the period is not the input the rebuild replaced.
    holder = sim.get_holder("adjusted_net_income")
    holder.put_in_cache(np.array([123.0]), period(2026))
    person = sim.populations["person"]
    assert supplied_input(person, "adjusted_net_income", period(2026)) is None


TWO_PEOPLE = {
    "people": {
        "first": {"age": {2026: 40}, "employment_income": {2026: 30_000}},
        "second": {"age": {2026: 50}, "employment_income": {2026: 40_000}},
    },
    "benunits": {"b1": {"members": ["first"]}, "b2": {"members": ["second"]}},
    "households": {
        "h1": {"members": ["first"]},
        "h2": {"members": ["second"]},
    },
}
YEAR = period(2026)
INCOME = "adjusted_net_income"


def answers(simulation):
    person = simulation.populations["person"]
    return (
        supplied_input(person, INCOME, YEAR),
        stored_as_input(person, INCOME, YEAR),
    )


def assert_calculated(simulation):
    supplied, stored = answers(simulation)
    assert supplied is None
    assert not stored


def calculated(values):
    # As utils/dependencies.py holds a value the simulation calculated: as an
    # input, so that it stays put, with a model value that stands for a
    # calculation. It writes to the holder directly, so a NaN gets through.
    sim = Simulation(situation=TWO_PEOPLE)
    sim.get_holder(INCOME)._set(YEAR, np.array(values), sim.branch_name, is_input=True)
    record_model_value(sim, INCOME, YEAR, sim.branch_name, calculated=True)
    return sim


def test_a_value_recorded_as_calculated_is_neither_supplied_nor_an_input():
    # utils/dependencies.py stores values the simulation calculated as
    # inputs, so that they stay put, and records them as model values that
    # stand for a calculation.
    name, year = INCOME, YEAR
    sim = Simulation(situation=TWO_PEOPLE)
    sim.set_input(name, year, [1_000.0, 2_000.0])
    record_model_value(sim, name, year, sim.branch_name, calculated=True)

    # A simulation that takes sim's populations takes the record with them
    # (keep_population_records).
    rebuilt = Simulation(situation=TWO_PEOPLE)
    rebuilt.build_from_populations(sim.populations)
    for copy in (sim, sim.clone(), sim.get_branch("copy"), rebuilt):
        assert answers(copy) == (None, False)
    with household_subset(sim, "subset", np.array([False, True])) as subset:
        assert subset.person is not None
        assert subset.simulation.calculate(name, 2026).tolist() == [2_000]
        assert answers(subset.simulation) == (None, False)
    # The model's own value counts as an input, though no one supplied it.
    set_model_value(sim, name, year, [1_000.0, 2_000.0])
    assert answers(sim) == (None, True)
    # A value the scenario sets for the period counts as supplied, even one
    # equal to the model's.
    sim.set_input(name, year, [1_000.0, 2_000.0])
    supplied, stored = answers(sim)
    assert supplied.tolist() == [1_000, 2_000]
    assert stored


def test_a_calculated_nan_is_neither_supplied_nor_an_input():
    sim = calculated([np.nan, 2_000.0])
    key = (INCOME, sim.branch_name, YEAR)
    rebuilt = Simulation(situation=TWO_PEOPLE)
    rebuilt.build_from_populations(sim.populations)

    for copy in (sim, sim.clone(), sim.get_branch("copy"), rebuilt):
        assert_calculated(copy)
        assert type(copy._model_values[key]) is CalculatedValue
        assert f"{INCOME}__{YEAR}" not in copy.to_input_dataframe().columns
    with household_subset(sim, "subset", np.array([True, False])) as subset:
        assert subset.person is not None
        assert_calculated(subset.simulation)


@pytest.mark.parametrize("values", [[1_000.0, 2_000.0], [np.nan, 2_000.0]])
def test_the_aggregate_guard_restores_a_value_recorded_as_calculated(values):
    sim = calculated(values)
    key = (INCOME, sim.branch_name, YEAR)
    snapshot = snapshot_inputs(sim, [INCOME])

    _set_guard_value(sim, INCOME, YEAR, [1_100.0, 2_100.0])
    assert answers(sim)[1]
    sim.calculate("net_income", 2026)
    _restore(sim, INCOME, snapshot)

    assert_calculated(sim)
    assert type(sim._model_values[key]) is CalculatedValue
    stored = sim.get_holder(INCOME).get_array(YEAR, sim.branch_name)
    assert same_array(stored, np.array(values, dtype=stored.dtype))
    # What the simulation calculated from the synthetic value is gone.
    assert sim.get_holder("net_income").get_array(YEAR, sim.branch_name) is None


def test_the_aggregate_guard_runs_against_a_package_without_the_newer_helpers(
    monkeypatch,
):
    # CI runs the pull request head's copy of the tool against the base's
    # package too, so the guard can't assume the base has these names. The
    # package's own functions keep them, as a base's keep what they use.
    older = ModuleType(supplied_inputs.__name__)
    newer = {"CalculatedValue", "record_model_value", "same_array"}
    vars(older).update(
        {
            name: value
            for name, value in vars(supplied_inputs).items()
            if name not in newer
        }
    )
    monkeypatch.setitem(sys.modules, supplied_inputs.__name__, older)
    sim = Simulation(situation=TWO_PEOPLE)
    set_model_value(sim, INCOME, YEAR, [1_000.0, 2_000.0])

    snapshot = snapshot_inputs(sim, [INCOME])
    _set_guard_value(sim, INCOME, YEAR, [1_100.0, 2_100.0])
    _restore(sim, INCOME, snapshot)

    assert sim.get_holder(INCOME).get_array(YEAR, sim.branch_name).tolist() == [
        1_000,
        2_000,
    ]
    assert answers(sim) == (None, True)
    plain = {INCOME: [(YEAR, np.array([1_000.0, 2_000.0], dtype=np.float32))]}
    assert _guard_snapshot(sim, plain, [INCOME]).origins[INCOME]


def test_the_aggregate_guard_matches_a_plain_snapshot_that_holds_a_nan():
    sim = calculated([np.nan, 2_000.0])
    plain = {INCOME: [(YEAR, np.array([np.nan, 2_000.0], dtype=np.float32))]}

    assert _guard_snapshot(sim, plain, [INCOME]).origins[INCOME]
