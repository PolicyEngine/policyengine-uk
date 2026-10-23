"""LISA capital transfers reach fiscal totals without becoming current income."""

from copy import deepcopy

import pytest

from policyengine_uk import Simulation


pytestmark = pytest.mark.usefixtures("cloned_uk_tax_benefit_system")


def test_lisa_bonus_and_charge_reach_only_their_declared_fiscal_totals():
    """Source amounts: 2400*25%=600 bonus; gross2000*25%=500 charge.

    Routing capital transfers outside household current income is the explicit
    accounting contract for2584, not an additional statutory income definition.
    Supplied balances are separate stocks and must not be updated by the flows.
    """
    situation = {
        "people": {
            "person": {
                "age": {2026: 35},
                "employment_income": {2026: 30_000},
                "lifetime_isa_balance": {2026: 10_000},
            }
        },
        "benunits": {"benunit": {"members": ["person"]}},
        "households": {
            "household": {
                "members": ["person"],
                "country": {2026: "ENGLAND"},
                "savings": {2026: 1_000},
            }
        },
    }
    with_flows = deepcopy(situation)
    with_flows["people"]["person"].update(
        lifetime_isa_payments={2026: 2_400},
        lifetime_isa_withdrawals={2026: 2_000},
    )
    baseline = Simulation(situation=situation)
    changed = Simulation(situation=with_flows)

    assert changed.calculate("lifetime_isa_bonus", 2026).tolist() == [600]
    assert changed.calculate("lifetime_isa_withdrawal_charge", 2026).tolist() == [500]
    for variable, expected in (("gov_spending", 600), ("gov_tax", 500)):
        difference = changed.calculate(variable, 2026) - baseline.calculate(
            variable, 2026
        )
        assert difference.tolist() == pytest.approx([expected], abs=0.01), variable
    for variable in (
        "household_market_income",
        "household_benefits",
        "household_tax",
        "household_net_income",
        "hbai_household_net_income",
        "lifetime_isa_balance",
        "lifetime_isa_countable_capital",
        "uc_assessable_capital",
    ):
        assert changed.calculate(variable, 2026).tolist() == pytest.approx(
            baseline.calculate(variable, 2026).tolist(), abs=0.01
        ), variable


def test_noncash_isa_interest_charge_reaches_tax_and_final_current_income_once():
    """From fiscal2027,100 of ISA interest gives22 tax and78 net income."""
    situation = {
        "people": {
            "person": {
                "age": {2027: 35},
                "employment_income": {2027: 30_000},
            }
        },
        "benunits": {"benunit": {"members": ["person"]}},
        "households": {
            "household": {"members": ["person"], "country": {2027: "ENGLAND"}}
        },
    }
    with_return = deepcopy(situation)
    with_return["people"]["person"]["non_cash_isa_cash_interest"] = {2027: 100}
    baseline = Simulation(situation=situation)
    changed = Simulation(situation=with_return)
    assert changed.calculate("isa_cash_interest_flat_rate_charge", 2027).tolist() == [
        22
    ]
    for variable, expected in (
        ("market_income", 100),
        ("capital_income", 100),
        ("household_market_income", 100),
        ("gov_tax", 22),
        ("household_tax", 22),
        ("household_net_income", 78),
        ("hbai_household_net_income", 78),
        ("income_tax", 0),
    ):
        difference = changed.calculate(variable, 2027) - baseline.calculate(
            variable, 2027
        )
        assert difference.tolist() == pytest.approx([expected], abs=0.01), variable
