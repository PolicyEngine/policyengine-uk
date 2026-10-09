"""Statutory dates and reform compatibility for HB accommodation disregards."""

from datetime import date

import pytest

from policyengine_uk import CountryTaxBenefitSystem, Simulation
from policyengine_uk.model_api import Variable, BenUnit, YEAR


PREFIX = (
    "gov.dwp.housing_benefit.means_test.income_disregard."
    "specified_or_temporary_accommodation"
)


@pytest.fixture(scope="module")
def system():
    return CountryTaxBenefitSystem()


def node(parameters):
    return parameters.gov.dwp.housing_benefit.means_test.income_disregard.specified_or_temporary_accommodation


@pytest.mark.parametrize(
    "family,age,amount",
    [
        ("single", "younger", 61.41),
        ("single", "older", 77.73),
        ("lone_parent", "younger", 61.41),
        ("lone_parent", "older", 77.73),
        ("couple", "minors", 97.33),
        ("couple", "younger", 61.53),
        ("couple", "older", 119.70),
    ],
)
def test_processed_amounts_keep_5_october_commencement(system, family, age, amount):
    """GB SI 2026/753 and NI SR 2026/157 commence on 5 October, not January."""
    leaf = node(system.parameters).children[family].children[age]
    assert leaf("2026-10-04") == 0
    assert leaf("2026-10-05") == amount


def situation(years=(2026,)):
    return {
        "people": {
            "person1": {
                "age": {year: 30 for year in years},
                "employment_income": {year: 1_000 for year in years},
                "income_tax": {year: 0 for year in years},
                "national_insurance": {year: 0 for year in years},
                "pension_contributions": {year: 0 for year in years},
            }
        },
        "benunits": {
            "family": {
                "members": ["person1"],
                "in_specified_or_temporary_accommodation": {
                    year: True for year in years
                },
                "housing_benefit_net_earnings": {year: 1_000 for year in years},
                "housing_benefit_special_earnings_disregard": {
                    year: 260 for year in years
                },
                "housing_benefit_applicable_amount": {year: 500 for year in years},
                "housing_benefit_on_passporting_benefit": {
                    year: False for year in years
                },
                "housing_benefit_pension_age_regulations_apply": {
                    year: False for year in years
                },
                "housing_benefit_tariff_income": {year: 0 for year in years},
                "housing_benefit_applicable_income_childcare_element": {
                    year: 0 for year in years
                },
                "meets_housing_benefit_additional_earnings_disregard_conditions": {
                    year: False for year in years
                },
                "benunit_rent": {year: 10_400 for year in years},
                "housing_benefit_meals_deduction": {year: 0 for year in years},
                "housing_benefit_non_dep_deductions": {year: 0 for year in years},
                "LHA_eligible": {year: False for year in years},
                "income_support": {year: 0 for year in years},
                "jsa_income": {year: 0 for year in years},
                "esa_income": {year: 0 for year in years},
                "tax_credits": {year: 0 for year in years},
            }
        },
        "households": {"household": {"members": ["person1"]}},
    }


def test_first_year_combines_completed_awards():
    """Reg 71: average the awards, not the income before its £500 threshold."""
    simulation = Simulation(situation=situation())
    before = 10_400 - 0.65 * (1_000 - 260 - 500)
    after = 10_400
    days_before = (date(2026, 10, 5) - date(2026, 4, 6)).days
    days_after = (date(2027, 4, 6) - date(2026, 10, 5)).days
    expected = (before * days_before + after * days_after) / 365
    assert simulation.calculate("housing_benefit_entitlement", 2026)[
        0
    ] == pytest.approx(expected, abs=0.01)


def test_bare_year_zero_reform_has_fiscal_year_boundaries():
    """A 2026 reform must not leak into the following 2027-28 fiscal year."""
    simulation = Simulation(
        situation=situation((2025, 2026, 2027)),
        reform={f"{PREFIX}.single.older": {"2026": 0}},
    )
    amounts = [
        simulation.calculate(
            "housing_benefit_specified_or_temporary_accommodation_disregard", year
        )[0]
        for year in (2025, 2026, 2027)
    ]
    assert amounts == pytest.approx([0, 0, 77.73 * 52], abs=0.01)


