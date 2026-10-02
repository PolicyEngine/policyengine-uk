"""Obsolete State Pension age paths give migration help at every reform entry."""

import copy
import sys
from types import SimpleNamespace

import pytest
from policyengine_core.parameters import ParameterNode, get_parameter
from policyengine_core.reforms import Reform, set_parameter

from policyengine_uk import Simulation
from policyengine_uk.system import system
from policyengine_uk.utils.parameters import RemovedParameterNode
from policyengine_uk.utils.scenario import Scenario


AGE_PREFIX = "gov.dwp.state_pension.age"
REMOVED_PATHS = [f"{AGE_PREFIX}.male", f"{AGE_PREFIX}.female"]
REPLACEMENT_PATH = f"{AGE_PREFIX}.age_by_birth_date[14].amount"
SITUATION = {
    "people": {"person": {"age": {"2028": 66}}},
    "benunits": {"benunit": {"members": ["person"]}},
    "households": {"household": {"members": ["person"]}},
}


@pytest.fixture(scope="module", autouse=True)
def reuse_country_model():
    # Exercise the real constructor and reform paths with an independent
    # parameter tree, without importing all model variables for every case.
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
    # Each case has an independent parameter tree without rebuilding entities
    # and loading the whole country model for every entry point.
    return baseline_simulation.clone()


def structural_reform(path, access="get_child", use_modifier=False):
    def modifier(parameters):
        if access == "attribute":
            target = getattr(
                parameters.gov.dwp.state_pension.age, path.rsplit(".", 1)[1]
            )
        elif access == "children":
            target = parameters.gov.dwp.state_pension.age.children[
                path.rsplit(".", 1)[1]
            ]
        else:
            target = parameters.get_child(path)
        target.update(period="2028", value=780)
        return parameters

    class ChangeAge(Reform):
        def apply(self):
            if use_modifier:
                self.modify_parameters(modifier)
            else:
                modifier(self.parameters)

    return ChangeAge


ENTRY_POINTS = [
    "parameter_lookup",
    "simulation_parameter_changes",
    "scenario_dict_modifier",
    "scenario_apply_scalar",
    "scenario_apply_periods",
    "scenario_apply_nested",
    "scenario_structural_class",
    "scenario_structural_tuple",
    "simulation_apply_dict",
    "simulation_apply_class",
    "simulation_apply_tuple",
    "system_apply_dict",
    "system_apply_class",
    "system_apply_tuple",
    "system_modify_dict",
    "system_modify_callback",
    "core_reform_dict",
    "structural_attribute",
    "structural_children",
    "structural_modifier",
    "core_set_parameter",
    "core_set_parameter_modifier",
    "system_imported_reform",
    "core_reform_api",
    "api_parameter_normalization",
    "api_legacy_policy_normalization",
]


