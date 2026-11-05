"""What a read of a stored draw may return, in simulations built from data.

``input_source(population, name, period)`` names the supplied input
policyengine-core reads for a registered draw, returns None where no supplied
input reaches the period, and raises otherwise. ``Simulation.calculate``
applies it before core and checks core's answer after.

Invariants:

1. Provenance: a non-derived value in the slot core reads counts only when it
   is a supplied input; a derived value there only when core's carry source,
   chosen by core's own order, is supplied and the cache equals it; with no
   supplied source only a cached default, as absence. Anything else raises.
2. Requests: only one whole year, in storage form. Months, longer periods and
   aliases raise, with an exact input, a carried one or none.
3. Definitions: the current definition and the holder's must keep the
   registered entity, type and period, with no formula or other computation;
   a neutralised or abolished draw, carry turned off where a read needs it,
   core's macro cache and a disk tier each raise.
4. Dispatch: calculate never answers a draw from the fast cache; core's
   answer must equal the source it read; ADD, DIVIDE and output refuse draws.
5. Writes: a new draw input is refused while a calculation runs or while a
   derived value of the draw is stored, and accepted otherwise.
6. Differential: every accepted read returns exactly what core's own
   calculate returns with the check removed and the fast-cache entry
   cleared; with map_to=None it is the source's array, or with no source the
   holder's default.
7. Changing nothing: input_source leaves storage, records and the fast cache
   as they were.
"""

import copy

import numpy as np
import pytest
from policyengine_core.data_storage import OnDiskStorage
from policyengine_core.model_api import ADD, DIVIDE
from policyengine_core.periods import period
from policyengine_core.simulations import Simulation as CoreSimulation

from policyengine_uk import Simulation
from policyengine_uk.model_api import BenUnit, Person, Variable, YEAR
from policyengine_uk.tests.stored_draw_fixtures import one_person_units_frame
from policyengine_uk.utils.stored_draws import (
    CORE_DISK_KEY_ISSUE,
    InputSource,
    StoredDrawError,
    calculation,
    input_source,
)

pytestmark = pytest.mark.usefixtures("cloned_uk_tax_benefit_system")

DRAW = "pip_phase_in_draw"
GROUP_DRAW = "uc_new_claimant_health_element_draw"
VALUES = np.array([0.25, 0.5, 0.75], dtype=np.float32)
OTHER = np.array([0.125, 0.375, 0.625], dtype=np.float32)


def built(draws=None, name=DRAW):
    """Three one-person units, with ``draws`` (year -> values) supplied."""
    columns = {name: draws} if draws else {}
    years = tuple(sorted({2025, *(draws or {})}))
    return Simulation(
        dataset=one_person_units_frame(count=3, years=years, columns=columns)
    )


def source_of(sim, p, name=DRAW):
    return input_source(sim.get_variable_population(name), name, p)


def core_answer(sim, p, name=DRAW, **kwargs):
    """Core's own calculate, with the check removed and the request's
    fast-cache entry cleared."""
    sim._fast_cache.pop((name, period(p)), None)
    return CoreSimulation.calculate(sim, name, period(p), **kwargs)


def storage_state(sim, name=DRAW):
    holder = sim.get_holder(name)
    memory = holder._memory_storage
    return (
        {key: np.array(value) for key, value in memory._arrays.items()},
        set(memory._inputs),
        set(sim._user_input_keys),
        copy.deepcopy(getattr(holder, "_user_input_storage", {})),
        {key: np.array(value) for key, value in sim._fast_cache.items()},
    )


def assert_same_state(before, after):
    arrays, inputs, keys, locations, fast = before
    arrays2, inputs2, keys2, locations2, fast2 = after
    assert arrays.keys() == arrays2.keys()
    for key in arrays:
        np.testing.assert_array_equal(arrays[key], arrays2[key])
    assert (inputs, keys, locations) == (inputs2, keys2, locations2)
    assert fast.keys() == fast2.keys()


# --- Provenance -------------------------------------------------------------


def test_an_exact_supplied_draw_is_its_own_source_before_and_after_reads():
    sim = built({2025: VALUES})
    for _ in range(3):
        source = source_of(sim, 2025)
        assert isinstance(source, InputSource)
        assert (source.period, source.branch_name, source.tier) == (
            period(2025),
            "default",
            "memory",
        )
        np.testing.assert_array_equal(sim.calculate(DRAW, 2025), VALUES)
    # An exact read stores nothing derived.
    assert sim.get_holder(DRAW).get_known_periods() == [period(2025)]


