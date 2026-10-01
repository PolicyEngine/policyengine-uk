"""Fiscal-year segmentation and Scenario integration for household excise duties."""

import pytest
from policyengine_core.parameters import ParameterNode

from policyengine_uk import CountryTaxBenefitSystem, Microsimulation
from policyengine_uk.model_api import Scenario
from policyengine_uk.utils.excise import fiscal_year_segments


def test_segment_weights_include_budget_day_time_and_leap_day():
    """The FY2023 denominator is 366; 22 November changes at 6pm."""
    node = ParameterNode(
        "rates",
        data={
            "rate": {
                "values": {
                    "2023-04-06": 1,
                    "2023-11-22": {
                        "value": 2,
                        "metadata": {"effective_time": "18:00:00"},
                    },
                }
            }
        },
    )
    segments = list(fiscal_year_segments(node, 2023))
    assert [rates.rate for rates, share in segments] == [1, 2]
    assert [share for rates, share in segments] == pytest.approx(
        [230.75 / 366, 135.25 / 366]
    )


def test_schedules_keep_statutory_dates_after_parameter_processing():
    """February alcohol and October tobacco changes survive fiscal conversion."""
    system = CountryTaxBenefitSystem()
    alcohol = system.parameters.gov.hmrc.alcohol_duty.rates.beer
    tobacco = system.parameters.gov.hmrc.tobacco_duty.rates.cigarette_specific
    assert alcohol("2026-01-31") == 21.78
    assert alcohol("2026-02-01") == 22.58
    assert tobacco("2026-09-30") == 0.3535
    assert tobacco("2026-10-01") == 0.39409


def simulation(changes, person=None, household=None):
    return Microsimulation(
        situation={
            "people": {"person": {"age": {2026: 40}, **(person or {})}},
            "benunits": {"benunit": {"members": ["person"]}},
            "households": {"household": {"members": ["person"], **(household or {})}},
        },
        scenario=Scenario(parameter_changes=changes),
    )


@pytest.mark.parametrize(
    "changes, household, variable, expected",
    [
        (
            {"gov.hmrc.alcohol_duty.rates.beer": {"2026": 30}},
            {"beer_litres": {2026: 100}, "beer_abv": {2026: 0.05}},
            "alcohol_duty",
            150,
        ),
        (
            {"gov.hmrc.alcohol_duty.rates.draught_other": {"2026": 10}},
            {
                "beer_litres": {2026: 100},
                "beer_abv": {2026: 0.05},
                "beer_draught_share": {2026: 1},
            },
            "alcohol_duty",
            50,
        ),
        (
            {"gov.hmrc.tobacco_duty.rates.cigarette_minimum": {"2026": 1}},
            {
                "cigarettes_per_week": {2026: 20},
                "cigarette_price_per_pack": {2026: 10},
            },
            "tobacco_duty",
            1_040,
        ),
        (
            {"gov.hmrc.fuel_duty.lpg": {"2026": 1}},
            {"lpg_kg": {2026: 1_000}},
            "fuel_duty",
            1_000,
        ),
    ],
)
def test_annual_reform_applies_across_the_full_fiscal_year(
    changes, household, variable, expected
):
    """Reforms name fiscal years and must not revert for January to April."""
    sim = simulation(changes, household=household)
    assert sim.calculate(variable, 2026).values[0] == pytest.approx(expected)


def test_zero_emission_supplement_threshold_reform():
    """Restoring the £40,000 threshold adds the £440 supplement in 2026."""
    person = {
        "car_first_registration_date": {2026: "2025-05-01"},
        "car_fuel_type": {2026: "ELECTRIC"},
        "car_list_price": {2026: 45_000},
    }
    baseline = simulation({}, person=person)
    reform = simulation(
        {
            "gov.dft.vehicle_excise_duty.zero_emission_expensive_car_threshold": {
                "2026": 40_000
            }
        },
        person=person,
    )
    assert baseline.calculate("vehicle_excise_duty", 2026).values[0] == 200
    assert reform.calculate("vehicle_excise_duty", 2026).values[0] == 640


def test_annual_tobacco_override_leaves_adjacent_years_on_law():
    sim = simulation({"gov.hmrc.tobacco_duty.rates.cigarette_minimum": {"2026": 1}})
    node = sim.tax_benefit_system.parameters.gov.hmrc.tobacco_duty.rates
    for year, expected in [
        (2025, (0.44667 * 234.75 + 0.47193 * 130.25) / 365),
        (2026, 1),
        (2027, 0.51875),
    ]:
        result = sum(
            p.cigarette_minimum * weight
            for p, weight in fiscal_year_segments(node, year)
        )
        assert result == pytest.approx(expected)


def test_legacy_bare_year_reform_uses_the_fiscal_year_for_preserved_rates():
    """Existing reform dictionaries must cover January-April of the named FY."""
    sim = Microsimulation(
        situation={
            "people": {"person": {"age": {2026: 40}}},
            "benunits": {"benunit": {"members": ["person"]}},
            "households": {
                "household": {
                    "members": ["person"],
                    "beer_litres": {2026: 100},
                    "beer_abv": {2026: 0.05},
                }
            },
        },
        reform={"gov.hmrc.alcohol_duty.rates.beer": {"2026": 30}},
    )
    assert sim.calculate("alcohol_duty", 2026).values[0] == pytest.approx(150)
