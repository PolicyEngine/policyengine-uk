"""Only a supplied value that is still stored counts as a supplied input.

``supplied_input`` and ``supplied_input_periods`` tell formulas whether a value
was given to the simulation as an input (``set_input``) rather than filled in
by the engine. policyengine-core keeps its record of an input
(``Simulation._user_input_keys``) after a value is cached over the input, so
the helpers read a supplied value only from a storage tier (memory or disk)
that still holds it (#2307). Before, they counted a value cached over an input
as supplied, and read an input stored on disk from memory when a value was
cached over it there.

Invariants, for every sequence of inputs set, values cached (calculated or
not), arrays deleted and calculations run, on a branch, on the branch it was
made from and on the default branch, in memory or on disk:

1. Survival (model): ``supplied_input`` returns the input on the nearest of
   those branches that still stores one for the period, reading memory before
   disk; otherwise None. An input stays stored until it is deleted, or
   another input or a value is cached over it in the same tier. A value
   cached in memory over an input on disk leaves the input. A value the
   engine calculates never replaces an input.
2. Agreement: ``supplied_input`` returns a value for a period exactly when
   ``supplied_input_periods`` lists the period, and the list is sorted
   earliest first.
3. Differential: for every recorded input, the helpers count it as supplied
   exactly when policyengine-core's ``Holder._stores_user_input`` does. On
   policyengine-core 3.33.1 and later, ``supplied_input`` returns what
   ``Simulation._get_recorded_input_array`` returns, and from 3.33.2
   ``supplied_input_periods`` lists the periods
   ``Simulation._get_set_input_periods`` does.
4. Calculation: calculating, on the default branch and on a branch, leaves
   every supplied value of every variable in ``SUPPLIED_INPUT_VARIABLES``
   supplied and unchanged. No calculation caches a value over a supplied
   input, so in normal use the helpers gave the right answer before the fix
   too.

5. Differential, on a branch and on a branch made from it, after any
   sequence of inputs, caches, model values (``set_model_value``),
   deletions, writes to disk, calculations and branching: for every recorded
   input, ``stored_supplied_value`` finds it exactly when
   ``Holder._stores_user_input`` does; the value it finds on the nearest
   branch is what ``Simulation._get_recorded_input_array`` returns; the
   periods with a surviving input are those
   ``Simulation._get_set_input_periods`` lists; and ``supplied_input`` and
   ``supplied_input_periods`` give the same answers, leaving out the model's
   own values.
6. Engine reads: ``_counted_input``, which ``stored_draws`` reads to name a
   draw's source, counts a recorded input exactly when policyengine-core's
   ``Holder._is_input`` finds it on the branch ``Holder.get_array`` reads,
   unless it is the model's own value; and the value it counts is the value
   ``Holder.get_array`` returns, for a variable that is not neutralised.
7. Inclusion: for a variable that is not neutralised, whenever
   ``_counted_input`` counts an input, ``supplied_input`` returns the same
   value. The engine reads the first value stored on its branches, and an
   input it reads there is that branch's surviving input, so the engine-read
   rule never counts an input the recorded rule misses.

Intended: a neutralised variable whose input is still stored reads as its
default, as it does through the engine. ``_counted_input`` still returns the
stored input, which the engine does not read, so ``stored_draws`` refuses a
neutralised draw before it asks.
"""

from contextlib import contextmanager, nullcontext
from types import SimpleNamespace

import numpy as np
import pytest
from hypothesis import HealthCheck, example, given, settings
from hypothesis import strategies as st
from policyengine_core.data_storage import OnDiskStorage
from policyengine_core.enums import Enum
from policyengine_core.periods import period as period_
from policyengine_core.reforms import Reform

from policyengine_uk import Simulation
from policyengine_uk.utils.supplied_inputs import (
    SUPPLIED_INPUT_VARIABLES,
    _counted_input,
    _is_model_value,
    _visible_branch_names,
    set_model_value,
    stored_supplied_value,
    supplied_input,
    supplied_input_periods,
)

pytestmark = pytest.mark.usefixtures("cloned_uk_tax_benefit_system")


def single_person(person=None):
    return Simulation(
        situation={
            "people": {"person": {"age": {2025: 40}, **(person or {})}},
            "benunits": {"benunit": {"members": ["person"]}},
            "households": {"household": {"members": ["person"]}},
        }
    )


