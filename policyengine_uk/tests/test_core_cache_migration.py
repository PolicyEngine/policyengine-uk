"""Country integration with Core cache contracts, using one-person fixtures."""

from unittest.mock import Mock

import numpy as np
import pytest
from policyengine_core.entities import build_entity
from policyengine_core.parameters import ParameterNode
from policyengine_core.periods import YEAR, period as period_
from policyengine_core.simulations import Simulation as CoreSimulation
from policyengine_core.taxbenefitsystems import TaxBenefitSystem
from policyengine_core.tracers import FullTracer, SimpleTracer
from policyengine_core.variables import Variable

import policyengine_uk.simulation as simulation_module
import policyengine_uk.tax_benefit_system as system_module
from policyengine_uk import Simulation
from policyengine_uk.entities import BenUnit, Household, Person
from policyengine_uk.utils.supplied_inputs import supplied_input, supplied_input_periods


TestPerson = build_entity("person", "people", "Person", "Test person", is_person=True)


class input_amount(Variable):
    label = "Fixture supplied amount"
    entity = TestPerson
    value_type = float
    definition_period = YEAR


class doubled_amount(Variable):
    label = "Fixture doubled amount"
    entity = TestPerson
    value_type = float
    definition_period = YEAR

    def formula(person, period):
        return person("input_amount", period) * 2


@pytest.fixture
def simulation():
    system = TaxBenefitSystem([TestPerson])
    system.replace_parameters(ParameterNode("", data={}))
    system.auto_carry_over_input_variables = True
    system.add_variables(input_amount, doubled_amount)
    sim = Simulation.__new__(Simulation)
    CoreSimulation.__init__(
        sim, tax_benefit_system=system, situation={"input_amount": {2025: 10}}
    )
    return sim


@pytest.fixture
def tiny_uk_system(monkeypatch):
    """Keep UK construction but avoid loading the entire country per case."""
    tree = ParameterNode("", data={"amount": {"values": {"2025-01-01": 10}}})
    monkeypatch.setattr(system_module, "_processed_parameters_cache", tree)
    monkeypatch.setattr(
        system_module.CountryTaxBenefitSystem,
        "add_variables_from_directory",
        lambda self, path: None,
    )
    return tree


def test_country_system_runs_core_initialization(tiny_uk_system):
    system = system_module.CountryTaxBenefitSystem()
    assert system.data_modified is False
    assert system.variables == {}
    assert system.variable_module_metadata == {}
    assert system.group_entity_keys == ["benunit", "household"]
    variable = system.add_variable(input_amount)
    for owned, template in zip(system.entities, [Person, BenUnit, Household]):
        assert owned is not template
        assert owned.get_variable("input_amount") is variable


def test_warm_parameters_are_installed_through_core(monkeypatch, tiny_uk_system):
    installed = []
    original = TaxBenefitSystem.replace_parameters

    def replace(system, tree):
        installed.append(tree)
        original(system, tree)

    monkeypatch.setattr(TaxBenefitSystem, "replace_parameters", replace)
    system = system_module.CountryTaxBenefitSystem()
    assert installed[-1] is system.parameters
    assert installed[-1] is not tiny_uk_system
    assert system.get_parameters_at_instant("2025").amount == 10


def test_warm_systems_do_not_share_parameter_mutations(tiny_uk_system):
    first = system_module.CountryTaxBenefitSystem()
    second = system_module.CountryTaxBenefitSystem()
    first.parameters.amount.update(period="2025", value=20)
    assert first.get_parameters_at_instant("2025").amount == 20
    assert second.get_parameters_at_instant("2025").amount == 10
    assert tiny_uk_system("2025").amount == 10


def test_uk_constructor_does_not_run_generic_parameter_processing(
    monkeypatch, tiny_uk_system
):
    generic = Mock(side_effect=AssertionError("UK owns its parameter processing"))
    monkeypatch.setattr(TaxBenefitSystem, "add_abolition_parameters", generic)
    system_module.CountryTaxBenefitSystem()
    generic.assert_not_called()


