"""Property-rate routing before and from the model's annual 2027 period.

Finance Act 2026 ss. 6(8) and 7 commence the separate property rates in
2027-28. Earlier rUK property income follows the complete main-rate scale.
The amounts below are independent marginal-band arithmetic, not snapshots.
https://www.legislation.gov.uk/ukpga/2026/11/section/6/enacted
https://www.legislation.gov.uk/ukpga/2026/11/section/7/enacted
"""

import pytest

from policyengine_uk import Simulation

pytestmark = pytest.mark.usefixtures("cloned_uk_tax_benefit_system")

UK_RATE = "gov.hmrc.income_tax.rates.uk[{}].rate"
PROPERTY_BASIC = "gov.hmrc.income_tax.rates.property.basic"
RUK_COUNTRIES = ("ENGLAND", "WALES", "NORTHERN_IRELAND")


def component_simulation(
    year, earned, property_income, gift=0, country="ENGLAND", rates=None
):
    """Control taxable amounts after ordinary allowances to isolate the producer."""
    return Simulation(
        situation={
            "people": {
                "person": {
                    "age": {year: 40},
                    "non_savings_income_after_allowances": {
                        year: earned + property_income
                    },
                    "taxable_property_income_after_allowances": {year: property_income},
                    "gift_aid_grossed_up": {year: gift},
                }
            },
            "benunits": {"benunit": {"members": ["person"]}},
            "households": {
                "household": {"members": ["person"], "country": {year: country}}
            },
        },
        reform={path: {str(year): value} for path, value in (rates or {}).items()},
    )


@pytest.mark.parametrize("year", [2025, 2026])
@pytest.mark.parametrize("country", RUK_COUNTRIES)
@pytest.mark.parametrize(
    "earned, bracket, rate, expected",
    [(10_000, 0, 0.21, 1_050), (40_000, 1, 0.41, 2_050), (130_000, 2, 0.46, 2_300)],
    ids=["basic", "higher", "additional"],
)
def test_pre_2027_property_income_uses_main_rate_reform(
    year, country, earned, bracket, rate, expected
):
    sim = component_simulation(
        year, earned, 5_000, country=country, rates={UK_RATE.format(bracket): rate}
    )
    assert sim.calculate("property_income_tax", year)[0] == pytest.approx(
        expected, abs=0.01
    )


@pytest.mark.parametrize("year", [2025, 2026])
@pytest.mark.parametrize(
    "earned, gift, expected",
    [(36_700, 0, 1_850), (36_700, 2_000, 1_450), (124_140, 2_000, 2_150)],
    ids=["basic-higher", "gift-basic-higher", "gift-higher-additional"],
)
def test_main_rate_band_crossings_respect_gift_aid(year, earned, gift, expected):
    rates = {UK_RATE.format(i): value for i, value in enumerate((0.21, 0.41, 0.46))}
    sim = component_simulation(year, earned, 5_000, gift, rates=rates)
    assert sim.calculate("property_income_tax", year)[0] == pytest.approx(
        expected, abs=0.01
    )


@pytest.mark.parametrize("year", [2025, 2026])
@pytest.mark.parametrize("gift", [0, 2_000])
def test_pre_2027_property_income_uses_optional_fourth_main_bracket(year, gift):
    sim = component_simulation(
        year, 9_999_000, 5_000, gift, rates={UK_RATE.format(3): 0.60}
    )
    # Gift Aid extends statutory basic/higher limits, not this optional bracket.
    assert sim.calculate("property_income_tax", year)[0] == pytest.approx(
        1_000 * 0.45 + 4_000 * 0.60, abs=0.01
    )


