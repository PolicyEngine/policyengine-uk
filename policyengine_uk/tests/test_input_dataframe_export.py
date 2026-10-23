"""Input export preserves supplied values, including formula overrides.

All amounts below are synthetic input identities, not statutory rate oracles.
"""

import numpy as np
import pandas as pd
import pytest
from policyengine_core.data_storage import OnDiskStorage
from policyengine_core.periods import period
from policyengine_core.simulations import Simulation as CoreSimulation

from policyengine_uk import Simulation
from policyengine_uk.data import UKSingleYearDataset
from policyengine_uk.data.input_dataframe import with_identifiers_in_each_year
from policyengine_uk.scenarios import no_economic_assumptions
from policyengine_uk.model_api import Reform
from policyengine_uk.utils.supplied_inputs import set_model_value

pytestmark = pytest.mark.usefixtures("cloned_uk_tax_benefit_system")
YEAR = 2025
FORMULA = "state_pension_reported"


def built():
    return Simulation(
        situation={
            "people": {"person": {"age": {YEAR: 71}}},
            "benunits": {"benunit": {"members": ["person"]}},
            "households": {"household": {"members": ["person"]}},
        }
    )


def values(simulation, variable, year=YEAR):
    return simulation.to_input_dataframe()[f"{variable}__{year}"].tolist()


def test_dataset_formula_input_round_trip_preserves_final_pension():
    dataset = UKSingleYearDataset(
        person=pd.DataFrame(
            {
                "person_id": [1],
                "person_benunit_id": [1],
                "person_household_id": [1],
                "age": [71],
                FORMULA: [9_500.0],
            }
        ),
        benunit=pd.DataFrame({"benunit_id": [1]}),
        household=pd.DataFrame(
            {
                "household_id": [1],
                "region": ["LONDON"],
                "council_tax": [0],
                "tenure_type": ["OWNED_OUTRIGHT"],
                "rent": [0],
            }
        ),
        fiscal_year=YEAR,
    )
    original = Simulation(dataset=dataset, scenario=no_economic_assumptions)
    assert original.calculate("state_pension", YEAR).tolist() == [9_500]
    exported = original.to_input_dataframe()
    reloaded = Simulation(dataset=exported, scenario=no_economic_assumptions)
    assert reloaded.calculate("state_pension", YEAR).tolist() == [9_500]
    assert exported[f"{FORMULA}__{YEAR}"].tolist() == [9_500]
    assert reloaded.calculate(FORMULA, YEAR).tolist() == [9_500]


@pytest.mark.parametrize("variable", ["hours_worked", FORMULA, "employment_income"])
def test_supplied_structural_formula_and_adds_values_are_exported(variable):
    sim = built()
    sim.set_input(variable, YEAR, [100])
    assert values(sim, variable) == [100]


def test_export_does_not_calculate_values(monkeypatch):
    sim = built()
    sim.set_input(FORMULA, YEAR, [100])

    def calculate(*args, **kwargs):
        pytest.fail("default export must read supplied arrays, not calculate")

    monkeypatch.setattr(sim, "calculate", calculate)
    assert values(sim, FORMULA) == [100]


def test_derived_only_and_carried_periods_are_not_inputs():
    sim = built()
    sim.set_input("hours_worked", YEAR, [100])
    assert sim.calculate("hours_worked", YEAR + 1).tolist() == [100]
    sim.calculate("state_pension", YEAR)
    exported = sim.to_input_dataframe()
    assert "hours_worked__2026" not in exported
    assert "state_pension__2025" not in exported
    assert exported["hours_worked__2025"].tolist() == [100]


@pytest.mark.parametrize("disk_survives", [False, True])
def test_only_a_surviving_recorded_storage_tier_is_exported(disk_survives, tmp_path):
    sim = built()
    sim.set_input("hours_worked", YEAR, [100])
    holder = sim.get_holder("hours_worked")
    source_period = period(YEAR)
    if disk_survives:
        holder._disk_storage = OnDiskStorage(str(tmp_path))
        holder._disk_storage.put(np.array([100.0]), source_period, sim.branch_name)
        holder._user_input_storage[(sim.branch_name, str(source_period))] = (
            source_period,
            frozenset({"disk"}),
        )
    holder._memory_storage.put(
        np.array([999.0]), source_period, sim.branch_name, derived=True
    )
    exported = sim.to_input_dataframe()
    if disk_survives:
        assert exported["hours_worked__2025"].tolist() == [100]
    else:
        assert "hours_worked__2025" not in exported


