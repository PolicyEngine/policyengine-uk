"""Saved ESA higher earnings limit policies fail with directions to the wage."""

import pytest
from policyengine_core.reforms import Reform

from policyengine_uk import Simulation
from policyengine_uk.system import system
from policyengine_uk.utils.parameters import RemovedParameterNode
from policyengine_uk.utils.scenario import Scenario

REMOVED = "gov.dwp.ESA.exempt_work.higher_earnings_limit"
REPLACEMENTS = (
    "gov.hmrc.minimum_wage.non_apprentice",
    "gov.dwp.ESA.exempt_work.higher_earnings_limit_minimum_wage_hours",
    "gov.dwp.ESA.exempt_work.fixed_higher_earnings_limit",
)
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
def test_removed_esa_higher_earnings_limit_reforms_give_directions(
    simulation, entry_point
):
    changes = {REMOVED: {"2026": 250}}

    with pytest.raises(ValueError) as error:
        if entry_point == "core_reform":
            Reform.from_dict(changes)(simulation.tax_benefit_system)
        elif entry_point == "scenario_reform":
            Scenario.from_reform(changes).apply(simulation)
        elif entry_point == "scenario_scalar":
            Scenario(parameter_changes={REMOVED: 250}).apply(simulation)
        else:
            Scenario(parameter_changes=changes).apply(simulation)

    message = str(error.value)
    assert f"{REMOVED} has been removed" in message
    assert "esa_exempt_work_higher_earnings_limit" in message
    for replacement in REPLACEMENTS:
        assert replacement in message
    assert simulation.calculate("esa_exempt_work_higher_earnings_limit", 2026)[0] == (
        203.5
    )


def test_removed_esa_higher_earnings_limit_alias_uses_its_own_parent(baseline):
    exempt_work = baseline.tax_benefit_system.parameters.gov.dwp.ESA.exempt_work
    alias = exempt_work.children["higher_earnings_limit"]

    assert isinstance(alias, RemovedParameterNode)
    assert alias.parent is exempt_work
    assert alias.metadata["removed"] is True
    with pytest.raises(ValueError, match="national living wage"):
        alias.update(period="2026", value=250)


def test_minimum_wage_hours_remain_reformable(simulation):
    Scenario(parameter_changes={REPLACEMENTS[1]: 20}).apply(simulation)

    # 20 x £12.71 = £254.20, rounded up to £254.50.
    assert simulation.calculate("esa_exempt_work_higher_earnings_limit", 2026)[0] == (
        254.5
    )