@pytest.mark.parametrize("year", [2027, 2028])
@pytest.mark.parametrize("country", RUK_COUNTRIES)
def test_from_2027_main_rate_reform_leaves_separate_property_rate_unchanged(
    year, country
):
    sim = component_simulation(
        year, 10_000, 5_000, country=country, rates={UK_RATE.format(0): 0.21}
    )
    # 5,000 at the 24% property basic rate (22% from Budget 2025, 2 points
    # more from Budget 2026).
    assert sim.calculate("property_income_tax", year)[0] == pytest.approx(
        1_200, abs=0.01
    )


@pytest.mark.parametrize("year", [2027, 2028])
def test_from_2027_separate_property_rate_reform_changes_property_tax(year):
    sim = component_simulation(year, 10_000, 5_000, rates={PROPERTY_BASIC: 0.23})
    assert sim.calculate("property_income_tax", year)[0] == pytest.approx(
        1_150, abs=0.01
    )


@pytest.mark.parametrize("year", [2025, 2026])
def test_pre_2027_separate_property_rate_reform_does_not_apply(year):
    sim = component_simulation(year, 10_000, 5_000, rates={PROPERTY_BASIC: 0.99})
    assert sim.calculate("property_income_tax", year)[0] == pytest.approx(
        1_000, abs=0.01
    )


@pytest.mark.parametrize("year", [2025, 2026, 2027, 2028])
def test_scottish_property_tax_keeps_scottish_rates_under_uk_reform(year):
    rates = {UK_RATE.format(i): value for i, value in enumerate((0.21, 0.41, 0.46))}
    sim = component_simulation(year, 40_000, 5_000, country="SCOTLAND", rates=rates)
    assert sim.calculate("property_income_tax", year)[0] == pytest.approx(
        5_000 * 0.42, abs=0.01
    )


@pytest.mark.parametrize("year", [2025, 2026])
def test_scottish_gift_aid_band_crossing_is_unchanged(year):
    sim = component_simulation(
        year, 30_000, 5_000, 2_000, "SCOTLAND", {UK_RATE.format(1): 0.41}
    )
    assert sim.calculate("property_income_tax", year)[0] == pytest.approx(
        3_092 * 0.21 + 1_908 * 0.42, abs=0.01
    )


@pytest.mark.parametrize("year", [2025, 2026, 2027, 2028])
def test_zero_property_income_has_zero_property_tax_under_reform(year):
    sim = component_simulation(year, 40_000, 0, rates={UK_RATE.format(1): 0.41})
    assert sim.calculate("property_income_tax", year)[0] == 0


@pytest.mark.parametrize(
    "year, expected", [(2025, 1_000), (2026, 1_000), (2027, 1_200), (2028, 1_200)]
)
def test_baseline_property_rates_retain_annual_2027_boundary(year, expected):
    sim = component_simulation(year, 10_000, 5_000)
    assert sim.calculate("property_income_tax", year)[0] == pytest.approx(
        expected, abs=0.01
    )


@pytest.mark.parametrize("country", RUK_COUNTRIES)
def test_main_rate_reform_reaches_property_and_final_tax_from_natural_income(country):
    year = 2026
    sim = Simulation(
        situation={
            "people": {
                "person": {
                    "age": {year: 40},
                    "employment_income": {year: 22_570},
                    "property_income": {year: 5_000},
                    "property_allowance_deduction": {year: 0},
                }
            },
            "benunits": {"benunit": {"members": ["person"]}},
            "households": {
                "household": {"members": ["person"], "country": {year: country}}
            },
        },
        reform={UK_RATE.format(0): {str(year): 0.21}},
    )
    assert sim.calculate("personal_allowance", year)[0] == 12_570
    assert sim.calculate("non_savings_income_after_allowances", year)[0] == 15_000
    assert sim.calculate("taxable_property_income_after_allowances", year)[0] == 5_000
    assert sim.calculate("earned_income_tax", year)[0] == pytest.approx(2_100, abs=0.01)
    assert sim.calculate("property_income_tax", year)[0] == pytest.approx(
        1_050, abs=0.01
    )
    assert sim.calculate("income_tax", year)[0] == pytest.approx(3_150, abs=0.01)