@pytest.mark.parametrize("trace", [False, True])
def test_uk_simulation_initializes_core_state_before_loading(monkeypatch, trace):
    system = TaxBenefitSystem([TestPerson])
    system.add_variable(input_amount)
    monkeypatch.setattr(simulation_module, "CountryTaxBenefitSystem", lambda: system)

    class StopLoading(Exception):
        pass

    def capture(sim, situation):
        assert sim.tax_benefit_system.simulation is sim
        assert sim.parent_branch is None
        assert sim.has_axes is False
        assert sim.supplied_input_periods("input_amount") == []
        assert sim.input_variables == []
        assert type(sim.tracer) is (FullTracer if trace else SimpleTracer)
        assert sim.populations["person"].simulation is sim
        raise StopLoading

    monkeypatch.setattr(Simulation, "build_from_situation", capture)
    with pytest.raises(StopLoading):
        Simulation(situation={"input_amount": 10}, trace=trace)


@pytest.mark.parametrize("year", [2025, 2026])
def test_supplied_helpers_accept_any_core_variable(simulation, year):
    simulation.set_input("input_amount", year, [12])
    population = simulation.get_variable_population("input_amount")
    assert supplied_input(population, "input_amount", period_(year)).tolist() == [12]
    assert period_(year) in supplied_input_periods(population, "input_amount")


@pytest.mark.parametrize("branch_name", [None, "child", "nested"])
@pytest.mark.parametrize("delete_through", ["simulation", "holder"])
def test_deleted_inputs_never_reappear_as_supplied(
    simulation, branch_name, delete_through
):
    sim = simulation
    if branch_name:
        sim = simulation.get_branch("child")
        if branch_name == "nested":
            sim = sim.get_branch("nested")
    sim.set_input("input_amount", 2026, [20])
    if delete_through == "simulation":
        sim.delete_arrays("input_amount", 2026)
    else:
        sim.get_holder("input_amount").delete_arrays(period_(2026), sim.branch_name)
    assert sim.calculate("input_amount", 2026).tolist() == [10]
    population = sim.get_variable_population("input_amount")
    assert supplied_input(population, "input_amount", period_(2026)) is None
    assert supplied_input_periods(population, "input_amount") == [period_(2025)]


@pytest.mark.parametrize("make_copy", ["clone", "branch"])
@pytest.mark.parametrize("action", ["replace", "delete", "clear"])
def test_owner_operations_preserve_existing_snapshots(simulation, make_copy, action):
    snapshot = (
        simulation.clone() if make_copy == "clone" else simulation.get_branch("copy")
    )
    assert snapshot.calculate("doubled_amount", 2025).tolist() == [20]
    if action == "replace":
        simulation.set_input("input_amount", 2025, [30])
    elif action == "delete":
        simulation.delete_arrays("input_amount", 2025)
    else:
        simulation.reset_calculations()
    assert snapshot.calculate("doubled_amount", 2025).tolist() == [20]
    assert snapshot.get_supplied_input("input_amount", 2025).tolist() == [10]


def test_reset_clears_carried_periods_but_preserves_explicit_periods(simulation):
    simulation.calculate("input_amount", 2026)
    simulation.calculate("doubled_amount", 2025)
    simulation.reset_calculations()
    assert simulation.get_array("input_amount", 2026) is None
    assert simulation.get_array("doubled_amount", 2025) is None
    assert simulation.get_supplied_input("input_amount", 2025).tolist() == [10]


def test_reset_preserves_inputs_added_after_construction(simulation):
    simulation.set_input("doubled_amount", 2026, [99])
    simulation.reset_calculations()
    assert simulation.get_supplied_input("doubled_amount", 2026).tolist() == [99]


def test_neutralized_input_keeps_uk_effective_value_semantics(simulation):
    simulation.tax_benefit_system.neutralize_variable("input_amount")
    population = simulation.get_variable_population("input_amount")
    assert supplied_input(population, "input_amount", period_(2025)).tolist() == [0]
    assert simulation.get_supplied_input("input_amount", 2025).tolist() == [10]


