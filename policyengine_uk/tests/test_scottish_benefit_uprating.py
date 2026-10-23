"""Scottish rates follow September CPI and compound rounded annual awards.

September CPI and nearest-5p rounding are Scottish Ministers' current policy,
not a statutory choice of index (2018 Act s86A(5)). The 2025-26 and 2026-27
uprating reports supply the historical anchors below. The April 2027
projections use September 2026 CPI of 3.5%, published by ONS in October.
"""

from decimal import Decimal, ROUND_HALF_UP

import pytest
from policyengine_core.parameters import load_parameter_file

from policyengine_uk import Simulation
from policyengine_uk.model_api import Scenario
from policyengine_uk.system import system
from policyengine_uk.tax_benefit_system import COUNTRY_DIR


SCOTLAND = "gov.social_security_scotland"
SCP = f"{SCOTLAND}.scottish_child_payment.amount"
PAWHP = f"{SCOTLAND}.pawhp.amount"
INDEX = "gov.benefit_uprating_cpi"

# Published amounts from the Scottish Government's annual uprating reports.
# The last two PAWHP rates coincide but are separate statutory awards.
PUBLISHED = {
    SCP: (27.15, 28.20),
    f"{PAWHP}.higher": (305.10, 316.70),
    f"{PAWHP}.lower": (203.40, 211.15),
    f"{PAWHP}.higher_shared_with_80_or_over": (152.55, 158.35),
    f"{PAWHP}.lower_shared": (101.70, 105.55),
    f"{PAWHP}.higher_shared_with_under_80": (203.40, 211.15),
}

# Independent hand calculations: 2026 amount x 1.035, nearest 5p.
# 28.20 -> 29.187; 316.70 -> 327.7845; 211.15 -> 218.54025;
# 158.35 -> 163.89225; 105.55 -> 109.24425.
APRIL_2027 = {
    SCP: 29.20,
    f"{PAWHP}.higher": 327.80,
    f"{PAWHP}.lower": 218.55,
    f"{PAWHP}.higher_shared_with_80_or_over": 163.90,
    f"{PAWHP}.lower_shared": 109.25,
    f"{PAWHP}.higher_shared_with_under_80": 218.55,
}


@pytest.mark.parametrize("name, amounts", PUBLISHED.items())
def test_published_2025_and_2026_scottish_rates_are_preserved(name, amounts):
    parameter = system.parameters.get_child(name)
    for year, expected in zip((2025, 2026), amounts):
        assert parameter(f"{year}-04-30") == expected


@pytest.mark.parametrize("name, expected", APRIL_2027.items())
def test_april_2027_scottish_rates_use_published_september_cpi(name, expected):
    assert system.parameters.get_child(name)("2027-04-30") == pytest.approx(
        expected, abs=1e-9
    )


@pytest.fixture(scope="module")
def raw_parameters():
    return load_parameter_file(str(COUNTRY_DIR / "parameters"), name="")


@pytest.mark.parametrize("name", PUBLISHED)
def test_scottish_projection_starts_after_the_last_enacted_rate(raw_parameters, name):
    """SFC 2027-30 forecasts must not override the new September projection."""
    parameter = raw_parameters.get_child(name)
    assert max(value.instant_str for value in parameter.values_list) == "2026-04-01"
    uprating = parameter.metadata["uprating"]
    assert uprating["parameter"] == INDEX
    assert uprating["rounding"] == {"type": "nearest", "interval": 0.05}


@pytest.mark.parametrize("name, amounts", PUBLISHED.items())
def test_later_scottish_projections_compound_the_previous_rounded_amount(name, amounts):
    """Check every projected year, including beyond the former 2030 anchor.

    The independent calculation reads annual CPI growth, rather than the
    cumulative index ratio, and rounds after each year's increase.
    """
    parameters = system.parameters
    parameter = parameters.get_child(name)
    previous = Decimal(str(amounts[1]))
    increment = Decimal("0.05")
    for year in range(2027, 2040):
        rate = parameters.gov.economic_assumptions.yoy_growth.september_cpi_uprating(
            f"{year}-01-01"
        )
        unrounded = previous * (1 + Decimal(str(rate)))
        expected = (unrounded / increment).quantize(
            Decimal("1"), rounding=ROUND_HALF_UP
        ) * increment
        assert parameter(f"{year}-04-30") == pytest.approx(float(expected), abs=1e-9), (
            name,
            year,
        )
        previous = expected


@pytest.mark.parametrize("september", [0.035, 0.05])
def test_april_2027_uses_september_cpi_even_when_calendar_cpi_differs(september):
    """Observed September CPI controls 2027; calendar 2027 affects later forecasts."""
    simulation = Simulation(
        situation={
            "people": {"person": {"age": {2027: 40}}},
            "benunits": {"benunit": {"members": ["person"]}},
            "households": {"household": {"members": ["person"]}},
        },
        scenario=Scenario(
            applied_before_data_load=True,
            parameter_changes={
                "gov.economic_assumptions.statutory_uprating_inputs.cpi_september": {
                    "year:2026-09-01:1": september
                },
                "gov.economic_assumptions.yoy_growth.obr.consumer_price_index": {
                    "year:2027-01-01:1": 0.11
                },
            },
        ),
    )
    expected = (
        APRIL_2027
        if september == 0.035
        else {
            SCP: 29.60,
            f"{PAWHP}.higher": 332.55,
            f"{PAWHP}.lower": 221.70,
            f"{PAWHP}.higher_shared_with_80_or_over": 166.25,
            f"{PAWHP}.lower_shared": 110.85,
            f"{PAWHP}.higher_shared_with_under_80": 221.70,
        }
    )
    parameters = simulation.tax_benefit_system.parameters
    for name, amount in expected.items():
        assert parameters.get_child(name)("2027-04-30") == pytest.approx(
            amount, abs=1e-9
        ), name
        assert parameters.get_child(name)("2026-04-30") == PUBLISHED[name][1]
