"""Annual-model history and rate overrides, not an academic-day allocation."""

from pathlib import Path

import pytest
from policyengine_core.parameters import ParameterNode

from policyengine_uk import CountryTaxBenefitSystem, Simulation
from policyengine_uk.utils.scenario import Scenario


pytestmark = pytest.mark.usefixtures("cloned_uk_tax_benefit_system")


def test_raw_amount_keeps_the_annual_model_history_anchors():
    directory = Path(__file__).parents[1] / "parameters/gov/dfe/care_to_learn"
    raw = ParameterNode(directory_path=str(directory)).amount
    # These are deliberately annual model anchors, not legal daily switches.
    for date in ("2015-01-01", "2023-12-31"):
        assert raw(date).in_london == 175
        assert raw(date).outside_london == 160
    for date in ("2024-01-01", "2026-04-30"):
        assert raw(date).in_london == 195
        assert raw(date).outside_london == 180


def test_processed_amount_keeps_old_and_current_annual_caps():
    parameters = CountryTaxBenefitSystem().parameters
    for year, london, elsewhere in (
        (2015, 175, 160),
        (2023, 175, 160),
        (2024, 195, 180),
        (2026, 195, 180),
    ):
        amount = parameters(str(year)).gov.dfe.care_to_learn.amount
        assert amount.in_london == london
        assert amount.outside_london == elsewhere


def test_historical_rate_override_reaches_final_household_benefits():
    situation = {
        "people": {
            "parent": {
                "age": {2015: 18},
                "is_parent": {2015: True},
                "current_education": {2015: "UPPER_SECONDARY"},
                "is_apprentice": {2015: False},
            },
            "child": {"age": {2015: 1}, "childcare_expenses": {2015: 12_000}},
        },
        "benunits": {"family": {"members": ["parent", "child"]}},
        "households": {
            "home": {
                "members": ["parent", "child"],
                "country": {2015: "ENGLAND"},
                "region": {2015: "EAST_OF_ENGLAND"},
            }
        },
    }
    baseline = Simulation(situation=situation)
    reformed = Simulation(
        situation=situation,
        scenario=Scenario(
            parameter_changes={
                "gov.dfe.care_to_learn.amount.outside_london": {2015: 200}
            }
        ),
    )
    # Model-contract arithmetic: 160 * 52 = 8320, 200 * 52 = 10400.
    assert baseline.calculate("care_to_learn", 2015).tolist() == [8_320, 0]
    assert reformed.calculate("care_to_learn", 2015).tolist() == [10_400, 0]
    difference = reformed.calculate("household_benefits", 2015) - baseline.calculate(
        "household_benefits", 2015
    )
    assert difference[0] == pytest.approx(2_080, abs=0.01)
