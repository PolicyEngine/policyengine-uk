"""The removed OBR elasticities switch gives directions at every reform entry.

``gov.simulation.labour_supply_responses.obr_elasticities`` was removed because
nothing read it (#2412). A reform or saved policy that still names it, under
the current path or the legacy ``labor_supply_responses`` one, fails with a
message pointing to ``gov.dynamic.obr_labour_supply_assumptions`` rather than
a bare lookup error.
"""

import copy
from types import SimpleNamespace

import pytest
from policyengine_core.parameters import ParameterNode, get_parameter
from policyengine_core.reforms import Reform, set_parameter

from policyengine_uk import Simulation
from policyengine_uk.system import system
from policyengine_uk.utils.parameters import RemovedParameterNode
from policyengine_uk.utils.scenario import Scenario

CANONICAL = "gov.simulation.labour_supply_responses.obr_elasticities"
LEGACY = "gov.simulation.labor_supply_responses.obr_elasticities"
REMOVED_PATHS = [CANONICAL, LEGACY]
SITUATION = {
    "people": {"person": {"age": 30, "employment_income": 25_000}},
    "benunits": {"benunit": {"members": ["person"]}},
    "households": {"household": {"members": ["person"]}},
}


@pytest.fixture(scope="module", autouse=True)
def reuse_country_model():
    # Build each simulation's system by cloning the loaded one rather than
    # loading the whole country model for every case.
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(
            "policyengine_uk.simulation.CountryTaxBenefitSystem", system.clone
        )
        yield


@pytest.fixture(scope="module")
def baseline_simulation():
    return Simulation(situation=SITUATION)


@pytest.fixture
def simulation(baseline_simulation):
    return baseline_simulation.clone()


def assert_directions(message: str) -> None:
    assert "supply_responses.obr_elasticities has been removed" in message
    assert "Nothing read it" in message
    assert "gov.dynamic.obr_labour_supply_assumptions" in message


ENTRY_POINTS = [
    "parameter_lookup",
    "simulation_parameter_changes",
    "scenario_dict_modifier",
    "scenario_apply_scalar",
    "scenario_apply_periods",
    "simulation_apply_dict",
    "system_apply_dict",
    "system_modify_dict",
    "core_reform_dict",
    "core_set_parameter",
    "core_reform_api",
    "api_parameter_normalization",
    "api_legacy_policy_normalization",
]


@pytest.mark.parametrize("path", REMOVED_PATHS)
@pytest.mark.parametrize("entry_point", ENTRY_POINTS)
def test_removed_switch_entry_points_give_directions(
    simulation, monkeypatch, path, entry_point
):
    changes = {path: {"2025": 1}}
    tax_benefit_system = simulation.tax_benefit_system

    with pytest.raises(ValueError) as error:
        if entry_point == "parameter_lookup":
            tax_benefit_system.parameters.get_child(path)
        elif entry_point == "simulation_parameter_changes":
            simulation.apply_parameter_changes(changes)
        elif entry_point == "scenario_dict_modifier":
            Scenario.from_reform(changes).simulation_modifier(simulation)
        elif entry_point == "scenario_apply_scalar":
            Scenario(parameter_changes={path: 1}).apply(simulation)
        elif entry_point == "scenario_apply_periods":
            Scenario(parameter_changes=changes).apply(simulation)
        elif entry_point == "simulation_apply_dict":
            simulation.apply_reform(changes)
        elif entry_point == "system_apply_dict":
            tax_benefit_system.apply_reform_set(changes)
        elif entry_point == "system_modify_dict":
            tax_benefit_system.modify_parameters(changes)
        elif entry_point == "core_reform_dict":
            Reform.from_dict(changes)(tax_benefit_system)
        elif entry_point == "core_set_parameter":
            set_parameter(path, 1, period="2025")(tax_benefit_system)
        elif entry_point == "core_reform_api":
            response = SimpleNamespace(
                json=lambda: {
                    "result": {
                        "policy_json": {path: {"2025-01-01.2025-12-31": 1}},
                        "label": "saved OBR elasticities reform",
                    }
                }
            )
            monkeypatch.setattr(
                "policyengine_core.reforms.reform.requests.get",
                lambda *a, **k: response,
            )
            Reform.from_api("obr-elasticities", country_id="uk")(tax_benefit_system)
        elif entry_point == "api_parameter_normalization":
            # policyengine-api reads the final value to infer a type before it
            # calls Parameter.update.
            get_parameter(tax_benefit_system.parameters, path).values_list[-1].value
        elif entry_point == "api_legacy_policy_normalization":
            # It also walks the children, then reads values_list.
            node = tax_benefit_system.parameters
            for part in path.split("."):
                node = node.children[part]
            node.values_list[-1].value
        else:
            raise AssertionError(f"Unknown entry point: {entry_point}")

    assert_directions(str(error.value))


@pytest.mark.parametrize("path", REMOVED_PATHS)
@pytest.mark.parametrize("entry_point", ["reform_dict", "scenario"])
def test_simulation_constructor_rejects_removed_switch(path, entry_point):
    changes = {path: {"2025": 1}}
    if entry_point == "reform_dict":
        kwargs = {"reform": changes}
    else:
        kwargs = {"scenario": Scenario(parameter_changes=changes)}

    with pytest.raises(ValueError) as error:
        Simulation(situation=SITUATION, **kwargs)
    assert_directions(str(error.value))


@pytest.mark.parametrize("path", REMOVED_PATHS)
@pytest.mark.parametrize("clone_method", ["clone", "deepcopy"])
def test_removed_switch_stub_is_hidden_and_survives_copies(
    baseline_simulation, path, clone_method
):
    original = baseline_simulation.tax_benefit_system.parameters
    parameters = (
        original.clone() if clone_method == "clone" else copy.deepcopy(original)
    )
    stub = parameters
    for part in path.split("."):
        stub = stub.children[part]
    assert isinstance(stub, RemovedParameterNode)
    assert isinstance(stub, ParameterNode)
    assert not stub.children
    assert stub.metadata["removed"] is True
    assert stub.metadata["economy"] is False
    assert stub.metadata["household"] is False
    assert stub.metadata["label"] == "removed OBR elasticities switch"
    assert_directions(stub.description)
    with pytest.raises(ValueError) as error:
        parameters.get_child(path)
    assert_directions(str(error.value))
    with pytest.raises(ValueError) as error:
        stub.update(period="2025", value=1)
    assert_directions(str(error.value))


@pytest.mark.parametrize(
    "path",
    [
        "gov.simulation.labour_supply_responses.income_elasticity",
        "gov.simulation.labor_supply_responses.income_elasticity",
    ],
)
def test_neighbouring_labour_supply_parameters_can_still_be_reformed(simulation, path):
    simulation.apply_parameter_changes({path: {"2025": -0.05}})
    lsr = simulation.tax_benefit_system.parameters.gov.simulation
    assert lsr.labour_supply_responses.income_elasticity("2025") == -0.05