@pytest.mark.parametrize("actual_input", [False, True])
def test_model_values_are_omitted_until_a_real_input_is_set(actual_input):
    sim = built()
    set_model_value(sim, "adjusted_net_income", YEAR, np.array([123.0]))
    if actual_input:
        sim.set_input("adjusted_net_income", YEAR, [123])
        assert values(sim, "adjusted_net_income") == [123]
    else:
        assert "adjusted_net_income__2025" not in sim.to_input_dataframe()


def test_deleted_array_with_a_stale_key_is_not_exported():
    sim = built()
    sim.set_input(FORMULA, YEAR, [100])
    holder = sim.get_holder(FORMULA)
    holder._memory_storage.delete(period(YEAR))
    assert (FORMULA, sim.branch_name, period(YEAR)) in sim._user_input_keys
    assert f"{FORMULA}__{YEAR}" not in sim.to_input_dataframe()


@pytest.mark.parametrize("copy_kind", ["clone", "branch"])
def test_copies_keep_independent_inputs_and_model_markers(copy_kind):
    parent = built()
    set_model_value(parent, "adjusted_net_income", YEAR, np.array([123.0]))
    parent.set_input(FORMULA, YEAR, [100])
    child = parent.clone() if copy_kind == "clone" else parent.get_branch("child")
    child.set_input(FORMULA, YEAR, [200])
    child.set_input("adjusted_net_income", YEAR, [123])
    assert values(parent, FORMULA) == [100]
    assert values(child, FORMULA) == [200]
    assert "adjusted_net_income__2025" not in parent.to_input_dataframe()
    assert values(child, "adjusted_net_income") == [123]


def test_nearest_surviving_branch_input_precedes_ancestors():
    parent = built()
    parent.set_input(FORMULA, YEAR, [100])
    child = parent.get_branch("child")
    child.set_input(FORMULA, YEAR, [200])
    nested = child.get_branch("nested")
    assert values(nested, FORMULA) == [200]
    nested.set_input(FORMULA, YEAR, [300])
    assert values(nested, FORMULA) == [300]
    assert values(parent, FORMULA) == [100]


def test_entity_projection_row_order_dates_and_round_trip():
    supplied = pd.DataFrame(
        {
            "person_id__2025": [30, 10, 20],
            "person_benunit_id__2025": [2, 1, 2],
            "person_household_id__2025": [2, 1, 2],
            "age__2025": [40, 41, 42],
            "benunit_reported_capital__2025": [200, 100, 200],
            "council_tax__2025": [2_000, 1_000, 2_000],
            "state_pension_reported__2025": [300, 100, 200],
        }
    )
    sim = Simulation(dataset=supplied)
    sim.set_input(FORMULA, 2027, [600, 400, 500])
    exported = sim.to_input_dataframe()
    for variable in ("benunit_reported_capital", "council_tax", FORMULA):
        assert (
            exported[f"{variable}__2025"].tolist()
            == supplied[f"{variable}__2025"].tolist()
        )
    assert exported[f"{FORMULA}__2027"].tolist() == [600, 400, 500]
    assert exported["person_id__2027"].tolist() == [30, 10, 20]
    reloaded = Simulation(dataset=exported)
    pd.testing.assert_frame_equal(reloaded.to_input_dataframe().copy(), exported.copy())


def test_only_periods_matching_the_variable_definition_are_exported():
    sim = built()
    holder = sim.get_holder(FORMULA)
    monthly = period("2025-02")
    holder._memory_storage.put(np.array([100.0]), monthly, sim.branch_name)
    sim._user_input_keys.add((FORMULA, sim.branch_name, monthly))
    assert f"{FORMULA}__2025-02" not in sim.to_input_dataframe()