def test_a_draw_supplied_for_2025_carries_to_2026_on_every_read():
    sim = built({2025: VALUES})
    first = source_of(sim, 2026)
    assert first.period == period(2025)
    for _ in range(3):
        np.testing.assert_array_equal(sim.calculate(DRAW, 2026), VALUES)
        # After the first read core caches the carried value as derived; the
        # check accepts it because it equals its supplied source.
        assert source_of(sim, 2026) == first
    assert sim.get_holder(DRAW).is_derived(period(2026), "default")


def test_no_supplied_draw_is_absence_and_reads_the_default_every_time():
    sim = built()
    assert source_of(sim, 2026) is None
    for _ in range(2):
        np.testing.assert_array_equal(sim.calculate(DRAW, 2026), [1.0, 1.0, 1.0])
        assert source_of(sim, 2026) is None


def test_an_input_only_for_a_later_year_leaves_earlier_years_absent():
    sim = built({2027: VALUES})
    for _ in range(2):
        assert source_of(sim, 2026) is None
        np.testing.assert_array_equal(sim.calculate(DRAW, 2026), [1.0, 1.0, 1.0])
    # Core returns the default without caching it.
    assert period(2026) not in sim.get_holder(DRAW).get_known_periods()


def test_a_model_marked_value_over_an_older_supplied_input_raises():
    sim = built({2025: VALUES})
    sim.set_input(DRAW, 2026, OTHER)
    holder = sim.get_holder(DRAW)
    sim._model_values[(DRAW, "default", period(2026))] = np.array(
        holder.get_array(period(2026), "default")
    )
    with pytest.raises(StoredDrawError, match="not a supplied one"):
        sim.calculate(DRAW, 2026)


def test_a_value_cached_as_non_derived_over_an_input_raises():
    sim = built({2025: VALUES})
    sim.get_holder(DRAW).put_in_cache(OTHER, period(2025), "default", derived=False)
    with pytest.raises(StoredDrawError, match="not a supplied one"):
        source_of(sim, 2025)


def test_a_non_input_carry_source_raises():
    sim = built()
    # Non-derived, so core would carry it, but never set as an input.
    sim.get_holder(DRAW).put_in_cache(OTHER, period(2024), "default", derived=False)
    np.testing.assert_array_equal(core_answer(sim, 2026), OTHER)
    sim._fast_cache.clear()
    sim.get_holder(DRAW).delete_arrays(period(2026))
    with pytest.raises(StoredDrawError, match="not a supplied input"):
        sim.calculate(DRAW, 2026)


def test_a_child_branch_value_over_a_parent_input_raises_on_the_child():
    sim = built({2025: VALUES})
    child = sim.get_branch("child")
    child.get_holder(DRAW).put_in_cache(OTHER, period(2025), "child", derived=False)
    with pytest.raises(StoredDrawError, match="branch 'child'"):
        source_of(child, 2025)
    assert source_of(sim, 2025).branch_name == "default"


def test_a_child_branch_reads_its_parent_input_and_carried_cache():
    sim = built({2025: VALUES})
    np.testing.assert_array_equal(sim.calculate(DRAW, 2026), VALUES)
    child = sim.get_branch("child")
    for p in (2025, 2026):
        source = source_of(child, p)
        assert (source.period, source.branch_name) == (period(2025), "default")
        np.testing.assert_array_equal(child.calculate(DRAW, p), VALUES)


def test_a_clone_keeps_its_source():
    sim = built({2025: VALUES})
    sim.calculate(DRAW, 2026)
    clone = sim.clone()
    assert source_of(clone, 2026).period == period(2025)
    np.testing.assert_array_equal(clone.calculate(DRAW, 2026), VALUES)


def test_a_default_cached_before_an_earlier_input_is_supplied():
    sim = built()
    sim.calculate(DRAW, 2026)  # caches the default as derived
    # The public setter refuses while the derived default stands.
    with pytest.raises(StoredDrawError, match="after the simulation has calculated"):
        sim.set_input(DRAW, 2025, VALUES)
    # A holder-level write gets past it; the surviving default then differs
    # from the new source, so the read raises.
    sim.get_holder(DRAW).set_input(period(2025), VALUES)
    with pytest.raises(StoredDrawError, match="differs from its supplied source"):
        sim.calculate(DRAW, 2026)