@contextmanager
def under_memory_pressure(holder, folder):
    """Store what ``holder`` stores next on disk, unless it already holds a
    value for that period in memory, as a simulation over its memory limit
    does."""
    if holder._disk_storage is None:
        holder._disk_storage = OnDiskStorage(str(folder), preserve_storage_dir=True)
    holder._on_disk_storable = True
    # A memory limit no simulation can stay under.
    holder.simulation.memory_config = SimpleNamespace(max_memory_occupation_pc=-1)
    try:
        yield
    finally:
        holder._on_disk_storable = False
        holder.simulation.memory_config = None


def read(population, variable, year):
    value = supplied_input(population, variable, period_(year))
    return None if value is None else value.tolist()


def recorded_input_array(simulation, variable, year):
    """policyengine-core's own reading of the supplied value, from 3.33.1."""
    value = simulation._get_recorded_input_array(variable, period_(year))
    return None if value is None else np.asarray(value).tolist()


def stored_period(sim, variable, year):
    """The period a test stores ``variable`` for: ``year``, or its first month
    for a monthly variable."""
    definition = sim.tax_benefit_system.get_variable(variable)
    return period_(f"{year}-01" if definition.definition_period == "month" else year)


def value_of_type(sim, variable, number):
    """A one-person value of ``variable``'s type, built from ``number``: the
    number itself, True for a boolean, or one of an enum's values."""
    definition = sim.tax_benefit_system.get_variable(variable)
    if definition.value_type is Enum:
        names = [item.name for item in definition.possible_values]
        return definition.possible_values.encode(
            np.array([names[int(number) % len(names)]])
        )
    if definition.value_type is bool:
        return np.array([bool(number)])
    return np.array([number], dtype=definition.dtype)


@pytest.mark.parametrize("variable", sorted(SUPPLIED_INPUT_VARIABLES))
def test_a_value_cached_over_an_input_is_not_supplied(variable):
    sim = single_person()
    holder = sim.get_holder(variable)
    population = holder.population
    period = stored_period(sim, variable, 2025)
    supplied = value_of_type(sim, variable, 1)
    cached = value_of_type(sim, variable, 0)
    sim.set_input(variable, period, supplied)
    assert supplied_input(population, variable, period).tolist() == supplied.tolist()

    holder.put_in_cache(cached, period)

    assert holder.get_array(period).tolist() == cached.tolist()
    assert supplied_input(population, variable, period) is None
    assert supplied_input_periods(population, variable) == []
    assert not holder._stores_user_input(period, "default")
    if hasattr(sim, "_get_recorded_input_array"):
        assert sim._get_recorded_input_array(variable, period) is None


def test_other_years_inputs_are_still_supplied():
    sim = single_person({"trading_loss": {2024: 100.0, 2025: 200.0, 2026: 300.0}})
    holder = sim.get_holder("trading_loss")
    holder.put_in_cache(np.array([999.0]), period_(2025))
    population = holder.population
    assert [read(population, "trading_loss", year) for year in (2024, 2025, 2026)] == [
        [100.0],
        None,
        [300.0],
    ]
    assert supplied_input_periods(population, "trading_loss") == [
        period_(2024),
        period_(2026),
    ]


def test_an_input_on_disk_under_a_value_cached_in_memory_is_supplied(tmp_path):
    sim = single_person()
    holder = sim.get_holder("trading_loss")
    with under_memory_pressure(holder, tmp_path):
        sim.set_input("trading_loss", 2025, [100.0])
    assert holder._disk_storage.has(period_(2025), "default")
    assert not holder._memory_storage.has(period_(2025), "default")

    holder.put_in_cache(np.array([999.0]), period_(2025))

    # The engine reads the cached value, but the input is still stored.
    assert holder.get_array(period_(2025)).tolist() == [999.0]
    population = holder.population
    assert read(population, "trading_loss", 2025) == [100.0]
    assert supplied_input_periods(population, "trading_loss") == [period_(2025)]
    assert holder._stores_user_input(period_(2025), "default")
    if hasattr(sim, "_get_recorded_input_array"):
        assert recorded_input_array(sim, "trading_loss", 2025) == [100.0]


def test_a_value_cached_over_an_input_on_disk_is_not_supplied(tmp_path):
    sim = single_person()
    holder = sim.get_holder("trading_loss")
    with under_memory_pressure(holder, tmp_path):
        sim.set_input("trading_loss", 2025, [100.0])
        holder.put_in_cache(np.array([999.0]), period_(2025))
    assert holder._disk_storage.get(period_(2025)).tolist() == [999.0]
    assert not holder._memory_storage.has(period_(2025), "default")

    population = holder.population
    assert read(population, "trading_loss", 2025) is None
    assert supplied_input_periods(population, "trading_loss") == []
    assert not holder._stores_user_input(period_(2025), "default")


