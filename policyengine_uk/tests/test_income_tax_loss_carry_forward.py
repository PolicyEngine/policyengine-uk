"""Income Tax loss stock, supplied-year provenance and public cache APIs.

The conservation test follows actual income deductions, including amounts
that fall within the personal allowance. It does not count a tax saving as
loss consumption or assume that Income Tax and Class 4 stocks are equal.
"""

from functools import lru_cache
from unittest.mock import patch

import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from policyengine_core import periods
from policyengine_core.reforms import Reform

from policyengine_uk import CountryTaxBenefitSystem, Simulation
from policyengine_uk.utils.supplied_inputs import (
    set_model_value,
    supplied_input_periods,
)


@lru_cache(maxsize=1)
def model_template():
    """Load source once; give every generated world independent model state."""
    return CountryTaxBenefitSystem()


def simulation(person):
    # Match the repository's cloned_uk_tax_benefit_system fixture. The UK
    # wrapper constructs its system internally, rather than accepting Core's
    # tax_benefit_system constructor keyword.
    with patch(
        "policyengine_uk.simulation.CountryTaxBenefitSystem",
        side_effect=model_template().clone,
    ):
        return Simulation(
            situation={
                "people": {"person": person},
                "benunits": {"benunit": {"members": ["person"]}},
                "households": {"household": {"members": ["person"]}},
            }
        )


def value(sim, name, year):
    return float(sim.calculate(name, year)[0])


def history():
    return {
        "age": {2024: 40},
        "taxable_social_security_income": {2024: 0},
        "employment_income": {2024: 0, 2025: 0, 2026: 0},
        "self_employment_income": {2024: 0, 2025: 2_000, 2026: 5_000},
        "trading_loss": {2024: 10_000},
        "trading_allowance_deduction": {2024: 0, 2025: 0, 2026: 0},
    }


@settings(max_examples=20, deadline=None, derandomize=True)
@given(
    st.lists(
        st.tuples(
            st.integers(0, 80_000),  # Profit before losses.
            st.integers(0, 120_000),  # Current loss in the eligible trade pool.
            st.integers(0, 180_000),  # Other income.
        ),
        min_size=2,
        max_size=5,
    ),
    st.one_of(st.none(), st.tuples(st.integers(0, 4), st.integers(0, 100_000))),
)
def test_deductions_and_remaining_stock_conserve_each_loss_segment(years, reset):
    calendar = list(range(2024, 2024 + len(years)))
    person = {
        "age": {2024: 40},
        "taxable_social_security_income": {2024: 0},
        "self_employment_income": dict(zip(calendar, [x[0] for x in years])),
        "trading_loss": dict(zip(calendar, [x[1] for x in years])),
        "employment_income": dict(zip(calendar, [x[2] for x in years])),
        "trading_allowance_deduction": dict.fromkeys(calendar, 0),
    }
    reset_index = None if reset is None else reset[0] % len(years)
    if reset is not None:
        person["loss_relief"] = {calendar[reset_index]: reset[1]}
    sim = simulation(person)
    # Request the latest stock first: cached calculation order must not
    # become an input or cause a recursive spiral through the allowance.
    value(sim, "loss_relief", calendar[-1] + 1)
    available = used = expected_opening = 0
    for index, (year, (profit, loss, pay)) in enumerate(zip(calendar, years)):
        if index == reset_index:
            available, used, expected_opening = reset[1], 0, reset[1]
        opening = value(sim, "loss_relief", year)
        assert opening == expected_opening
        absorbed = min(opening, profit)
        taxable = profit - absorbed
        income = pay + taxable
        # The s.24A cap restores s.83 relief; available income stays net of it.
        general = min(loss, max(50_000, (pay + profit) * 0.25), income)
        assert value(sim, "taxable_self_employment_income", year) == taxable
        assert value(sim, "trade_loss_relief_against_general_income", year) == general
        available += loss
        used += absorbed + general
        expected_opening = available - used
        # A supplied next-year balance overrides this segment's derived carry.
        next_opening = reset[1] if index + 1 == reset_index else expected_opening
        assert value(sim, "loss_relief", year + 1) == next_opening
        assert expected_opening >= 0


@pytest.mark.parametrize("order", [(2026, 2024, 2025), (2024, 2025, 2026)])
def test_opening_stock_is_independent_of_calculation_order(order):
    sim = simulation(history())
    expected = {2024: 0, 2025: 10_000, 2026: 8_000}
    for year in order:
        assert value(sim, "loss_relief", year) == expected[year]
    recorded = supplied_input_periods(sim.populations["person"], "loss_relief")
    assert recorded == []


def test_a_zero_reset_on_a_branch_does_not_change_the_parent():
    sim = simulation(history())
    assert value(sim, "loss_relief", 2026) == 8_000
    branch = sim.get_branch("external_loss_use")
    branch.set_input("loss_relief", 2025, np.array([0.0]))
    assert value(branch, "loss_relief", 2026) == 0
    assert value(sim, "loss_relief", 2026) == 8_000
    assert supplied_input_periods(sim.populations["person"], "loss_relief") == []


def test_replacing_a_clones_loss_does_not_change_the_original():
    sim = simulation(history())
    clone = sim.clone()
    clone.set_input("trading_loss", 2024, np.array([6_000.0]))
    assert value(sim, "loss_relief", 2026) == 8_000
    assert value(clone, "loss_relief", 2026) == 4_000


@pytest.mark.parametrize("variable", ["trading_loss", "loss_relief"])
def test_deleted_inputs_do_not_reappear_as_supplied_history(variable):
    person = history()
    if variable == "loss_relief":
        person.pop("trading_loss")
        person["loss_relief"] = {2024: 10_000}
    sim = simulation(person)
    sim.delete_arrays(variable, 2024)
    assert value(sim, "loss_relief", 2026) == 0
    assert supplied_input_periods(sim.populations["person"], variable) == []


def test_model_written_loss_is_not_a_new_supplied_loss():
    sim = simulation(history())
    set_model_value(sim, "trading_loss", periods.period(2025), np.array([9_000.0]))
    assert value(sim, "loss_relief", 2026) == 8_000
    assert value(sim, "trade_loss_relief_against_general_income", 2025) == 0


def test_neutralizing_the_loss_removes_automatic_carry_forward():
    class neutralize_loss(Reform):
        def apply(self):
            self.neutralize_variable("trading_loss")

    sim = simulation(history())
    assert value(sim, "loss_relief", 2026) == 8_000
    sim.apply_reform(neutralize_loss)
    assert value(sim, "loss_relief", 2026) == 0