def test_a_stale_non_default_cache_with_no_source_raises():
    sim = built()
    sim.get_holder(DRAW)._memory_storage.put(
        OTHER, period(2026), "default", derived=True
    )
    with pytest.raises(StoredDrawError, match="not the default"):
        sim.calculate(DRAW, 2026)


def test_a_cached_default_is_compared_with_the_holders_own_default():
    sim = built()
    sim.calculate(DRAW, 2026)

    class pip_phase_in_draw(Variable):
        value_type = float
        entity = Person
        definition_period = YEAR
        default_value = 0.5
        label = "draw with another default"

    sim.tax_benefit_system.update_variable(pip_phase_in_draw)
    # The holder keeps the definition it was made with, so its default 1.0.
    assert source_of(sim, 2026) is None


def test_input_source_changes_nothing():
    sim = built({2025: VALUES})
    sim.calculate(DRAW, 2026)
    sim.calculate(DRAW, 2025)
    before = storage_state(sim)
    for p in (2024, 2025, 2026, 2027):
        source_of(sim, p)
    assert_same_state(before, storage_state(sim))


# --- Root, branch and deletion ---------------------------------------------


def test_root_holder_replacement_raises_on_an_unequal_cache_and_keeps_an_equal_one():
    sim = built({2025: VALUES})
    sim.calculate(DRAW, 2026)
    holder = sim.get_holder(DRAW)
    holder.set_input(period(2025), VALUES)
    np.testing.assert_array_equal(sim.calculate(DRAW, 2026), VALUES)
    holder.set_input(period(2025), OTHER)
    with pytest.raises(StoredDrawError, match="differs from its supplied source"):
        sim.calculate(DRAW, 2026)


def test_branch_holder_replacement_recomputes_from_the_new_source():
    sim = built({2025: VALUES})
    branch = sim.get_branch("reform")
    np.testing.assert_array_equal(branch.calculate(DRAW, 2026), VALUES)
    branch.get_holder(DRAW).set_input(period(2025), OTHER, "reform")
    np.testing.assert_array_equal(branch.calculate(DRAW, 2026), OTHER)
    np.testing.assert_array_equal(sim.calculate(DRAW, 2026), VALUES)


def test_deleting_the_source_exposes_an_equal_earlier_input_or_raises():
    sim = built({2024: VALUES, 2025: VALUES})
    sim.calculate(DRAW, 2026)
    sim.get_holder(DRAW).delete_arrays(period(2025))
    source = source_of(sim, 2026)
    assert source.period == period(2024)
    np.testing.assert_array_equal(sim.calculate(DRAW, 2026), VALUES)

    sim = built({2025: VALUES})
    sim.calculate(DRAW, 2026)
    sim.get_holder(DRAW)._memory_storage.delete(period(2025), "default")
    with pytest.raises(StoredDrawError, match="no supplied input"):
        source_of(sim, 2026)


def test_a_rebuild_drops_the_fast_cache_and_a_new_holder_recomputes():
    sim = built({2025: VALUES})
    sim.calculate(DRAW, 2026)
    sim._fast_cache[(DRAW, period(2026))] = OTHER
    other = built({2024: OTHER})
    sim.build_from_populations(other.populations)
    assert not sim._fast_cache
    assert source_of(sim, 2026).period == period(2024)
    np.testing.assert_array_equal(sim.calculate(DRAW, 2026), OTHER)


def test_holder_cache_opt_out_reads_storage_each_time():
    sim = built({2025: VALUES})
    sim.get_holder(DRAW)._do_not_store = True
    for _ in range(2):
        np.testing.assert_array_equal(sim.calculate(DRAW, 2026), VALUES)
    sim.set_input(DRAW, 2025, OTHER)
    np.testing.assert_array_equal(sim.calculate(DRAW, 2026), OTHER)


# --- Requests and definitions -----------------------------------------------


@pytest.mark.parametrize(
    "request_period",
    ["2026-06", "year:2026:2", "month:2026-06:12", "year:2025-01-15"],
)
@pytest.mark.parametrize("supplied", [{2026: VALUES}, {2025: VALUES}, None])
def test_requests_other_than_one_stored_year_raise(request_period, supplied):
    sim = built(supplied)
    with pytest.raises(StoredDrawError, match="read only for one year"):
        sim.calculate(DRAW, request_period)