def test_a_calculated_value_is_never_stored_over_an_input(tmp_path):
    """policyengine-core stores a calculated (derived) value over nothing the
    engine reads as an input, in memory or on disk."""
    sim = single_person()
    holder = sim.get_holder("trading_loss")
    sim.set_input("trading_loss", 2025, [100.0])
    with under_memory_pressure(holder, tmp_path):
        sim.set_input("trading_loss", 2026, [200.0])
        holder.put_in_cache(np.array([999.0]), period_(2026), derived=True)
    holder.put_in_cache(np.array([999.0]), period_(2025), derived=True)
    holder.put_in_cache(np.array([999.0]), period_(2026), derived=True)
    assert holder.get_array(period_(2025)).tolist() == [100.0]
    assert holder.get_array(period_(2026)).tolist() == [200.0]
    population = holder.population
    assert read(population, "trading_loss", 2025) == [100.0]
    assert read(population, "trading_loss", 2026) == [200.0]


def test_the_nearest_branch_still_storing_an_input_is_read():
    sim = single_person({"trading_loss": {2025: 100.0}})
    branch = sim.get_branch("reform")
    population = branch.get_variable_population("trading_loss")
    # The branch reads the input of the simulation it was made from.
    assert read(population, "trading_loss", 2025) == [100.0]

    branch.set_input("trading_loss", 2025, [200.0])
    assert read(population, "trading_loss", 2025) == [200.0]
    # The simulation the branch was made from does not see the branch's input.
    assert read(sim.get_variable_population("trading_loss"), "trading_loss", 2025) == [
        100.0
    ]

    holder = branch.get_holder("trading_loss")
    holder.put_in_cache(np.array([999.0]), period_(2025), "reform")
    # The branch's input is gone, so the input it was made from is read, as
    # policyengine-core reads it.
    assert read(population, "trading_loss", 2025) == [100.0]
    assert supplied_input_periods(population, "trading_loss") == [period_(2025)]
    if hasattr(branch, "_get_recorded_input_array"):
        assert recorded_input_array(branch, "trading_loss", 2025) == [100.0]

    holder.put_in_cache(np.array([998.0]), period_(2025), "default")
    assert read(population, "trading_loss", 2025) is None
    assert supplied_input_periods(population, "trading_loss") == []


class neutralize_trading_loss(Reform):
    def apply(self):
        self.neutralize_variable("trading_loss")


def test_a_neutralised_input_reads_as_its_default_only_while_it_is_stored():
    sim = single_person({"trading_loss": {2025: 100.0, 2026: 200.0}})
    sim.apply_reform(neutralize_trading_loss)
    holder = sim.get_holder("trading_loss")
    holder.put_in_cache(np.array([999.0]), period_(2026))
    population = holder.population
    assert read(population, "trading_loss", 2025) == [0.0]
    assert read(population, "trading_loss", 2026) is None
    assert supplied_input_periods(population, "trading_loss") == [period_(2025)]


CALCULATED = [
    "household_net_income",
    "income_tax",
    "ni_class_4",
    "ni_class_4_losses_carried_forward",
    "ni_class_4_trading_loss",
    "ni_class_4_losses_brought_forward",
    "trading_loss",
    "person_bus_fare_spending",
    "bus_fare_spending",
    "local_bus_trips",
]


def assert_supplied(sim, expected):
    for variable in SUPPLIED_INPUT_VARIABLES:
        population = sim.get_variable_population(variable)
        stored = sorted(
            (period for name, period in expected if name == variable),
            key=lambda period: period.start,
        )
        assert supplied_input_periods(population, variable) == stored, variable
        for period in stored:
            assert (
                supplied_input(population, variable, period).tolist()
                == expected[variable, period]
            ), (variable, period)
    for variable, branch_name, period in sim._user_input_keys:
        assert sim.get_holder(variable)._stores_user_input(period, branch_name)