@pytest.mark.parametrize("path", REMOVED_PATHS)
@pytest.mark.parametrize("entry_point", ENTRY_POINTS)
def test_removed_parameter_entry_points_name_the_replacement(
    simulation, monkeypatch, path, entry_point
):
    changes = {path: {"2028": 67}}
    system = simulation.tax_benefit_system
    reform = structural_reform(path)

    with pytest.raises(ValueError) as error:
        if entry_point == "parameter_lookup":
            system.parameters.get_child(path)
        elif entry_point == "simulation_parameter_changes":
            simulation.apply_parameter_changes(changes)
        elif entry_point == "scenario_dict_modifier":
            Scenario.from_reform(changes).simulation_modifier(simulation)
        elif entry_point == "scenario_apply_scalar":
            Scenario(parameter_changes={path: 67}).apply(simulation)
        elif entry_point == "scenario_apply_periods":
            Scenario(parameter_changes=changes).apply(simulation)
        elif entry_point == "scenario_apply_nested":
            Scenario(
                parameter_changes={AGE_PREFIX: {path.rsplit(".", 1)[1]: 67}}
            ).apply(simulation)
        elif entry_point == "scenario_structural_class":
            Scenario.from_reform(reform).apply(simulation)
        elif entry_point == "scenario_structural_tuple":
            Scenario.from_reform((reform,)).apply(simulation)
        elif entry_point == "simulation_apply_dict":
            simulation.apply_reform(changes)
        elif entry_point == "simulation_apply_class":
            simulation.apply_reform(reform)
        elif entry_point == "simulation_apply_tuple":
            simulation.apply_reform((reform,))
        elif entry_point == "system_apply_dict":
            system.apply_reform_set(changes)
        elif entry_point == "system_apply_class":
            system.apply_reform_set(reform)
        elif entry_point == "system_apply_tuple":
            system.apply_reform_set((reform,))
        elif entry_point == "system_modify_dict":
            system.modify_parameters(changes)
        elif entry_point == "system_modify_callback":
            system.modify_parameters(
                set_parameter(path, 67, period="2028", return_modifier=True)
            )
        elif entry_point == "core_reform_dict":
            Reform.from_dict(changes)(system)
        elif entry_point == "structural_attribute":
            structural_reform(path, access="attribute")(system)
        elif entry_point == "structural_children":
            structural_reform(path, access="children")(system)
        elif entry_point == "structural_modifier":
            structural_reform(path, use_modifier=True)(system)
        elif entry_point == "core_set_parameter":
            set_parameter(path, 67, period="2028")(system)
        elif entry_point == "core_set_parameter_modifier":
            set_parameter(path, 67, period="2028", return_modifier=True)(
                system.parameters
            )
        elif entry_point == "system_imported_reform":
            monkeypatch.setattr(
                sys.modules[__name__], "ImportedReform", reform, raising=False
            )
            system.apply_reform(f"{__name__}.ImportedReform")
        elif entry_point == "core_reform_api":
            response = SimpleNamespace(
                json=lambda: {
                    "result": {
                        "policy_json": {path: {"2028-01-01.2028-12-31": 67}},
                        "label": "saved obsolete age reform",
                    }
                }
            )
            monkeypatch.setattr(
                "policyengine_core.reforms.reform.requests.get",
                lambda *a, **k: response,
            )
            Reform.from_api("obsolete-age", country_id="uk")(system)
        elif entry_point == "api_parameter_normalization":
            # policyengine-api/country.py::_normalize_reform_values reads the
            # final value to infer a type before it calls Parameter.update.
            get_parameter(system.parameters, path).values_list[-1].value
        elif entry_point == "api_legacy_policy_normalization":
            # The same repository's create_policy_reform walks children first,
            # then reads values_list before applying its parameter update.
            node = system.parameters
            for part in path.split("."):
                node = node.children[part]
            node.values_list[-1].value
        else:
            raise AssertionError(f"Unknown entry point: {entry_point}")

    message = str(error.value)
    assert path in message
    assert "has been removed" in message
    assert "age_by_birth_date" in message
    assert "day_by_birth_date" in message
    assert "state_pension_age" in message


@pytest.mark.parametrize("path", REMOVED_PATHS)
def test_removed_parameter_rejection_preserves_existing_policy(simulation, path):
    parameters = simulation.tax_benefit_system.parameters
    parameters.get_child(REPLACEMENT_PATH).update(period="2028", value=780)
    with pytest.raises(ValueError, match="age_by_birth_date"):
        simulation.apply_parameter_changes({path: {"2028": 67}})
    assert simulation.tax_benefit_system.parameters is parameters
    assert parameters.get_child(REPLACEMENT_PATH)("2028") == 780


@pytest.mark.parametrize("path", REMOVED_PATHS)
@pytest.mark.parametrize(
    "entry_point",
    [
        "reform_dict",
        "scenario",
        "scenario_before_data",
        "structural_class",
        "structural_tuple",
    ],
)
def test_simulation_constructor_rejects_removed_parameters(path, entry_point):
    changes = {path: {"2028": 67}}
    if entry_point == "reform_dict":
        kwargs = {"reform": changes}
    elif entry_point in ("scenario", "scenario_before_data"):
        kwargs = {
            "scenario": Scenario(
                parameter_changes=changes,
                applied_before_data_load=entry_point == "scenario_before_data",
            )
        }
    else:
        reform = structural_reform(path)
        kwargs = {"reform": (reform,) if entry_point == "structural_tuple" else reform}

    with pytest.raises(ValueError, match="age_by_birth_date") as error:
        Simulation(situation=SITUATION, **kwargs)
    assert path in str(error.value)