def test_add_divide_and_output_refuse_a_draw():
    sim = built({2025: VALUES})
    with pytest.raises(StoredDrawError, match="calculate_add"):
        sim.calculate_add(DRAW, "year:2025:2")
    with pytest.raises(StoredDrawError, match="calculate_divide"):
        sim.calculate_divide(DRAW, "2025-06")
    with pytest.raises(StoredDrawError, match="calculate_output"):
        sim.calculate_output(DRAW, 2025)
    population = sim.get_variable_population(DRAW)
    with pytest.raises(StoredDrawError):
        population(DRAW, period("2025-06"), options=[DIVIDE])
    with pytest.raises(StoredDrawError):
        population(DRAW, period("year:2025:2"), options=[ADD])


def test_a_neutralised_draw_raises():
    sim = built({2025: VALUES})
    sim.tax_benefit_system.neutralize_variable(DRAW)
    for p in (2025, 2026):
        with pytest.raises(StoredDrawError, match="neutralised"):
            sim.calculate(DRAW, p)


def test_a_draw_abolished_by_parameter_raises(monkeypatch):
    sim = built({2025: VALUES})
    system = sim.tax_benefit_system
    real = system.parameters

    class Abolitions:
        def __getitem__(self, name):
            return name == DRAW

    class Node:
        def __init__(self, inner):
            self.inner = inner

        def __getattr__(self, name):
            if name == "abolitions":
                return Abolitions()
            return getattr(self.inner, name)

    class At:
        def __init__(self, inner):
            self.gov = Node(inner.gov)

    def parameters(p):
        return At(real(p))

    monkeypatch.setattr(system, "parameters", parameters, raising=False)
    with pytest.raises(StoredDrawError, match="abolishes"):
        sim.calculate(DRAW, 2026)


def test_redefinitions_raise():
    for attributes in (
        {"formula": lambda person, period, parameters: 0.5},
        {"adds": ["age"]},
        {"value_type": int, "default_value": 1},
        {"requires_computation_after": "age"},
    ):
        sim = built({2025: VALUES})
        body = dict(
            value_type=float,
            entity=Person,
            definition_period=YEAR,
            default_value=1.0,
            label="redefined draw",
        )
        body.update(attributes)
        sim.tax_benefit_system.update_variable(type(DRAW, (Variable,), body))
        for p in (2025, 2026):
            with pytest.raises(StoredDrawError, match="current definition"):
                sim.calculate(DRAW, p)


def test_a_draw_removed_from_the_system_raises():
    sim = built({2025: VALUES})
    population = sim.get_variable_population(DRAW)
    del sim.tax_benefit_system.variables[DRAW]
    with pytest.raises(StoredDrawError, match="has no current definition"):
        input_source(population, DRAW, 2025)


def test_a_draw_moved_to_another_entity_raises():
    sim = built({2025: VALUES})
    sim.tax_benefit_system.update_variable(
        type(
            DRAW,
            (Variable,),
            dict(
                value_type=float,
                entity=BenUnit,
                definition_period=YEAR,
                default_value=1.0,
                label="draw on benefit units",
            ),
        )
    )
    with pytest.raises(StoredDrawError):
        source_of(sim, 2025)


def test_a_holder_kept_from_another_definition_raises():
    sim = built({2025: VALUES})
    holder = sim.get_holder(DRAW)
    retained = copy.copy(holder.variable)
    retained.value_type = int
    holder.variable = retained
    with pytest.raises(StoredDrawError, match="holder's definition"):
        sim.calculate(DRAW, 2025)


def test_carry_off_raises_only_where_a_read_needs_it():
    sim = built({2025: VALUES})
    sim.tax_benefit_system.auto_carry_over_input_variables = False
    try:
        np.testing.assert_array_equal(sim.calculate(DRAW, 2025), VALUES)
        np.testing.assert_array_equal(sim.calculate(DRAW, 2025), VALUES)
        with pytest.raises(StoredDrawError, match="does not carry inputs over"):
            sim.calculate(DRAW, 2026)
        assert source_of(sim, 2024) is None
    finally:
        sim.tax_benefit_system.auto_carry_over_input_variables = True


def test_the_macro_cache_raises():
    sim = built({2025: VALUES})
    sim.macro_cache_read = True
    with pytest.raises(StoredDrawError, match="macro cache"):
        sim.calculate(DRAW, 2025)


@pytest.mark.parametrize(
    "route", ["attached", "cloned_holder", "branch_with_underscore"]
)
def test_a_disk_tier_raises_naming_core_526(route, tmp_path):
    sim = built({2025: VALUES})
    target = (
        sim.get_branch("with_underscore") if route == "branch_with_underscore" else sim
    )
    holder = target.get_holder(DRAW)
    holder._disk_storage = OnDiskStorage(str(tmp_path))
    if route == "cloned_holder":
        population = target.get_variable_population(DRAW)
        population._holders[DRAW] = holder.clone(population)
    for p in (2025, 2026):
        with pytest.raises(StoredDrawError, match=CORE_DISK_KEY_ISSUE):
            target.calculate(DRAW, p)


