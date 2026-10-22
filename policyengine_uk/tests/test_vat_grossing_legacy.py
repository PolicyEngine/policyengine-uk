import pytest
from policyengine_core.reforms import Reform

from policyengine_uk import Simulation
from policyengine_uk.model_api import Scenario
from policyengine_uk.system import system
from policyengine_uk.utils.vat import LEGACY_COVERAGE_DEFAULT

LEGACY = "gov.simulation.microdata_vat_coverage"
SITUATION = {
    "people": {"adult": {"age": {2025: 40}}},
    "benunits": {"benunit": {"members": ["adult"]}},
    "households": {
        "household": {
            "members": ["adult"],
            "full_rate_vat_consumption": {2025: 10_000},
            "reduced_rate_vat_consumption": {2025: 1_000},
        }
    },
}
RAW_VAT = 10_000 * 0.2 + 1_000 * 0.05


def test_legacy_default_is_the_product_of_the_two_factors():
    p = system.parameters.gov.simulation
    for year in range(2015, 2031):
        product = p.vat.survey_consumption_coverage(
            year
        ) * p.vat.household_share_of_receipts(year)
        assert p.microdata_vat_coverage(year) == pytest.approx(product)
    assert LEGACY_COVERAGE_DEFAULT == pytest.approx(0.469)


def test_reform_dict_to_legacy_path_changes_vat():
    reform = Reform.from_dict({LEGACY: {"2010-01-01.2100-12-31": 0.5}}, "uk")
    sim = Simulation(situation=SITUATION, reform=reform)
    assert sim.calculate("vat", 2025)[0] == pytest.approx(RAW_VAT / 0.5)


def test_scenario_to_legacy_path_changes_vat():
    scenario = Scenario(parameter_changes={LEGACY: {"year:2025:1": 0.5}})
    sim = Simulation(situation=SITUATION, scenario=scenario)
    assert sim.calculate("vat", 2025)[0] == pytest.approx(RAW_VAT / 0.5)


def test_untouched_legacy_path_uses_the_two_factors():
    reform = Reform.from_dict(
        {
            "gov.simulation.vat.survey_consumption_coverage": {
                "2010-01-01.2100-12-31": 1
            }
        },
        "uk",
    )
    sim = Simulation(situation=SITUATION, reform=reform)
    assert sim.calculate("vat", 2025)[0] == pytest.approx(RAW_VAT / 0.7)