def test_calculating_leaves_every_supplied_value_supplied():
    situation = {
        "self_employment_income": {year: 30_000 for year in range(2024, 2028)},
        "employment_income": {year: 10_000 for year in range(2024, 2028)},
    }
    sim = single_person(situation)
    # The situation's registered inputs, then a value of every other
    # registered variable for 2025 and 2026.
    expected = {
        (variable, period_(year)): [float(value)]
        for variable, values in situation.items()
        if variable in SUPPLIED_INPUT_VARIABLES
        for year, value in values.items()
    }
    for year in (2025, 2026):
        for number, variable in enumerate(sorted(SUPPLIED_INPUT_VARIABLES), 1):
            if variable in situation:
                continue
            period = stored_period(sim, variable, year)
            value = value_of_type(sim, variable, number + year)
            sim.set_input(variable, period, value)
            expected[variable, period] = value.tolist()
    branch = sim.get_branch("reform")
    branch.set_input("trading_loss", 2027, [123.0])
    branch_expected = {**expected, ("trading_loss", period_(2027)): [123.0]}

    for simulation in (sim, branch):
        for year in (2024, 2025, 2026, 2027, 2028):
            for variable in CALCULATED:
                simulation.calculate(variable, year)

    assert_supplied(sim, expected)
    assert_supplied(branch, branch_expected)


BRANCHES = ("child", "parent", "default")  # nearest first
YEARS = (2024, 2025, 2026)
step = st.one_of(
    # Set an input, on disk if under memory pressure.
    st.tuples(
        st.just("set"), st.sampled_from(BRANCHES), st.sampled_from(YEARS), st.booleans()
    ),
    # Cache a value, calculated (derived) or not, on disk if under pressure.
    st.tuples(
        st.just("cache"),
        st.sampled_from(BRANCHES),
        st.sampled_from(YEARS),
        st.booleans(),
        st.booleans(),
    ),
    st.tuples(st.just("delete"), st.sampled_from(BRANCHES), st.sampled_from(YEARS)),
    st.tuples(
        st.just("calculate"),
        st.sampled_from(["trading_loss", "ni_class_4_losses_brought_forward"]),
        st.sampled_from(YEARS + (2027,)),
    ),
)

_templates = []


def branch_chain():
    """A branch ("child") of a branch ("parent") of a simulation."""
    if not _templates:
        _templates.append(single_person())
    root = _templates[0].clone(clone_tax_benefit_system=False)
    return root.get_branch("parent").get_branch("child")


def tier_holding(holder, period, branch_name, value):
    """The tier that holds ``value`` for ``period`` on ``branch_name``."""
    for tier, storage in (
        ("memory", holder._memory_storage),
        ("disk", holder._disk_storage),
    ):
        if (
            storage is not None
            and storage.has(period, branch_name)
            and storage.get(period, branch_name).tolist() == [value]
        ):
            return tier
    return None


def expected_supplied(stored, year):
    """Invariant 1: the input on the nearest branch, memory before disk."""
    for branch_name in BRANCHES:
        for tier in ("memory", "disk"):
            if (branch_name, year, tier) in stored:
                return [stored[branch_name, year, tier]]
    return None


