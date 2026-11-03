"""Saved couple carer-premium policies fail with per-person migration help."""

import pytest
from policyengine_core.reforms import Reform

from policyengine_uk import Simulation
from policyengine_uk.system import system
from policyengine_uk.utils.parameters import RemovedParameterNode
from policyengine_uk.utils.scenario import Scenario

REMOVED = "gov.dwp.carer_premium.couple"
REPLACEMENT = "gov.dwp.carer_premium.single"
SITUATION = {"people": {"person": {"age": {2026: 40}}}}


@pytest.fixture(scope="module", autouse=True)
def reuse_country_model():
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(
            "policyengine_uk.simulation.CountryTaxBenefitSystem", system.clone
        )
        yield


@pytest.fixture(scope="module")
def baseline():
    return Simulation(situation=SITUATION)


@pytest.fixture
def simulation(baseline):
    return baseline.clone()


@pytest.mark.parametrize(
    "entry_point",
    ["core_reform", "scenario_reform", "scenario_scalar", "scenario_saved_periods"],
)
def test_removed_carer_premium_reforms_give_migration_directions(
    simulation, entry_point
):
    changes = {REMOVED: {"2026": 99}}
    parameters = simulation.tax_benefit_system.parameters
    original = parameters.get_child(REPLACEMENT)(2026)

    with pytest.raises(ValueError) as error:
        if entry_point == "core_reform":
            Reform.from_dict(changes)(simulation.tax_benefit_system)
        elif entry_point == "scenario_reform":
            Scenario.from_reform(changes).apply(simulation)
        elif entry_point == "scenario_scalar":
            Scenario(parameter_changes={REMOVED: 99}).apply(simulation)
        else:
            Scenario(parameter_changes=changes).apply(simulation)

    message = str(error.value)
    assert f"{REMOVED} has been removed" in message
    assert REPLACEMENT in message
    assert "per qualifying claimant or partner" in message
    assert "per-person" in message
    assert parameters.get_child(REPLACEMENT)(2026) == original


def test_removed_carer_premium_alias_uses_its_own_parent(baseline):
    parameters = baseline.tax_benefit_system.parameters
    premium = parameters.gov.dwp.carer_premium
    alias = premium.children["couple"]

    assert isinstance(alias, RemovedParameterNode)
    assert alias.parent is premium
    assert alias.metadata["removed"] is True
    assert alias.metadata["household"] is False
    assert alias.metadata["economy"] is False
    assert REPLACEMENT in alias.description
    assert "couple" not in parameters.gov.dwp.state_pension.age.children
    with pytest.raises(ValueError, match="per-person"):
        alias.update(period="2026", value=99)


def test_per_person_carer_premium_remains_reformable(simulation):
    Scenario(parameter_changes={REPLACEMENT: 99}).apply(simulation)

    assert simulation.tax_benefit_system.parameters.get_child(REPLACEMENT)(2026) == 99