def test_dated_zero_reform_is_not_overwritten():
    simulation = Simulation(
        situation=situation(),
        reform={f"{PREFIX}.single.older": {"2026-10-05.2027-04-05": 0}},
    )
    assert simulation.calculate("housing_benefit_entitlement", 2026)[
        0
    ] == pytest.approx(10_400 - 0.65 * (1_000 - 260 - 500), abs=0.01)


def test_later_supplied_income_keeps_its_value():
    simulation = Simulation(situation=situation())
    simulation.set_input("housing_benefit_applicable_income", 2026, [2_000])
    assert simulation.calculate("housing_benefit_entitlement", 2026)[
        0
    ] == pytest.approx(10_400 - 0.65 * (2_000 - 500), abs=0.01)


def test_single_day_zero_reform_changes_only_that_day():
    simulation = Simulation(
        situation=situation(),
        reform={f"{PREFIX}.single.older": {"2026-10-05": 0}},
    )
    before = 10_400 - 0.65 * (1_000 - 260 - 500)
    assert simulation.calculate("housing_benefit_entitlement", 2026)[
        0
    ] == pytest.approx((before * 183 + 10_400 * 182) / 365, abs=0.01)


def test_only_supplied_period_overrides_recalculation():
    data = situation((2025, 2026))
    data["benunits"]["family"]["housing_benefit_applicable_income"] = {2025: 2_000}
    simulation = Simulation(situation=data)
    before = 10_400 - 0.65 * (1_000 - 260 - 500)
    assert simulation.calculate("housing_benefit_entitlement", 2026)[
        0
    ] == pytest.approx((before * 182 + 10_400 * 183) / 365, abs=0.01)


def test_replaced_income_formula_is_not_bypassed():
    class housing_benefit_applicable_income(Variable):
        entity = BenUnit
        definition_period = YEAR
        value_type = float

        def formula(benunit, period, parameters):
            return benunit.filled_array(2_000)

    simulation = Simulation(situation=situation())
    simulation.tax_benefit_system.update_variable(housing_benefit_applicable_income)
    assert simulation.calculate("housing_benefit_entitlement", 2026)[
        0
    ] == pytest.approx(10_400 - 0.65 * (2_000 - 500), abs=0.01)


def test_neutralized_income_is_not_recalculated():
    simulation = Simulation(situation=situation())
    simulation.tax_benefit_system.neutralize_variable(
        "housing_benefit_applicable_income"
    )
    assert simulation.calculate("housing_benefit_entitlement", 2026)[0] == 10_400


def test_replaced_disregard_formula_is_not_bypassed():
    class housing_benefit_applicable_income_disregard(Variable):
        entity = BenUnit
        definition_period = YEAR
        value_type = float

        def formula(benunit, period, parameters):
            return benunit.filled_array(100)

    simulation = Simulation(situation=situation())
    simulation.tax_benefit_system.update_variable(
        housing_benefit_applicable_income_disregard
    )
    assert simulation.calculate("housing_benefit_entitlement", 2026)[
        0
    ] == pytest.approx(10_400 - 0.65 * (1_000 - 100 - 500), abs=0.01)


def test_calculation_does_not_reparent_or_edit_parameter_leaves():
    simulation = Simulation(situation=situation())
    schedule = node(simulation.tax_benefit_system.parameters)
    parents = {
        leaf.name: leaf.parent
        for family in ("single", "lone_parent", "couple")
        for leaf in schedule.children[family].children.values()
    }
    values = {
        leaf.name: [(value.instant_str, value.value) for value in leaf.values_list]
        for family in ("single", "lone_parent", "couple")
        for leaf in schedule.children[family].children.values()
    }
    simulation.calculate("housing_benefit_entitlement", 2026)
    for family in ("single", "lone_parent", "couple"):
        for leaf in schedule.children[family].children.values():
            assert leaf.parent is parents[leaf.name]
            assert [
                (value.instant_str, value.value) for value in leaf.values_list
            ] == values[leaf.name]