@settings(
    max_examples=100,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow],
)
@given(steps=st.lists(step, max_size=10))
# A value cached over the input in the same tier (#2307).
@example(steps=[("set", "child", 2025, False), ("cache", "child", 2025, False, False)])
# An input on disk under a value cached in memory.
@example(steps=[("set", "child", 2025, True), ("cache", "child", 2025, False, False)])
# A value cached over the child's input leaves the parent's.
@example(
    steps=[
        ("set", "parent", 2025, False),
        ("set", "child", 2025, True),
        ("cache", "child", 2025, False, True),
    ]
)
# An input in memory over an earlier input on disk is read, as the engine
# reads it.
@example(steps=[("set", "child", 2025, True), ("set", "child", 2025, False)])
# From policyengine-core 3.33, the first input drops the cached value, so it
# and the second input go to disk (found by Hypothesis).
@example(
    steps=[
        ("cache", "child", 2024, False, False),
        ("set", "child", 2024, True),
        ("set", "child", 2024, True),
    ]
)
def test_only_inputs_still_stored_are_supplied(tmp_path_factory, steps):
    child = branch_chain()
    holder = child.get_holder("trading_loss")
    population = holder.population
    folder = tmp_path_factory.mktemp("disk")
    # The surviving inputs, by (branch, year, tier).
    stored = {}
    for index, (kind, *args) in enumerate(steps):
        if kind in ("set", "cache"):
            branch_name, year, *flags = args
            pressure = flags[-1]
            period = period_(year)
            # Every value written is new, so the tier holding it shows where
            # core stored it. (Under pressure, core stores on disk unless
            # memory holds a value for the period; from 3.33, setting an input
            # first drops cached values that may depend on it.)
            value = (1.0 if kind == "set" else 10_000.0) + index
            with under_memory_pressure(holder, folder) if pressure else nullcontext():
                if kind == "set":
                    holder.set_input(period, np.array([value]), branch_name)
                else:
                    derived = flags[0]
                    holder.put_in_cache(np.array([value]), period, branch_name, derived)
            tier = tier_holding(holder, period, branch_name, value)
            if kind == "set":
                assert tier is not None
                stored[branch_name, year, tier] = value
            elif tier is not None:
                # A calculated value never replaces an input.
                assert not (derived and (branch_name, year, tier) in stored)
                stored.pop((branch_name, year, tier), None)
        elif kind == "delete":
            branch_name, year = args
            holder.delete_arrays(period_(year), branch_name)
            for tier in ("memory", "disk"):
                stored.pop((branch_name, year, tier), None)
        else:
            variable, year = args
            child.calculate(variable, year)

        supplied_years = []
        for year in YEARS:
            expected = expected_supplied(stored, year)
            assert read(population, "trading_loss", year) == expected, (year, stored)
            if expected is not None:
                supplied_years.append(year)
            if hasattr(child, "_get_recorded_input_array"):
                assert recorded_input_array(child, "trading_loss", year) == expected
        # Invariant 2.
        periods = supplied_input_periods(population, "trading_loss")
        assert periods == [period_(year) for year in supplied_years]
        if hasattr(child, "_get_set_input_periods"):
            assert set(child._get_set_input_periods("trading_loss")) == set(periods)
        # Invariant 3, for every recorded input of the variable.
        for variable, branch_name, period in child._user_input_keys:
            if variable == "trading_loss":
                ours = stored_supplied_value(holder, period, branch_name)
                assert (ours is not None) == holder._stores_user_input(
                    period, branch_name
                ), (branch_name, period)


# Invariants 5 to 7, on a branch ("parent") and a branch made from it
# ("child"), which a step makes at any point.
VARIABLE = "trading_loss"
TARGETS = ("parent", "child")
engine_step = st.one_of(
    # Set an input through the simulation, on disk if under memory pressure.
    st.tuples(
        st.just("set"), st.sampled_from(TARGETS), st.sampled_from(YEARS), st.booleans()
    ),
    # Cache a value, calculated (derived) or not, on disk if under pressure.
    st.tuples(
        st.just("cache"),
        st.sampled_from(TARGETS),
        st.sampled_from(YEARS),
        st.booleans(),
        st.booleans(),
    ),
    # Store the model's own value (set_model_value), on disk if under pressure.
    st.tuples(
        st.just("model"),
        st.sampled_from(TARGETS),
        st.sampled_from(YEARS),
        st.booleans(),
    ),
    # Delete through the simulation (every visible branch) or on the target's
    # own branch only.
    st.tuples(
        st.just("delete"),
        st.sampled_from(TARGETS),
        st.sampled_from(YEARS),
        st.booleans(),
    ),
    st.tuples(st.just("branch")),
    st.tuples(
        st.just("calculate"),
        st.sampled_from(TARGETS),
        st.sampled_from(["trading_loss", "ni_class_4_losses_brought_forward"]),
        st.sampled_from(YEARS + (2027,)),
    ),
)


def as_list(value):
    return None if value is None else np.asarray(value).tolist()


