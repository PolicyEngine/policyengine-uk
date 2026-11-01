"""Saved policies naming the Marriage Allowance eligible bands get directions.

The income conditions apply the rate conditions of ITA 2007 s. 55B(2)(b) and
(ba) directly, so nothing reads
``gov.hmrc.income_tax.allowances.marriage_allowance.eligible_bands`` (#2350).
"""

import pytest

from policyengine_uk import Simulation
from policyengine_uk.system import system
from policyengine_uk.utils.scenario import Scenario

REMOVED = "gov.hmrc.income_tax.allowances.marriage_allowance.eligible_bands"


@pytest.fixture(scope="module", autouse=True)
def reuse_country_model():
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(
            "policyengine_uk.simulation.CountryTaxBenefitSystem", system.clone
        )
        yield


def test_removed_eligible_bands_give_directions():
    with pytest.raises(ValueError) as error:
        Simulation(
            situation={"people": {"person": {"age": {2025: 40}}}},
            scenario=Scenario(parameter_changes={REMOVED: {"2025": ["BASIC"]}}),
        )
    message = str(error.value)
    assert f"{REMOVED} has been removed" in message
    assert "s. 55B(2)(b)" in message
    assert "gov.hmrc.income_tax.rates.uk[1].threshold" in message
    assert "gov.hmrc.income_tax.rates.scotland.rates[3].threshold" in message
