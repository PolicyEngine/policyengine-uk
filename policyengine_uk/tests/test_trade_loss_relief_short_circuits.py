"""Zero current relief preserves real carry, elections and public mutations.

ITA 2007 ss.64, 24A and 83 distinguish the current loss deduction from the
opening same-trade stock. ITTOIA 2005 s.783AF makes an allowance year's
current loss nil. These tests check public amounts, not evaluation order.
"""

import numpy as np
import pytest

from policyengine_uk import Simulation

pytestmark = pytest.mark.usefixtures("cloned_uk_tax_benefit_system")

YEAR = 2024
RELIEF = "trade_loss_relief_against_general_income"
ALLOWANCE = "gov.hmrc.income_tax.allowances.trading_allowance"


def simulate(people):
    return Simulation(
        situation={
            "people": {
                name: {"age": {YEAR: 40}, **inputs} for name, inputs in people.items()
            },
            "benunits": {f"unit_{name}": {"members": [name]} for name in people},
            "households": {f"household_{name}": {"members": [name]} for name in people},
        }
    )


def values(simulation, variable, year=YEAR):
    return np.asarray(simulation.calculate(variable, year), dtype=float)


@pytest.mark.parametrize("raw_loss", [None, 0, -50], ids=["absent", "zero", "negative"])
def test_no_new_loss_preserves_positive_opening_stock(raw_loss):
    person = {
        "employment_income": {year: 0 for year in range(2024, 2027)},
        "self_employment_income": {year: 3_000 for year in range(2024, 2027)},
        "self_employment_gross_receipts": {year: 4_000 for year in range(2024, 2027)},
        "loss_relief": {2024: 7_000},
    }
    if raw_loss is not None:
        person["trading_loss"] = {2024: raw_loss}
    simulation = simulate({"person": person})
    # No new eligible loss gives no current deduction. The separate opening
    # stock still absorbs 3,000 in each of 2024 and 2025: 7,000 - 6,000 = 1,000.
    for year in range(2024, 2027):
        assert values(simulation, RELIEF, year) == pytest.approx([0], abs=0.01)
    assert values(simulation, "loss_relief", 2026) == pytest.approx([1_000], abs=0.01)
    assert values(simulation, "taxable_self_employment_income", 2026) == (
        pytest.approx([2_000], abs=0.01)
    )


def test_mixed_loss_masks_preserve_net_pay_and_relief_cap():
    # The first two have no eligible loss. The third naturally takes full
    # allowance relief: receipts 900, profit 800 and raw loss 200. The fourth
    # has only 2,000 - 1,000 net-pay pension = 1,000 income to relieve. The
    # last is limited by the s.24A cap: max(50,000, 25% * 300,000) = 75,000.
    rows = [
        (0, 500, 0, 0, 0),
        (-50, 500, 0, 0, 0),
        (200, 40_000, 800, 900, 0),
        (3_000, 2_000, 0, 0, 1_000),
        (200_000, 300_000, 0, 0, 0),
    ]
    simulation = simulate(
        {
            f"person{i}": {
                "trading_loss": {YEAR: loss},
                "employment_income": {YEAR: pay},
                "self_employment_income": {YEAR: profit},
                "self_employment_gross_receipts": {YEAR: receipts},
                "employee_pension_contributions": {YEAR: net_pay},
            }
            for i, (loss, pay, profit, receipts, net_pay) in enumerate(rows)
        }
    )
    np.testing.assert_array_equal(
        values(simulation, "uses_trading_allowance"), [False, False, True, False, False]
    )
    assert values(simulation, "net_pay_pension_relief") == pytest.approx(
        [0, 0, 0, 1_000, 0], abs=0.01
    )
    assert values(simulation, "income_tax_relief_cap") == pytest.approx(
        [50_000, 50_000, 50_000, 50_000, 75_000], abs=0.05
    )
    assert values(simulation, RELIEF) == pytest.approx(
        [0, 0, 0, 1_000, 75_000], abs=0.05
    )
    assert values(simulation, "loss_relief", 2025) == pytest.approx(
        [0, 0, 0, 2_000, 125_000], abs=0.05
    )


def test_zero_and_positive_relief_refresh_after_public_changes():
    simulation = simulate(
        {
            "person": {
                "employment_income": {YEAR: 40_000},
                "trading_loss": {YEAR: 0},
                "loss_relief": {YEAR: 7_000},
            }
        }
    )
    assert values(simulation, RELIEF) == pytest.approx([0], abs=0.01)
    assert values(simulation, "loss_relief", 2025) == pytest.approx([7_000], abs=0.01)
    simulation.set_input("trading_loss", YEAR, np.array([50_000.0]))
    assert values(simulation, RELIEF) == pytest.approx([40_000], abs=0.01)
    assert values(simulation, "loss_relief", 2025) == pytest.approx([17_000], abs=0.01)

    branch = simulation.get_branch("current_loss_reset")
    branch.set_input("trading_loss", YEAR, np.array([0.0]))
    assert values(branch, RELIEF) == pytest.approx([0], abs=0.01)
    assert values(branch, "loss_relief", 2025) == pytest.approx([7_000], abs=0.01)
    branch.set_input("trading_loss", YEAR, np.array([500.0]))
    assert values(branch, RELIEF) == pytest.approx([500], abs=0.01)
    assert values(branch, "loss_relief", 2025) == pytest.approx([7_000], abs=0.01)
    assert values(simulation, RELIEF) == pytest.approx([40_000], abs=0.01)

    simulation.set_input("trading_loss", YEAR, np.array([0.0]))
    assert values(simulation, RELIEF) == pytest.approx([0], abs=0.01)
    # A supplied final relief remains an engine override even with raw loss0.
    simulation.set_input(RELIEF, YEAR, np.array([123.0]))
    assert values(simulation, RELIEF) == pytest.approx([123], abs=0.01)
    assert values(simulation, "loss_relief", 2025) == pytest.approx([7_000], abs=0.01)

    election = simulate(
        {
            "person": {
                "employment_income": {YEAR: 40_000},
                "self_employment_income": {YEAR: 800},
                "self_employment_gross_receipts": {YEAR: 900},
                "trading_loss": {YEAR: 200},
            }
        }
    )
    np.testing.assert_array_equal(values(election, "uses_trading_allowance"), [True])
    assert values(election, RELIEF) == pytest.approx([0], abs=0.01)
    election.apply_reform({ALLOWANCE: {str(YEAR): 0}})
    np.testing.assert_array_equal(values(election, "uses_trading_allowance"), [False])
    assert values(election, RELIEF) == pytest.approx([200], abs=0.01)
    election.apply_reform({ALLOWANCE: {str(YEAR): 1_000}})
    np.testing.assert_array_equal(values(election, "uses_trading_allowance"), [True])
    assert values(election, RELIEF) == pytest.approx([0], abs=0.01)
