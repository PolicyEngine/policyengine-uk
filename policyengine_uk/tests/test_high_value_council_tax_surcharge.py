import pytest

from policyengine_uk import Simulation
from policyengine_uk.variables.gov.gov_tax import gov_tax
from policyengine_uk.variables.gov.hmrc.household_tax import household_tax


def _homeowner(main_residence_value: float, region: str = "LONDON") -> dict:
    return {
        "people": {
            "person": {
                "age": {2026: 45, 2028: 47, 2029: 48},
                "employment_income": {2028: 0, 2029: 0},
            }
        },
        "benunits": {"benunit": {"members": ["person"]}},
        "households": {
            "household": {
                "members": ["person"],
                "region": {2028: region, 2029: region},
                "main_residence_value": {2026: main_residence_value},
            }
        },
    }


def test_high_value_council_tax_surcharge_starts_in_2028():
    sim = Simulation(situation=_homeowner(2_400_000))

    assert sim.calculate("high_value_council_tax_surcharge", 2027)[0] == 0
    assert sim.calculate("high_value_council_tax_surcharge", 2028)[0] == 2_500


def test_high_value_council_tax_surcharge_is_uprated_from_2029():
    sim = Simulation(situation=_homeowner(2_400_000))
    current = sim.tax_benefit_system.parameters("2029")
    previous = sim.tax_benefit_system.parameters("2028")
    expected_2029 = (
        2_500
        * float(current.gov.benefit_uprating_cpi)
        / float(previous.gov.benefit_uprating_cpi)
    )

    assert sim.calculate("high_value_council_tax_surcharge", 2029)[0] == pytest.approx(
        expected_2029
    )


def test_high_value_council_tax_surcharge_flows_into_tax_aggregates():
    sim = Simulation(situation=_homeowner(2_400_000))

    other_household_taxes = sum(
        sim.calculate(variable, 2028)[0]
        for variable in household_tax.adds
        if variable != "high_value_council_tax_surcharge"
    )
    other_government_taxes = sum(
        sim.calculate(variable, 2028)[0]
        for variable in gov_tax.adds
        if variable != "high_value_council_tax_surcharge"
    )

    assert sim.calculate("household_tax", 2028)[0] - other_household_taxes == 2_500
    assert sim.calculate("gov_tax", 2028)[0] - other_government_taxes == 2_500


def test_high_value_council_tax_surcharge_only_applies_in_england():
    sim = Simulation(situation=_homeowner(6_000_000, region="SCOTLAND"))

    assert sim.calculate("high_value_council_tax_surcharge", 2028)[0] == 0