def test_country_helpers_return_immutable_values(simulation):
    population = simulation.get_variable_population("input_amount")
    value = supplied_input(population, "input_amount", period_(2025))
    with pytest.raises(ValueError):
        value[0] = 99
    assert np.array_equal(value, [10])


def test_cold_parameter_processing_runs_once_and_warm_instances_clone(
    monkeypatch, tiny_uk_system
):
    monkeypatch.setattr(system_module, "_processed_parameters_cache", None)
    calls = []

    def reset(system):
        calls.append("reset")
        system.replace_parameters(tiny_uk_system.clone())

    def process(system):
        calls.append("process")
        system.parameters.amount.update(period="2025", value=15)

    monkeypatch.setattr(
        system_module.CountryTaxBenefitSystem, "reset_parameters", reset
    )
    monkeypatch.setattr(
        system_module.CountryTaxBenefitSystem, "process_parameters", process
    )
    cold = system_module.CountryTaxBenefitSystem()
    warm = system_module.CountryTaxBenefitSystem()
    assert calls == ["reset", "process"]
    assert cold.get_parameters_at_instant("2025").amount == 15
    assert warm.get_parameters_at_instant("2025").amount == 15
    cold.parameters.amount.update(period="2025", value=99)
    assert warm.get_parameters_at_instant("2025").amount == 15
    assert system_module._processed_parameters_cache("2025").amount == 15


def test_parameter_pipeline_installs_the_final_transformed_root(
    monkeypatch, tiny_uk_system
):
    system = system_module.CountryTaxBenefitSystem()
    system.replace_parameters(
        ParameterNode("", data={"gov": {"amount": {"values": {"2025-01-01": 10}}}})
    )
    stages = [
        "add_private_pension_uprating_factor",
        "add_lagged_earnings",
        "add_lagged_cpi",
        "add_statutory_uprating_inputs",
        "add_triple_lock",
        "create_economic_assumption_indices",
        "add_lsr_deprecation_aliases",
        "propagate_parameter_metadata",
        "uprate_parameters",
        "backdate_parameters",
    ]
    calls = []

    def step(name):
        def transform(tree, *args):
            calls.append(name)
            # A processor may replace the root, rather than mutate it.
            return tree.clone()

        return transform

    for name in stages:
        monkeypatch.setattr(system_module, name, step(name))
    monkeypatch.setattr(
        system_module, "convert_to_fiscal_year_parameters", step("fiscal_year")
    )
    installed = []
    original = system.replace_parameters

    def install(tree):
        installed.append(tree)
        original(tree)

    monkeypatch.setattr(system, "replace_parameters", install)
    system.process_parameters()
    assert calls == [*stages, "fiscal_year"]
    assert installed == [system.parameters]
    assert system.parameters.baseline is not system.parameters


def test_reset_parameters_installs_alias_transform_result(monkeypatch, tiny_uk_system):
    system = system_module.CountryTaxBenefitSystem()
    replacement = ParameterNode("", data={"amount": {"values": {"2025-01-01": 50}}})
    monkeypatch.setattr(system, "load_parameters", lambda path: None)
    monkeypatch.setattr(
        system_module, "add_removed_parameter_aliases", lambda root: replacement
    )
    installed = []
    original = system.replace_parameters

    def install(tree):
        installed.append(tree)
        original(tree)

    monkeypatch.setattr(system, "replace_parameters", install)
    system.get_parameters_at_instant("2025")
    system.reset_parameters()
    assert installed == [replacement]
    assert system.get_parameters_at_instant("2025").amount == 50


def test_parameter_changes_clear_results_without_discarding_supplied_values(
    simulation, monkeypatch
):
    system = simulation.tax_benefit_system
    system.replace_parameters(
        ParameterNode("", data={"amount": {"values": {"2025-01-01": 10}}})
    )
    monkeypatch.setattr(system, "reset_parameters", lambda: None, raising=False)
    monkeypatch.setattr(system, "process_parameters", lambda: None, raising=False)
    simulation.calculate("doubled_amount", 2025)
    snapshot = simulation.get_branch("snapshot", clone_system=True)
    simulation.apply_parameter_changes({"amount": {2025: 20}})
    assert simulation.get_array("doubled_amount", 2025) is None
    assert simulation.get_supplied_input("input_amount", 2025).tolist() == [10]
    assert snapshot.get_array("doubled_amount", 2025).tolist() == [20]