def test_annual_periods_keep_their_dates_and_sorted_order():
    sim = built()
    for source_period, amount in [(2027, 300), (2025, 100), (2026, 200)]:
        sim.set_input(FORMULA, source_period, [amount])
    exported = sim.to_input_dataframe()
    columns = [name for name in exported if name.startswith(f"{FORMULA}__")]
    assert columns == [f"{FORMULA}__{year}" for year in (2025, 2026, 2027)]
    assert exported[columns].iloc[0].tolist() == [100, 200, 300]


def test_an_array_without_an_input_record_is_not_exported():
    sim = built()
    sim.get_holder(FORMULA)._memory_storage.put(np.array([999.0]), period(YEAR))
    assert f"{FORMULA}__{YEAR}" not in sim.to_input_dataframe()


def test_register_only_input_uses_its_storage_marks():
    sim = built()
    sim.set_input(FORMULA, YEAR, [100])
    holder = sim.get_holder(FORMULA)
    holder._user_input_storage.pop((sim.branch_name, str(period(YEAR))))
    assert values(sim, FORMULA) == [100]


def test_a_replaced_child_input_falls_back_to_the_surviving_parent():
    parent = built()
    parent.set_input(FORMULA, YEAR, [100])
    child = parent.get_branch("child")
    child.set_input(FORMULA, YEAR, [200])
    child.get_holder(FORMULA)._memory_storage.put(
        np.array([999.0]), period(YEAR), child.branch_name, derived=True
    )
    assert values(child, FORMULA) == [100]
    assert values(parent, FORMULA) == [100]


def test_deletion_then_real_input_clears_a_model_marker():
    sim = built()
    set_model_value(sim, "adjusted_net_income", YEAR, np.array([123.0]))
    sim.delete_arrays("adjusted_net_income", YEAR)
    sim.set_input("adjusted_net_income", YEAR, [123])
    assert values(sim, "adjusted_net_income") == [123]


def test_a_rebuild_does_not_export_a_dropped_input_or_its_derived_replacement():
    sim = built()
    sim.set_input(FORMULA, YEAR, [100])
    sim.build_from_situation(
        {
            "people": {"other": {"age": {YEAR: 40}}},
            "benunits": {"other": {"members": ["other"]}},
            "households": {"other": {"members": ["other"]}},
        }
    )
    sim.get_holder(FORMULA)._memory_storage.put(
        np.array([999.0]), period(YEAR), sim.branch_name, derived=True
    )
    assert f"{FORMULA}__{YEAR}" not in sim.to_input_dataframe()


def test_a_reform_input_survives_a_calculation_reset():
    class EnterPension(Reform):
        def apply(self):
            self.simulation.set_input(FORMULA, YEAR, [100])

    sim = built()
    sim.apply_reform(EnterPension)
    sim.reset_calculations()
    assert values(sim, FORMULA) == [100]


def test_export_does_not_change_provenance_or_stored_values():
    sim = built()
    sim.set_input(FORMULA, YEAR, [100])
    holder = sim.get_holder(FORMULA)
    keys = set(sim._user_input_keys)
    records = dict(holder._user_input_storage)
    stored = holder._memory_storage.get(period(YEAR)).copy()
    first = sim.to_input_dataframe()
    pd.testing.assert_frame_equal(sim.to_input_dataframe().copy(), first.copy())
    assert sim._user_input_keys == keys
    assert holder._user_input_storage == records
    np.testing.assert_array_equal(holder._memory_storage.get(period(YEAR)), stored)


def test_computed_export_keeps_core_delegation():
    sim = built()
    sim.set_input(FORMULA, YEAR, [100])
    sim.calculate("state_pension", YEAR)
    expected = with_identifiers_in_each_year(
        CoreSimulation.to_input_dataframe(sim, include_computed_variables=True),
        sim.tax_benefit_system,
    )
    pd.testing.assert_frame_equal(
        sim.to_input_dataframe(include_computed_variables=True).copy(), expected.copy()
    )