@pytest.mark.parametrize(
    "entry_point",
    [
        "reform_dict",
        "scenario_parameter_changes",
        "scenario_apply",
        "structural_class",
        "structural_tuple",
        "core_set_parameter",
    ],
)
def test_replacement_parameter_can_still_be_reformed(simulation, entry_point):
    changes = {REPLACEMENT_PATH: {"2028": 780}}
    if entry_point == "reform_dict":
        Scenario.from_reform(changes).apply(simulation)
    elif entry_point == "scenario_parameter_changes":
        simulation.apply_parameter_changes(changes)
    elif entry_point == "scenario_apply":
        Scenario(parameter_changes={REPLACEMENT_PATH: 780}).apply(simulation)
    elif entry_point in ("structural_class", "structural_tuple"):
        reform = structural_reform(REPLACEMENT_PATH)
        Scenario.from_reform(
            (reform,) if entry_point == "structural_tuple" else reform
        ).apply(simulation)
    else:
        simulation.tax_benefit_system = set_parameter(
            REPLACEMENT_PATH, 780, period="2028"
        )(simulation.tax_benefit_system)

    assert (
        simulation.tax_benefit_system.parameters.get_child(REPLACEMENT_PATH)("2028")
        == 780
    )
    assert simulation.calculate("state_pension_age", 2028)[0] == 65
    assert simulation.calculate("is_SP_age", 2028)[0]


def test_structural_tuple_passes_constructor_arguments(simulation):
    class ParameterizedAgeReform(Reform):
        def __init__(self, baseline, months):
            self.months = months
            super().__init__(baseline)

        def apply(self):
            self.parameters.get_child(REPLACEMENT_PATH).update(
                period="2028", value=self.months
            )

    Scenario.from_reform((ParameterizedAgeReform, 780)).apply(simulation)
    assert (
        simulation.tax_benefit_system.parameters.get_child(REPLACEMENT_PATH)("2028")
        == 780
    )


def test_nested_scenario_can_change_a_valid_child(simulation):
    Scenario(parameter_changes={f"{AGE_PREFIX}.male": {"age": 768}}).apply(simulation)
    assert (
        simulation.tax_benefit_system.parameters.gov.dwp.state_pension.age.male.age(
            "2028"
        )
        == 768
    )


@pytest.mark.parametrize("path", REMOVED_PATHS)
@pytest.mark.parametrize("clone_method", ["clone", "deepcopy"])
def test_removed_parameter_aliases_survive_parameter_tree_copies(
    baseline_simulation, path, clone_method
):
    original = baseline_simulation.tax_benefit_system.parameters
    original_male_age = original.gov.dwp.state_pension.age.male.age("2028")
    parameters = (
        original.clone() if clone_method == "clone" else copy.deepcopy(original)
    )
    alias = getattr(parameters.gov.dwp.state_pension.age, path.rsplit(".", 1)[1])
    assert isinstance(alias, RemovedParameterNode)
    assert isinstance(alias, ParameterNode)
    assert alias.metadata["removed"] is True
    assert alias.metadata["economy"] is False
    assert alias.metadata["household"] is False
    assert "age_by_birth_date" in alias.description
    with pytest.raises(ValueError, match="age_by_birth_date"):
        parameters.get_child(path)
    with pytest.raises(ValueError, match="age_by_birth_date"):
        alias.update(period="2028", value=67)

    # The valid male children retain their parents and remain reformable.
    male = parameters.gov.dwp.state_pension.age.male
    assert male.age.parent is male
    male.age.update(period="2028", value=768)
    assert male.age("2028") == 768
    assert original.gov.dwp.state_pension.age.male.age("2028") == original_male_age