def test_moving_inputs_does_not_promote_carried_values(simulation):
    simulation.calculate("input_amount", 2026)
    simulation.move_values("input_amount", "doubled_amount")
    assert simulation.supplied_input_periods("input_amount") == []
    assert simulation.supplied_input_periods("doubled_amount") == [period_(2025)]
    assert simulation.get_supplied_input("doubled_amount", 2025).tolist() == [10]


def test_moving_inputs_uses_each_explicit_branch_value(simulation):
    child = simulation.get_branch("child")
    child.set_input("input_amount", 2025, [30])
    simulation.move_values("input_amount", "doubled_amount")
    assert simulation.get_supplied_input("doubled_amount", 2025).tolist() == [10]
    assert child.get_supplied_input("doubled_amount", 2025).tolist() == [30]
    for sim in [simulation, child]:
        assert sim.supplied_input_periods("input_amount") == []


def test_moving_an_input_leaves_an_unlisted_clone_unchanged(simulation):
    clone = simulation.clone()
    simulation.move_values("input_amount", "doubled_amount")
    assert clone.get_supplied_input("input_amount", 2025).tolist() == [10]
    assert clone.supplied_input_periods("doubled_amount") == []


@pytest.mark.parametrize(
    "donor, target",
    [
        ("capital_gains", "capital_gains_before_response"),
        ("employment_income", "employment_income_before_lsr"),
        ("employee_pension_contributions", "employee_pension_contributions_reported"),
        ("bus_fare_spending", "bus_fare_spending_reported"),
    ],
)
@pytest.mark.parametrize("explicit_donor", [False, True])
def test_constructor_input_routes_do_not_reapply_derived_responses(
    donor, target, explicit_donor
):
    """Synthetic response formula models the donor reading its own target."""
    system = TaxBenefitSystem([TestPerson])
    system.replace_parameters(ParameterNode("", data={}))
    attributes = {
        "entity": TestPerson,
        "value_type": float,
        "definition_period": YEAR,
        "label": "Fixture reported value",
    }
    system.add_variable(type(target, (Variable,), dict(attributes)))

    def response_formula(person, period):
        return person(target, period) * 2

    system.add_variable(
        type(donor, (Variable,), {**attributes, "formula": response_formula})
    )
    sim = Simulation.__new__(Simulation)
    inputs = {target: {2025: 10}}
    if explicit_donor:
        inputs[donor] = {2025: 30}
    CoreSimulation.__init__(sim, tax_benefit_system=system, situation=inputs)
    assert sim.calculate(donor, 2025).tolist() == [30 if explicit_donor else 20]
    sim.move_values(donor, target)
    assert sim.get_supplied_input(target, 2025).tolist() == [
        30 if explicit_donor else 10
    ]
    assert sim.supplied_input_periods(donor) == []


@pytest.mark.parametrize("branch_name", [None, "child"])
def test_holder_input_writes_use_core_provenance_without_country_registration(
    simulation, branch_name
):
    sim = simulation.get_branch(branch_name) if branch_name else simulation
    sim.get_holder("input_amount").set_input(period_(2026), [45], sim.branch_name)
    population = sim.get_variable_population("input_amount")
    assert supplied_input(population, "input_amount", period_(2026)).tolist() == [45]
    assert supplied_input_periods(population, "input_amount") == [
        period_(2025),
        period_(2026),
    ]


def test_scenario_structural_reform_uses_simulation_ownership_api(
    simulation, monkeypatch
):
    from policyengine_uk.utils.scenario import _apply_reform_class

    reform = object()
    apply = Mock()
    clear_parameters = Mock()
    monkeypatch.setattr(simulation, "apply_reform", apply)
    monkeypatch.setattr(
        simulation.tax_benefit_system, "clear_parameter_caches", clear_parameters
    )
    _apply_reform_class(reform, simulation)
    apply.assert_called_once_with(reform)
    clear_parameters.assert_called_once_with()
