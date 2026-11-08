"""Data attachments retain immutable draw storage and verify every visible input."""

import copy

import numpy as np
import pytest
from policyengine_core.data_storage import InMemoryStorage, OnDiskStorage
from policyengine_core.holders import Holder
from policyengine_core.periods import period

from policyengine_uk import Simulation
from policyengine_uk.model_api import Person, Variable, YEAR
from policyengine_uk.tests.stored_draw_fixtures import one_person_units_frame
from policyengine_uk.tests.test_stored_draw_core_route import core_file
from policyengine_uk.utils.protected_inputs import install_draw_storage, protects_draws
from policyengine_uk.utils.protected_storage import ProtectedMemoryStorage
from policyengine_uk.utils.stored_draws import (
    REGISTERED_DRAW_NAMES,
    StoredDrawError,
    calculation,
    input_source,
)


pytestmark = pytest.mark.usefixtures("cloned_uk_tax_benefit_system")

DRAW = "pip_phase_in_draw"
GROUP_DRAW = "uc_new_claimant_health_element_draw"
VALUES = np.array([0.25, 0.5, 0.75], dtype=np.float32)
OTHER = np.array([0.125, 0.375, 0.625], dtype=np.float32)


def built(columns=None):
    if columns is None:
        columns = {DRAW: VALUES, GROUP_DRAW: OTHER}
    return Simulation(dataset=one_person_units_frame(columns=columns))


def situation():
    names = [f"person_{index}" for index in range(len(VALUES))]
    return {
        "people": {
            name: {"age": 30, DRAW: float(values)}
            for name, values in zip(names, VALUES)
        },
        "benunits": {
            name: {"members": [name], GROUP_DRAW: float(values)}
            for name, values in zip(names, OTHER)
        },
        "households": {name: {"members": [name]} for name in names},
    }


def source_of(simulation, requested=2026, name=DRAW):
    return input_source(simulation.get_variable_population(name), name, requested)


def snapshot(simulation, name=DRAW):
    holder = simulation.get_holder(name)
    storage = holder._memory_storage
    return (
        {
            key: (values.dtype, values.shape, values.tobytes())
            for key, values in storage._arrays.items()
        },
        frozenset(storage._inputs),
        storage._sequence_numbers.copy(),
        set(simulation._user_input_keys),
        copy.deepcopy(getattr(holder, "_user_input_storage", {})),
    )


def assert_immutable(actual, expected):
    assert type(actual) is np.ndarray
    assert isinstance(actual.base, bytes)
    assert not actual.flags.writeable
    np.testing.assert_array_equal(actual, expected)
    with pytest.raises(ValueError):
        actual.flags.writeable = True
    with pytest.raises(ValueError):
        actual[0] = 0


@pytest.mark.parametrize("route", ["frame", "core"])
def test_each_loader_installs_both_draw_storages_before_its_first_store(
    route, monkeypatch, tmp_path
):
    seen = []
    original = Holder._set

    def checked_store(holder, *args, **kwargs):
        if holder.variable.name in REGISTERED_DRAW_NAMES:
            seen.append(holder.variable.name)
            assert isinstance(holder._memory_storage, ProtectedMemoryStorage)
        return original(holder, *args, **kwargs)

    monkeypatch.setattr(Holder, "_set", checked_store)
    if route == "frame":
        simulation = built()
    else:
        path = core_file(
            tmp_path / "draws.h5",
            columns={DRAW: {2025: VALUES}, GROUP_DRAW: {2025: OTHER}},
        )
        simulation = Simulation(dataset=path)

    assert set(seen) == REGISTERED_DRAW_NAMES
    assert protects_draws(simulation)
    for name, expected in ((DRAW, VALUES), (GROUP_DRAW, OTHER)):
        assert_immutable(simulation.calculate(name, 2025), expected)


def test_data_attachment_installs_empty_registered_holders():
    simulation = built({})
    for name in REGISTERED_DRAW_NAMES:
        assert isinstance(
            simulation.get_holder(name)._memory_storage, ProtectedMemoryStorage
        )


