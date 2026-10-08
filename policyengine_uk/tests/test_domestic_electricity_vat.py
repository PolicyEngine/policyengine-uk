"""
Domestic electricity VAT: the temporary GB zero rate (SI 2026/987) and the
explicit energy VAT base (#2166).

From 1 October 2026 to 31 March 2027 domestic electricity in England, Wales
and Scotland is zero-rated; Northern Ireland and gas stay at 5%. Model year
2026 runs 6 April 2026 to 5 April 2027, so with equal daily use it has 183
days at 5% and 182 at 0%.
"""

from pathlib import Path

import pytest
from policyengine_core.parameters import ParameterNode
from policyengine_core.reforms import Reform

import policyengine_uk
from policyengine_uk import Simulation
from policyengine_uk.model_api import Scenario
from policyengine_uk.system import system

FY2026_SHARE_AT_5_PERCENT = 183 / 365
GB_RATE = "gov.hmrc.vat.domestic_electricity_rate.great_britain"


def raw_parameters() -> ParameterNode:
    """Parameters as written, before uprating and fiscal-year conversion."""
    directory = Path(policyengine_uk.__file__).parent / "parameters"
    return ParameterNode(directory_path=str(directory))


def household(
    region="LONDON",
    electricity=1_050,
    gas=0,
    consumption=20_000,
    year=2026,
):
    return {
        "people": {"adult": {"age": {year: 45}}},
        "benunits": {"benunit": {"members": ["adult"]}},
        "households": {
            "household": {
                "members": ["adult"],
                "region": {year: region},
                "consumption": {year: consumption},
                "electricity_consumption": {year: electricity},
                "gas_consumption": {year: gas},
            }
        },
    }


def calc(variable, year=2026, scenario=None, **kwargs):
    sim = Simulation(situation=household(year=year, **kwargs), scenario=scenario)
    return float(sim.calculate(variable, year)[0])


@pytest.mark.parametrize(
    "date, rate",
    [
        ("2026-09-30", 0.05),
        ("2026-10-01", 0.0),
        ("2027-03-31", 0.0),
        ("2027-04-01", 0.05),
    ],
)
def test_gb_rate_changes_on_both_statutory_dates(date, rate):
    rates = raw_parameters().gov.hmrc.vat.domestic_electricity_rate
    assert rates.great_britain(date) == pytest.approx(rate)
    assert rates.northern_ireland(date) == pytest.approx(0.05)


def test_fy2026_gb_rate_is_day_weighted():
    rates = system.parameters.gov.hmrc.vat.domestic_electricity_rate
    assert rates.great_britain("2025") == pytest.approx(0.05)
    assert rates.great_britain("2026") == pytest.approx(
        0.05 * FY2026_SHARE_AT_5_PERCENT
    )
    assert rates.great_britain("2027") == pytest.approx(0.05)
    assert rates.northern_ireland("2026") == pytest.approx(0.05)


@pytest.mark.parametrize("region", ["LONDON", "WALES", "SCOTLAND"])
def test_gb_electricity_vat_in_fy2026(region):
    # £1,050 of bills includes £50 of VAT at 5%.
    assert calc("domestic_energy_vat", region=region) == pytest.approx(
        50 * FY2026_SHARE_AT_5_PERCENT
    )


def test_northern_ireland_keeps_5_percent():
    assert calc("domestic_energy_vat", region="NORTHERN_IRELAND") == pytest.approx(50)


def test_gas_is_unchanged():
    assert calc("domestic_energy_vat", electricity=0, gas=1_050) == pytest.approx(50)


@pytest.mark.parametrize("year", [2025, 2027])
def test_years_either_side_are_at_5_percent(year):
    assert calc("domestic_energy_vat", year=year) == pytest.approx(50)


def test_vat_responds_to_electricity():
    low = calc("vat", electricity=1_200)
    high = calc("vat", electricity=5_000)
    expected = 3_800 / 1.05 * 0.05 * FY2026_SHARE_AT_5_PERCENT
    assert high - low == pytest.approx(expected)


def test_energy_vat_is_not_grossed_up_by_coverage():
    with_energy = calc("vat", electricity=1_050, gas=1_050, year=2025)
    without_energy = calc("vat", electricity=0, gas=0, year=2025)
    assert with_energy - without_energy == pytest.approx(100)


def test_domestic_fuel_and_power_leaves_the_generic_reduced_rate_base():
    # The ONS domestic fuel and power share of spending (2.79% in 2025) exceeds
    # the OBR's 2.5% reduced-rate share, so nothing is left in the generic base.
    assert calc("reduced_rate_vat_consumption", year=2025) == 0


def test_non_energy_reduced_rate_base_is_kept():
    # A reduced-rate share above the domestic fuel and power share keeps the
    # remainder in the generic base, at the reduced rate.
    scenario = Scenario(
        parameter_changes={"gov.hmrc.vat.reduced_rate_share": {"2025": 0.0379}}
    )
    base = calc("reduced_rate_vat_consumption", year=2025, scenario=scenario)
    assert base == pytest.approx(20_000 * (0.0379 - 0.0279))


def test_no_reform_means_no_vat_change():
    assert calc("vat_change") == pytest.approx(0)
    assert calc("baseline_domestic_energy_vat") == pytest.approx(
        calc("domestic_energy_vat")
    )


def test_extending_the_zero_rate_to_fy2027():
    # A whole-year reform. A reform dated part-way through a year is not
    # day-weighted on blended parameters (#2167).
    reform = Reform.from_dict(
        {GB_RATE: {"2027-01-01.2027-12-31": 0.0}}, country_id="uk"
    )
    sim = Simulation(situation=household(year=2027), reform=reform)
    assert sim.calculate("domestic_energy_vat", 2027)[0] == 0
    assert sim.calculate("baseline_domestic_energy_vat", 2027)[0] == pytest.approx(50)
    assert sim.calculate("vat_change", 2027)[0] == pytest.approx(-50)


def test_reduced_rate_reform_reaches_gas_not_electricity():
    scenario = Scenario(parameter_changes={"gov.hmrc.vat.reduced_rate": {"2025": 0.0}})
    assert calc(
        "domestic_energy_vat", year=2025, scenario=scenario, gas=1_050
    ) == pytest.approx(50)
