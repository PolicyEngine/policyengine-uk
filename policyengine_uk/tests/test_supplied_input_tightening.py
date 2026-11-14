"""Which recorded inputs the supplied-input helpers count.

Invariants:

1. Registration: the three stored inputs (uc_new_claimant_health_element_draw,
   pip_phase_in_draw, would_claim_student_loan) are registered, so the helpers
   answer for them.
2. Ranking: latest_supplied_input_period picks, of the supplied periods that
   start before the request, the one policyengine-core's carry-over order
   (_latest_input_key) ranks last, whatever order they were stored in.
3. Two rules count recorded inputs. The general helpers (supplied_input,
   supplied_input_periods, supplied_by) count an input while it survives, on
   the nearest branch that still stores one, as policyengine-core's
   Simulation._get_recorded_input_array does. _counted_input, which
   stored_draws reads to name a draw's source, counts an input only where a
   calculation reads it: its branch is the first readable branch that stores
   the period, and the tier read there (memory before disk) holds the input.
   A value cached over the input in its own slot leaves it uncounted under
   both rules. A child branch's value over a parent's input, and a memory
   cache over an input on disk, leave it supplied but uncounted.
4. set_model_value refuses the three stored inputs.
"""

import numpy as np
import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
from policyengine_core.data_storage import OnDiskStorage
from policyengine_core.periods import period
from policyengine_core.simulations.simulation import _latest_input_key

from policyengine_uk import Simulation
from policyengine_uk.tests.stored_draw_fixtures import one_person_units_frame
from policyengine_uk.utils.supplied_inputs import (
    REQUIRED_STORED_INPUTS,
    SUPPLIED_INPUT_VARIABLES,
    _counted_input,
    latest_supplied_input_period,
    set_model_value,
    supplied_by,
    supplied_input,
    supplied_input_periods,
)

pytestmark = pytest.mark.usefixtures("cloned_uk_tax_benefit_system")

NEW_COLUMNS = (
    "uc_new_claimant_health_element_draw",
    "pip_phase_in_draw",
    "would_claim_student_loan",
)
DRAW = "pip_phase_in_draw"
# A registered input with no formula, whose readers ask the helpers.
OTHER = "adjusted_net_income"


def built():
    return Simulation(dataset=one_person_units_frame(count=1))


@pytest.fixture(scope="module")
def shared():
    return built()


def periods_of(sim, name=DRAW):
    return supplied_input_periods(sim.get_variable_population(name), name)


def test_new_columns_are_registered_and_required():
    assert set(NEW_COLUMNS) <= SUPPLIED_INPUT_VARIABLES
    assert set(NEW_COLUMNS) == REQUIRED_STORED_INPUTS
    sim = built()
    for name in NEW_COLUMNS:
        population = sim.get_variable_population(name)
        assert supplied_input_periods(population, name) == []
        assert not supplied_by(population, name, period(2025))


@pytest.mark.parametrize("name", NEW_COLUMNS)
def test_set_model_value_refuses_a_stored_input(name):
    sim = built()
    value = np.array([True]) if name == "would_claim_student_loan" else [0.5]
    with pytest.raises(ValueError, match=name):
        set_model_value(sim, name, 2025, value)
    assert periods_of(sim, name) == []
    assert sim.get_holder(name).get_known_periods() == []


def test_set_model_value_still_stores_other_variables():
    sim = built()
    set_model_value(sim, OTHER, 2025, np.array([10.0]))
    assert (
        supplied_input(sim.get_variable_population(OTHER), OTHER, period(2025)) is None
    )


def test_two_periods_starting_on_one_day_rank_by_core_order():
    for order in (
        [period("year:2024:2"), period(2024)],
        [period(2024), period("year:2024:2")],
    ):
        sim = built()
        for stored in order:
            sim.set_input(DRAW, stored, [0.5])
        population = sim.get_variable_population(DRAW)
        # Both start on 1 January 2024; core carries the one that ends last.
        assert latest_supplied_input_period(population, DRAW, period(2026)) == period(
            "year:2024:2"
        )


@settings(
    max_examples=25,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.function_scoped_fixture],
)
@given(
    stored=st.lists(
        st.tuples(st.integers(2020, 2026), st.integers(1, 3)),
        min_size=1,
        max_size=4,
        unique=True,
    ),
    before=st.integers(2020, 2028),
)
def test_latest_supplied_period_matches_core_carry_order(shared, stored, before):
    sim = shared
    sim.delete_arrays(DRAW)
    for start, size in stored:
        sim.set_input(DRAW, period(f"year:{start}:{size}"), [0.5])
    population = sim.get_variable_population(DRAW)
    earlier = [
        period(f"year:{start}:{size}") for start, size in stored if start < before
    ]
    expected = max(earlier, key=lambda p: _latest_input_key(p, "year"), default=None)
    assert latest_supplied_input_period(population, DRAW, period(before)) == expected
    sim.delete_arrays(DRAW)


