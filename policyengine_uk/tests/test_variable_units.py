"""Units of variables whose values are shares, pound amounts or flags.

A variable's unit is served in the model metadata and decides how a value is
displayed: a "/1" variable as a percentage, a currency variable in pounds. In
policyengine-core it also sets the default quantity type. A float with the
unit "/1" is a stock and any other float is a flow, and a yearly flow read
for a month is divided by twelve, where a yearly stock is not.

So a share must declare "/1" (a month's share of the national total is the
share, not a twelfth of it), a pound amount must declare pounds, and a
true/false variable declares no unit.
"""

import pytest

from policyengine_uk import CountryTaxBenefitSystem, Simulation
from policyengine_uk.model_api import FLOW, GBP, MONTHS_IN_YEAR, STOCK

YEAR = 2025
SHARES = ["shareholding", "consumption_shareholding"]


@pytest.fixture(scope="module")
def variables():
    return CountryTaxBenefitSystem().variables


def _household(variable, value):
    """One household with the variable entered directly for the year."""
    return Simulation(
        situation={
            "people": {"person": {"age": {YEAR: 40}}},
            "benunits": {"benunit": {"members": ["person"]}},
            "households": {
                "household": {"members": ["person"], variable: {YEAR: value}}
            },
        }
    )


@pytest.mark.parametrize("share", SHARES)
def test_a_share_declares_a_ratio_and_is_a_stock(variables, share):
    assert variables[share].unit == "/1"
    assert variables[share].quantity_type == STOCK


@pytest.mark.parametrize("share", SHARES)
def test_a_share_read_for_a_month_is_the_share(share):
    simulation = _household(share, 0.25)
    assert simulation.calculate(share, YEAR).tolist() == [0.25]
    assert simulation.calculate(share, f"{YEAR}-01").tolist() == [0.25]


def test_free_tv_licence_value_is_in_pounds_and_is_a_flow(variables):
    assert variables["free_tv_licence_value"].unit == GBP
    assert variables["free_tv_licence_value"].quantity_type == FLOW


def test_free_tv_licence_value_read_for_a_month_is_a_twelfth():
    simulation = _household("free_tv_licence_value", 180)
    assert simulation.calculate("free_tv_licence_value", YEAR).tolist() == [180]
    assert simulation.calculate("free_tv_licence_value", f"{YEAR}-01").tolist() == [
        180 / MONTHS_IN_YEAR
    ]


def test_no_true_or_false_variable_declares_a_unit(variables):
    with_a_unit = {
        name: variable.unit
        for name, variable in variables.items()
        if variable.value_type is bool and variable.unit is not None
    }
    assert with_a_unit == {}