def test_the_installer_does_not_create_holders_on_a_situation():
    from policyengine_uk.system import system

    simulation = Simulation.__new__(Simulation)
    simulation.tax_benefit_system = system
    simulation.populations = system.instantiate_entities()
    simulation.built_from_dataset = False
    install_draw_storage(simulation)
    assert not any(
        name in population._holders
        for population in simulation.populations.values()
        for name in REGISTERED_DRAW_NAMES
    )


def test_root_clone_and_branch_keep_input_marks_values_and_sequence_numbers():
    simulation = built()
    assert_immutable(simulation.calculate(DRAW, 2026), VALUES)
    before = snapshot(simulation)
    source = source_of(simulation)

    clone = simulation.clone()
    branch = simulation.get_branch("draw_child")
    for target in (simulation, clone, branch):
        assert protects_draws(target)
        assert snapshot(target) == before
        assert source_of(target) == source
        assert_immutable(target.calculate(DRAW, 2025), VALUES)
        first = target.calculate(DRAW, 2026)
        second = target.calculate(DRAW, 2026)
        assert first is not second
        assert_immutable(first, VALUES)
        first.shape = (1, 3)
        first.dtype = np.uint8
        assert_immutable(target.calculate(DRAW, 2026), VALUES)

    assert clone._user_input_keys is not simulation._user_input_keys
    assert branch._user_input_keys is not simulation._user_input_keys
    root_storage = simulation.get_holder(DRAW)._memory_storage
    for target in (clone, branch):
        storage = target.get_holder(DRAW)._memory_storage
        assert storage is not root_storage
        assert storage._arrays is not root_storage._arrays
        assert storage._sequence_numbers is not root_storage._sequence_numbers


def test_a_data_rebuild_adopts_plain_inputs_without_changing_their_provenance():
    source = Simulation(situation=situation())
    source_holder = source.get_holder(DRAW)
    before = snapshot(source)
    simulation = built()
    simulation.build_from_populations(source.populations)

    assert snapshot(simulation) == before
    assert source_of(simulation, 2025).sequence_number == before[2]["default:2025"]
    assert_immutable(simulation.calculate(DRAW, 2025), VALUES)
    source_holder.get_array(period(2025))[0] = 0
    assert_immutable(simulation.calculate(DRAW, 2025), VALUES)
    assert simulation.populations["person"] is not source.populations["person"]
    assert simulation.get_holder(DRAW) is not source_holder


def test_a_same_population_rebuild_keeps_its_existing_draw_record():
    simulation = built()
    before = snapshot(simulation)
    simulation.build_from_populations(simulation.populations)
    assert snapshot(simulation) == before
    assert_immutable(simulation.calculate(DRAW, 2026), VALUES)


def test_a_rebuild_with_fresh_populations_installs_before_new_inputs():
    simulation = built()
    populations = simulation.tax_benefit_system.instantiate_entities()
    for population in populations.values():
        population.count = 3
        population.ids = np.arange(3)
        if not population.entity.is_person:
            population.members_entity_id = np.arange(3)
            population.members_role = np.full(3, population.entity.flattened_roles[0])
    simulation.build_from_populations(populations)

    for name in REGISTERED_DRAW_NAMES:
        holder = simulation.get_holder(name)
        assert isinstance(holder._memory_storage, ProtectedMemoryStorage)
        assert holder.get_known_periods() == []
        assert not any(key[0] == name for key in simulation._user_input_keys)
    simulation.set_input(DRAW, 2025, VALUES)
    assert_immutable(simulation.calculate(DRAW, 2026), VALUES)


@pytest.mark.parametrize("replacement", ["holder", "storage"])
def test_plain_replacements_fail_every_read_and_a_clone_cannot_trust_them(replacement):
    simulation = built()
    population = simulation.get_variable_population(DRAW)
    holder = population.get_holder(DRAW)
    if replacement == "holder":
        holder = Holder(holder.variable, population)
        population._holders[DRAW] = holder
    else:
        holder._memory_storage = InMemoryStorage(False)
    holder._memory_storage.put(VALUES.copy(), period(2025))

    for _ in range(2):
        with pytest.raises(StoredDrawError, match=f"{DRAW}.*protected memory"):
            simulation.calculate(DRAW, 2025)
    try:
        clone = simulation.clone()
    except StoredDrawError:
        return
    for _ in range(2):
        with pytest.raises(StoredDrawError, match=f"{DRAW}.*protected memory"):
            clone.calculate(DRAW, 2025)


