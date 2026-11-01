"""Saved policies naming the Marriage Allowance eligible bands get directions.

The model applies the rate conditions of ITA 2007 s. 55B(2)(b) and (ba) to
income directly, so nothing reads
``gov.hmrc.income_tax.allowances.marriage_allowance.eligible_bands`` (#2350).
"""

import pytest
from policyengine_core.reforms import Reform

from policyengine_uk import Simulation
from policyengine_uk.system import system
from policyengine_uk.utils.parameters import RemovedParameterNode
from policyengine_uk.utils.scenario import Scenario

REMOVED = "gov.hmrc.income_tax.allowances.marriage_allowance.eligible_bands"
SITUATION = {"people": {"person": {"age": {2025: 40}}}}
# The parameter held a list of band names, as a saved policy would.
SAVED = {REMOVED: {"2025": ["NONE", "STARTER", "BASIC"]}}


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


@pytest.mark.parametrize("entry_point", ["core_reform", "scenario_reform"])
def test_removed_eligible_bands_give_directions(baseline, entry_point):
    simulation = baseline.clone()
    with pytest.raises(ValueError) as error:
        if entry_point == "core_reform":
            Reform.from_dict(SAVED)(simulation.tax_benefit_system)
        else:
            Scenario.from_reform(SAVED).apply(simulation)
    message = str(error.value)
    assert f"{REMOVED} has been removed" in message
    assert "s. 55B(2)(b)" in message
    assert "gov.hmrc.income_tax.rates.uk[1].threshold" in message
    assert "gov.hmrc.income_tax.rates.scotland.rates[3].threshold" in message


def test_removed_eligible_bands_stay_discoverable(baseline):
    marriage_allowance = baseline.tax_benefit_system.parameters.gov.hmrc.income_tax.allowances.marriage_allowance
    alias = marriage_allowance.children["eligible_bands"]
    assert isinstance(alias, RemovedParameterNode)
    assert alias.metadata["removed"] is True
    assert "s. 55B(2)(b)" in alias.description