def check_both_rules(sim):
    """Invariants 5 to 7 for ``VARIABLE`` in ``sim``."""
    holder = sim.get_holder(VARIABLE)
    population = holder.population
    visible = _visible_branch_names(sim)
    keys = [
        key for key in sim._user_input_keys if key[0] == VARIABLE and key[1] in visible
    ]
    # Invariant 5: the general helpers against core.
    surviving = {}
    for key in keys:
        _, branch_name, period = key
        value = stored_supplied_value(holder, period, branch_name)
        assert (value is not None) == holder._stores_user_input(period, branch_name), (
            key
        )
        if value is not None:
            surviving[key] = value
    assert {key[2] for key in surviving} == set(sim._get_set_input_periods(VARIABLE))
    supplied_periods = {
        key[2]
        for key, value in surviving.items()
        if not _is_model_value(sim, key, value)
    }
    assert supplied_input_periods(population, VARIABLE) == sorted(
        supplied_periods, key=lambda period: period.start
    )
    for year in YEARS:
        period = period_(year)
        nearest = next(
            (
                (VARIABLE, branch_name, period)
                for branch_name in visible
                if (VARIABLE, branch_name, period) in surviving
            ),
            None,
        )
        recorded = None if nearest is None else surviving[nearest]
        assert as_list(recorded) == as_list(
            sim._get_recorded_input_array(VARIABLE, period)
        ), (sim.branch_name, period)
        expected = (
            None
            if recorded is None or _is_model_value(sim, nearest, recorded)
            else recorded
        )
        assert as_list(supplied_input(population, VARIABLE, period)) == as_list(
            expected
        ), (sim.branch_name, period)
        # Invariant 6: the engine-read rule against the engine.
        storing = holder._branch_storing(period, sim.branch_name)
        if storing is None:
            continue
        read = holder.get_array(period, sim.branch_name)
        key = (VARIABLE, storing, period)
        engine_reads_input = (
            key in sim._user_input_keys
            and holder._is_input(period, storing)
            and not _is_model_value(sim, key, read)
        )
        assert (_counted_input(sim, holder, key) is not None) == engine_reads_input
    for key in keys:
        counted = _counted_input(sim, holder, key)
        if counted is None:
            continue
        _, branch_name, period = key
        assert branch_name == holder._branch_storing(period, sim.branch_name)
        assert as_list(counted) == as_list(holder.get_array(period, sim.branch_name))
        # Invariant 7.
        assert as_list(counted) == as_list(supplied_input(population, VARIABLE, period))


@settings(
    max_examples=100,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow],
)
@given(steps=st.lists(engine_step, max_size=12))
# A child branch's value over the parent's input: supplied, not counted.
@example(
    steps=[
        ("set", "parent", 2025, False),
        ("branch",),
        ("cache", "child", 2025, False, False),
    ]
)
# An input on disk under a value cached in memory: supplied, not counted.
@example(steps=[("set", "parent", 2025, True), ("cache", "parent", 2025, True, False)])
# The model's own value on the parent, then an input on the child.
@example(
    steps=[
        ("model", "parent", 2025, False),
        ("branch",),
        ("set", "child", 2025, True),
        ("delete", "child", 2025, False),
    ]
)
def test_the_two_rules_agree_with_core_on_a_branch_and_its_child(
    tmp_path_factory, steps
):
    if not _templates:
        _templates.append(single_person())
    root = _templates[0].clone(clone_tax_benefit_system=False)
    simulations = {"parent": root.get_branch("parent")}
    folder = tmp_path_factory.mktemp("disk")
    for index, (kind, *args) in enumerate(steps):
        if kind == "branch":
            simulations["child"] = simulations["parent"].get_branch("child")
            continue
        target, *args = args
        sim = simulations.get(target)
        if sim is None:
            continue
        holder = sim.get_holder(VARIABLE)
        # Every value written is new.
        value = np.array([1.0 + index + (100.0 if kind == "model" else 0.0)])
        if kind in ("set", "cache", "model"):
            year, *flags = args
            pressure = flags[-1]
            with under_memory_pressure(holder, folder) if pressure else nullcontext():
                if kind == "set":
                    sim.set_input(VARIABLE, year, value)
                elif kind == "model":
                    set_model_value(sim, VARIABLE, year, value)
                else:
                    holder.put_in_cache(
                        value + 10_000, period_(year), sim.branch_name, flags[0]
                    )
        elif kind == "delete":
            year, whole = args
            if whole:
                sim.delete_arrays(VARIABLE, year)
            else:
                holder.delete_arrays(period_(year), sim.branch_name)
        else:
            variable, year = args
            sim.calculate(variable, year)
        for simulation in simulations.values():
            check_both_rules(simulation)


def test_a_neutralised_input_is_counted_but_reads_as_its_default():
    """``_counted_input`` reads storage, so for a neutralised variable it
    returns the stored input while the engine and ``supplied_input`` return
    the default. ``stored_draws`` refuses a neutralised draw before it asks
    (``test_stored_draw_input_source.py::test_a_neutralised_draw_raises``)."""
    sim = single_person({"trading_loss": {2025: 100.0}})
    sim.apply_reform(neutralize_trading_loss)
    # A branch made after the reform reads the input of the simulation it was
    # made from.
    branch = sim.get_branch("reform")
    key = ("trading_loss", "default", period_(2025))
    for simulation in (sim, branch):
        holder = simulation.get_holder("trading_loss")
        assert holder.variable.is_neutralized
        assert as_list(_counted_input(simulation, holder, key)) == [100.0]
        assert holder.get_array(period_(2025), simulation.branch_name).tolist() == [0.0]
        assert read(holder.population, "trading_loss", 2025) == [0.0]