@pytest.mark.parametrize("record", ["missing_key", "none"])
def test_a_visible_mark_requires_the_reading_simulations_record(record):
    simulation = built()
    if record == "missing_key":
        simulation._user_input_keys.discard((DRAW, "default", period(2025)))
    else:
        simulation._user_input_keys = None
    with pytest.raises(StoredDrawError, match="simulation's input record"):
        source_of(simulation, 2025)


@pytest.mark.parametrize("requested", [2024, 2027])
def test_a_later_visible_mark_cannot_disappear_from_the_record(requested):
    simulation = built()
    simulation.get_holder(DRAW).set_input(period(2024), OTHER)
    simulation._user_input_keys.remove((DRAW, "default", period(2025)))
    with pytest.raises(StoredDrawError, match=f"{DRAW} for 2025.*input record"):
        source_of(simulation, requested)


def test_a_shadowed_visible_parent_mark_still_requires_a_record():
    simulation = built()
    branch = simulation.get_branch("record_child")
    branch.get_holder(DRAW).set_input(period(2025), OTHER, branch.branch_name)
    branch._user_input_keys.remove((DRAW, "default", period(2025)))
    with pytest.raises(
        StoredDrawError, match=f"{DRAW} for 2025.*default.*input record"
    ):
        source_of(branch, 2025)
    assert_immutable(simulation.calculate(DRAW, 2025), VALUES)


def test_a_mark_outside_the_readable_branches_does_not_block_a_read():
    simulation = built()
    simulation.get_holder(DRAW)._memory_storage.put(
        OTHER.copy(), period(2024), "unread_branch"
    )
    assert source_of(simulation, 2025).period == period(2025)
    assert_immutable(simulation.calculate(DRAW, 2025), VALUES)


@pytest.mark.parametrize(
    "location",
    [
        None,
        (period(2024), frozenset({"memory"})),
        (period(2025), frozenset()),
        (period(2025), frozenset({"disk"})),
    ],
    ids=["none", "wrong_period", "empty", "wrong_tier"],
)
def test_a_visible_mark_requires_the_holders_matching_location_record(location):
    simulation = built()
    holder = simulation.get_holder(DRAW)
    holder._user_input_storage[("default", "2025")] = location
    with pytest.raises(StoredDrawError, match="holder's location record"):
        source_of(simulation, 2025)


def test_a_register_only_input_seeds_its_location_without_changing_storage():
    simulation = built()
    holder = simulation.get_holder(DRAW)
    del holder._user_input_storage[("default", "2025")]
    before = snapshot(simulation)

    source = source_of(simulation, 2025)

    assert source.period == period(2025)
    assert snapshot(simulation)[:4] == before[:4]
    assert holder._user_input_storage[("default", "2025")] == (
        period(2025),
        frozenset({"memory"}),
    )


def test_an_early_year_mark_keeps_its_period_when_the_storage_key_omits_zeroes():
    simulation = built()
    early = period("0001")
    holder = simulation.get_holder(DRAW)
    holder.set_input(early, OTHER)
    source = source_of(simulation, early)
    assert source.period == early
    assert (
        source.sequence_number == holder._memory_storage._sequence_numbers["default:1"]
    )
    assert_immutable(holder.get_array(early), OTHER)


def test_clearing_the_public_data_flag_keeps_protection_and_clone_protection():
    simulation = built()
    simulation.built_from_dataset = False
    clone = simulation.clone()
    for target in (simulation, clone):
        assert protects_draws(target)
        assert_immutable(target.calculate(DRAW, 2025), VALUES)
        target._user_input_keys.remove((DRAW, "default", period(2025)))
        with pytest.raises(StoredDrawError, match="simulation's input record"):
            target.calculate(DRAW, 2025)


@pytest.mark.parametrize(
    "method", ["calculate_add", "calculate_divide", "calculate_output"]
)
def test_clearing_the_public_data_flag_keeps_draw_option_refusals(method):
    simulation = built()
    simulation.built_from_dataset = False
    with pytest.raises(StoredDrawError, match=method):
        getattr(simulation, method)(DRAW, 2025)