# --- Dispatch ---------------------------------------------------------------


def test_the_fast_cache_never_answers_a_draw():
    sim = built({2025: VALUES})
    sim.calculate(DRAW, 2026)
    sim._fast_cache[(DRAW, period(2026))] = OTHER
    np.testing.assert_array_equal(sim.calculate(DRAW, 2026), VALUES)


def test_a_wrong_answer_from_core_raises(monkeypatch):
    sim = built({2025: VALUES})
    real = CoreSimulation.calculate

    def wrong(self, name, *args, **kwargs):
        result = real(self, name, *args, **kwargs)
        return result * 0 if name == DRAW else result

    monkeypatch.setattr(CoreSimulation, "calculate", wrong)
    with pytest.raises(StoredDrawError, match="not its supplied"):
        sim.calculate(DRAW, 2026)


def test_a_spiral_default_from_core_raises():
    sim = built({2025: VALUES})
    for year in range(2010, 2010 + sim.max_spiral_loops):
        sim.tracer.stack.append(
            {"name": DRAW, "period": period(year), "branch_name": "default"}
        )
    try:
        with pytest.raises(StoredDrawError, match="not its supplied"):
            sim.calculate(DRAW, 2026)
    finally:
        del sim.tracer.stack[:]


def test_tracing_and_map_to_return_what_core_returns():
    sim = built({2025: VALUES}, name=GROUP_DRAW)
    sim.trace = True
    for p in (2025, 2026):
        for map_to in (None, "person", "household"):
            ours = np.asarray(sim.calculate(GROUP_DRAW, p, map_to=map_to))
            theirs = np.asarray(core_answer(sim, p, name=GROUP_DRAW, map_to=map_to))
            np.testing.assert_array_equal(ours, theirs)


def test_differential_against_core_calculate():
    cases = [
        ({2025: VALUES}, [2024, 2025, 2026, 2030]),
        ({2027: VALUES}, [2025, 2026, 2027, 2028]),
        ({2025: VALUES, 2027: OTHER}, [2025, 2026, 2027, 2028]),
        (None, [2025, 2026]),
    ]
    for supplied, requests in cases:
        sim = built(supplied)
        for p in requests * 2:
            source = source_of(sim, p)
            ours = np.asarray(sim.calculate(DRAW, p))
            holder = sim.get_holder(DRAW)
            expected = (
                holder.default_array()
                if source is None
                else np.asarray(
                    holder._memory_storage.get(source.period, source.branch_name)
                )
            )
            np.testing.assert_array_equal(ours, expected)
            assert ours.dtype == np.float32
            np.testing.assert_array_equal(ours, np.asarray(core_answer(sim, p)))


# --- Writes -----------------------------------------------------------------


def test_a_draw_cannot_be_set_while_any_calculation_runs():
    sim = built()
    other = built()
    with calculation():
        for target in (sim, other):
            with pytest.raises(StoredDrawError, match="while a calculation"):
                target.set_input(DRAW, 2025, VALUES)
    assert sim.get_holder(DRAW).get_known_periods() == []


def test_a_draw_set_from_inside_another_variables_formula_is_refused():
    sim = built()

    class writes_a_draw(Variable):
        value_type = float
        entity = Person
        definition_period = YEAR
        label = "writes a draw"

        def formula(person, period, parameters):
            person.simulation.set_input(DRAW, period, VALUES)
            return 0

    sim.tax_benefit_system.add_variable(writes_a_draw)
    with pytest.raises(StoredDrawError, match="while a calculation"):
        sim.calculate("writes_a_draw", 2025)


@pytest.mark.parametrize("before", ["no_read", "exact_reads", "opt_out"])
def test_a_new_draw_is_accepted_before_any_derived_value(before):
    sim = built({2025: VALUES})
    if before == "exact_reads":
        sim.calculate(DRAW, 2025)
        sim.calculate(DRAW, 2025)
    if before == "opt_out":
        sim.get_holder(DRAW)._do_not_store = True
        sim.calculate(DRAW, 2026)
    sim.set_input(DRAW, 2025, OTHER)
    np.testing.assert_array_equal(sim.calculate(DRAW, 2025), OTHER)
    np.testing.assert_array_equal(sim.calculate(DRAW, 2026), OTHER)