def test_a_value_cached_over_an_input_in_its_slot_is_not_supplied():
    sim = built()
    sim.set_input(OTHER, 2025, [100])
    population = sim.get_variable_population(OTHER)
    assert supplied_input_periods(population, OTHER) == [period(2025)]
    holder = sim.get_holder(OTHER)
    # A low-level cache write: core drops the slot's input tier but keeps the
    # key in its record of inputs.
    holder.put_in_cache(np.array([999.0]), period(2025), "default", derived=False)
    assert (OTHER, "default", period(2025)) in sim._user_input_keys
    assert supplied_input_periods(population, OTHER) == []
    assert supplied_input(population, OTHER, period(2025)) is None
    assert not supplied_by(population, OTHER, period(2026))


def counted(sim, name=OTHER, branch_name="default", year=2025):
    """_counted_input for the input ``name`` recorded on ``branch_name``."""
    return _counted_input(sim, sim.get_holder(name), (name, branch_name, period(year)))


def test_a_child_branch_value_over_a_parent_input_is_not_counted_on_the_child():
    sim = built()
    sim.set_input(OTHER, 2025, [100])
    child = sim.get_branch("child")
    child_holder = child.get_holder(OTHER)
    child_holder.put_in_cache(np.array([999.0]), period(2025), "child", derived=False)
    # Core reads the child's value from the child, the parent's input from the parent.
    assert child_holder.get_array(period(2025), "child").tolist() == [999]
    assert sim.get_holder(OTHER).get_array(period(2025), "default").tolist() == [100]
    # A calculation on the child reads the child's value, which is no input,
    # not the parent's input.
    assert counted(child) is None
    assert counted(child, branch_name="child") is None
    np.testing.assert_array_equal(counted(sim), [100])
    # The parent's input survives, so the general helpers still count it on
    # the child, as core's own record does.
    child_population = child.get_variable_population(OTHER)
    assert supplied_input_periods(child_population, OTHER) == [period(2025)]
    np.testing.assert_array_equal(
        supplied_input(child_population, OTHER, period(2025)), [100]
    )
    np.testing.assert_array_equal(
        child._get_recorded_input_array(OTHER, period(2025)), [100]
    )
    parent_population = sim.get_variable_population(OTHER)
    assert supplied_input_periods(parent_population, OTHER) == [period(2025)]
    np.testing.assert_array_equal(
        supplied_input(parent_population, OTHER, period(2025)), [100]
    )


def test_a_parent_input_with_nothing_on_the_child_is_supplied_on_the_child():
    sim = built()
    sim.set_input(OTHER, 2025, [100])
    child = sim.get_branch("child")
    population = child.get_variable_population(OTHER)
    assert supplied_input_periods(population, OTHER) == [period(2025)]
    np.testing.assert_array_equal(
        supplied_input(population, OTHER, period(2025)), [100]
    )


def input_on_disk(tmp_path):
    """A simulation whose input for OTHER in 2025 is stored on disk only."""
    sim = built()
    sim.set_input(OTHER, 2025, [100])
    holder = sim.get_holder(OTHER)
    source = period(2025)
    holder._memory_storage.delete(source, "default")
    holder._disk_storage = OnDiskStorage(str(tmp_path))
    holder._disk_storage.put(np.array([100.0]), source, "default")
    holder._user_input_storage[("default", str(source))] = (
        source,
        frozenset({"disk"}),
    )
    return sim, holder, source


def test_an_input_on_disk_counts_when_memory_holds_nothing(tmp_path):
    sim, holder, source = input_on_disk(tmp_path)
    population = sim.get_variable_population(OTHER)
    assert supplied_input_periods(population, OTHER) == [source]
    np.testing.assert_array_equal(supplied_input(population, OTHER, source), [100])
    np.testing.assert_array_equal(counted(sim), [100])


def test_an_input_on_disk_under_a_memory_cache_is_supplied_but_not_counted(
    tmp_path,
):
    sim, holder, source = input_on_disk(tmp_path)
    holder._memory_storage.put(np.array([999.0]), source, "default", derived=True)
    # Core reads memory first, so the cache, not the input on disk.
    assert holder.get_array(source, "default").tolist() == [999]
    assert counted(sim) is None
    # The input on disk survives, so the general helpers still count it.
    population = sim.get_variable_population(OTHER)
    assert supplied_input_periods(population, OTHER) == [source]
    np.testing.assert_array_equal(supplied_input(population, OTHER, source), [100])