def test_an_explicit_situation_rebuild_replaces_protected_storage_with_plain_storage():
    simulation = built()
    simulation.build_from_situation(situation())
    assert not protects_draws(simulation)
    holder = simulation.get_holder(DRAW)
    assert type(holder._memory_storage) is InMemoryStorage
    with calculation():
        holder.set_input(period(2026), OTHER)
    np.testing.assert_array_equal(simulation.calculate(DRAW, 2026), OTHER)


def test_a_situation_adopts_data_inputs_as_ordinary_writeable_storage():
    source = built()
    before = snapshot(source)
    simulation = Simulation(situation=situation())
    simulation.build_from_populations(source.populations)
    assert not protects_draws(simulation)
    holder = simulation.get_holder(DRAW)
    assert type(holder._memory_storage) is InMemoryStorage
    assert holder.get_array(period(2025)).flags.writeable
    with calculation():
        holder.set_input(period(2026), OTHER)
    np.testing.assert_array_equal(simulation.calculate(DRAW, 2026), OTHER)
    assert snapshot(source) == before


@pytest.mark.parametrize("target", ["own", "unrelated"])
@pytest.mark.parametrize("operation", ["input", "delete", "demote", "unmark"])
def test_a_formula_cannot_change_a_protected_input_on_any_simulation(target, operation):
    simulation = built()
    changed = simulation if target == "own" else built()
    before = snapshot(changed)
    attempts = []

    class attempts_draw_change(Variable):
        value_type = float
        entity = Person
        definition_period = YEAR
        label = "Attempt to change a stored draw"

        def formula(person, requested, parameters):
            holder = changed.get_holder(DRAW)
            with pytest.raises(StoredDrawError, match=DRAW):
                if operation == "input":
                    holder.set_input(period(2026), OTHER)
                elif operation == "delete":
                    holder.delete_arrays(period(2025))
                elif operation == "demote":
                    holder._memory_storage.mark_derived_except(set())
                else:
                    holder._memory_storage._unmark_input("default:2025")
            attempts.append(operation)
            return np.ones(person.count)

    simulation.tax_benefit_system.add_variable(attempts_draw_change)
    for _ in range(2):
        simulation.delete_arrays("attempts_draw_change", 2025)
        np.testing.assert_array_equal(
            simulation.calculate("attempts_draw_change", 2025), np.ones(3)
        )
        assert snapshot(changed) == before
    assert attempts == [operation, operation]


@pytest.mark.parametrize("after_read", [False, True])
def test_an_output_callback_cannot_store_a_draw_before_or_after_a_calculation(
    after_read,
):
    simulation = built()
    before = snapshot(simulation)

    def output_callback(current, name, requested):
        if after_read:
            current.calculate("age", requested)
        current.get_holder(DRAW).set_input(period(2026), OTHER)
        return np.ones(3)

    class draw_writing_output(Variable):
        value_type = float
        entity = Person
        definition_period = YEAR
        label = "Output that attempts to change a stored draw"
        calculate_output = output_callback

    simulation.tax_benefit_system.add_variable(draw_writing_output)
    with pytest.raises(StoredDrawError, match=f"store an input of {DRAW}"):
        simulation.calculate_output("draw_writing_output", 2025)
    assert snapshot(simulation) == before


def test_core_restores_inputs_as_bytes_before_a_calculation_and_refuses_during_one(
    tmp_path,
):
    from policyengine_core.tools.simulation_dumper import _restore_holder

    directory = tmp_path / DRAW
    directory.mkdir()
    disk = OnDiskStorage(str(directory))
    disk.put(VALUES.copy(), period(2025))
    simulation = built({})

    assert _restore_holder(simulation, DRAW, str(tmp_path), inputs=True) == 1
    assert_immutable(simulation.calculate(DRAW, 2025), VALUES)
    before = snapshot(simulation)
    with calculation():
        with pytest.raises(StoredDrawError, match=f"store an input of {DRAW}"):
            _restore_holder(simulation, DRAW, str(tmp_path), inputs=True)
    assert snapshot(simulation) == before