def test_a_new_draw_is_refused_after_a_carried_read_until_a_reset():
    sim = built({2025: VALUES})
    sim.calculate(DRAW, 2026)
    with pytest.raises(StoredDrawError, match="after the simulation has calculated"):
        sim.set_input(DRAW, 2025, OTHER)
    np.testing.assert_array_equal(sim.calculate(DRAW, 2026), VALUES)
    sim.reset_calculations()
    sim.set_input(DRAW, 2025, OTHER)
    np.testing.assert_array_equal(sim.calculate(DRAW, 2026), OTHER)


def test_reforms_and_resets_keep_the_supplied_draw():
    sim = built({2025: VALUES})
    sim.calculate(DRAW, 2026)
    sim.apply_reform({"gov.dwp.pip.daily_living.enhanced": {"2025-01-01": 200}})
    assert source_of(sim, 2026).period == period(2025)
    np.testing.assert_array_equal(sim.calculate(DRAW, 2026), VALUES)
    sim.reset_calculations()
    np.testing.assert_array_equal(sim.calculate(DRAW, 2026), VALUES)
    branch = sim.get_branch("measurement")
    np.testing.assert_array_equal(branch.calculate(DRAW, 2026), VALUES)


def test_situations_keep_cores_path():
    sim = Simulation(
        situation={
            "people": {"adult": {"age": {2025: 30}}},
            "benunits": {"benunit": {"members": ["adult"]}},
            "households": {"household": {"members": ["adult"]}},
        }
    )
    np.testing.assert_array_equal(
        sim.calculate_divide(DRAW, "2025-06"), np.float32([1 / 12])
    )


def test_two_inputs_starting_on_one_day_carry_the_one_core_carries():
    sim = built()
    sim.set_input(DRAW, 2024, VALUES)
    sim.set_input(DRAW, "year:2024:2", OTHER)
    for p in (2025, 2026, 2025):
        source = source_of(sim, p)
        assert source.period == period("year:2024:2")
        np.testing.assert_array_equal(sim.calculate(DRAW, p), OTHER)
        np.testing.assert_array_equal(core_answer(sim, p), OTHER)


def test_a_register_only_input_uses_its_tiers_mark():
    sim = built({2025: VALUES})
    holder = sim.get_holder(DRAW)
    holder._user_input_storage.clear()
    assert source_of(sim, 2026).period == period(2025)
    np.testing.assert_array_equal(sim.calculate(DRAW, 2026), VALUES)


def test_a_dumped_and_restored_draw_is_its_own_source(tmp_path):
    from policyengine_core.tools.simulation_dumper import (
        dump_simulation,
        restore_simulation,
    )

    sim = built({2025: VALUES})
    dump_simulation(sim, str(tmp_path / "dump"))
    restored = restore_simulation(str(tmp_path / "dump"), sim.tax_benefit_system)
    source = source_of(restored, 2026)
    assert source.period == period(2025)


def test_an_after_load_modifier_input_is_supplied_and_its_baseline_lacks_it():
    from policyengine_uk.model_api import Scenario

    def supply(simulation):
        simulation.set_input(DRAW, 2025, VALUES)

    sim = Simulation(
        dataset=one_person_units_frame(count=3),
        scenario=Scenario(simulation_modifier=supply),
    )
    assert source_of(sim, 2026).period == period(2025)
    np.testing.assert_array_equal(sim.calculate(DRAW, 2026), VALUES)
    assert source_of(sim.baseline, 2026) is None


def test_a_reform_formula_reads_the_draw_through_the_check():
    sim = built({2025: VALUES})

    class doubles_the_draw(Variable):
        value_type = float
        entity = Person
        definition_period = YEAR
        label = "twice the draw"

        def formula(person, period, parameters):
            return person(DRAW, period) * 2

    sim.tax_benefit_system.add_variable(doubles_the_draw)
    np.testing.assert_array_equal(sim.calculate("doubles_the_draw", 2026), VALUES * 2)
    sim.get_holder(DRAW)._memory_storage.put(
        OTHER, period(2027), "default", derived=True
    )
    with pytest.raises(StoredDrawError, match="differs from its supplied source"):
        sim.calculate("doubles_the_draw", 2027)
    missing = built()
    missing.tax_benefit_system.add_variable(doubles_the_draw)
    np.testing.assert_array_equal(
        missing.calculate("doubles_the_draw", 2026), [2, 2, 2]
    )
