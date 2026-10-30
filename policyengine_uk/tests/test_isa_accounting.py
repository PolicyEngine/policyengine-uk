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


GDP_INDEX = "gov.economic_assumptions.indices.obr.per_capita.gdp"
INTEREST_INDEX = (
    "gov.economic_assumptions.indices.ons.per_capita.household_interest_income"
)
ISA_INCOME_PAIRS = [
    ("individual_savings_account_dividend_income", "dividend_income", [100, 125, 150]),
    ("non_cash_isa_cash_interest", "savings_interest_income", [100, 150, 200]),
]


def income_household(observations):
    return {
        "people": {
            "person": {
                "age": {2026: 35, 2027: 35, 2028: 35},
                **observations,
            }
        },
        "benunits": {"benunit": {"members": ["person"]}},
        "households": {"household": {"members": ["person"]}},
    }


def controlled_income_growth():
    from policyengine_uk.model_api import Scenario

    return Scenario(
        parameter_changes={
            GDP_INDEX: {"2026": 100, "2027": 125, "2028": 150},
            INTEREST_INDEX: {"2026": 100, "2027": 150, "2028": 200},
        },
        applied_before_data_load=True,
    )


@pytest.mark.parametrize("isa, ordinary, levels", ISA_INCOME_PAIRS)
@pytest.mark.parametrize("observations", ["base", "later", "zero", "absent"])
def test_new_isa_income_uses_the_ordinary_counterpart_index(
    isa, ordinary, levels, observations
):
    if observations == "absent":
        inputs = {}
    else:
        amounts = {2026: 0 if observations == "zero" else 100}
        if observations == "later":
            amounts[2027] = 300
        inputs = {isa: deepcopy(amounts), ordinary: deepcopy(amounts)}
    simulation = Simulation(
        situation=income_household(inputs), scenario=controlled_income_growth()
    )
    for year in (2028, 2027, 2026):
        if observations in ("zero", "absent"):
            expected = 0
        elif observations == "later" and year >= 2027:
            expected = 300 * levels[year - 2026] / levels[1]
        else:
            expected = 100 * levels[year - 2026] / levels[0]
        actual = simulation.calculate(isa, year).tolist()
        assert actual == pytest.approx([expected], abs=0.01)
        assert actual == pytest.approx(
            simulation.calculate(ordinary, year).tolist(), abs=0.01
        )
    if observations in ("base", "later"):
        assert simulation.calculate(isa, 2028)[0] > 100
        assert simulation.calculate(isa, 2026).tolist() == [100]
    if observations == "later":
        assert simulation.calculate(isa, 2027).tolist() == [300]


def test_uprated_isa_components_reach_income_once():
    inputs = {
        name: {2026: 100}
        for name in (
            "dividend_income",
            "individual_savings_account_dividend_income",
            "savings_interest_income",
            "non_cash_isa_cash_interest",
        )
    }
    simulation = Simulation(
        situation=income_household(inputs), scenario=controlled_income_growth()
    )
    for variable in ("market_income", "capital_income"):
        assert simulation.calculate(variable, 2027).tolist() == pytest.approx(
            [550], abs=0.01
        )
        assert simulation.calculate(variable, 2026).tolist() == pytest.approx(
            [400], abs=0.01
        )
    for variable in (
        "non_cash_isa_cash_interest",
        "individual_savings_account_interest_income",
        "tax_free_savings_income",
        "taxable_savings_interest_income",
    ):
        assert simulation.calculate(variable, 2027).tolist() == pytest.approx(
            [150], abs=0.01
        )
    assert simulation.calculate("dividend_income", 2027).tolist() == pytest.approx(
        [125], abs=0.01
    )


def test_lisa_medical_input_is_specific_to_withdrawal_charge():
    people = {}
    for number, (age, flag) in enumerate(
        ((35, None), (35, False), (35, True), (60, False))
    ):
        person = {"age": {2026: age}, "lifetime_isa_withdrawals": {2026: 2_000}}
        if flag is not None:
            person["lifetime_isa_terminally_ill"] = {2026: flag}
        people[f"person{number}"] = person
    simulation = Simulation(
        situation={
            "people": people,
            "benunits": {name: {"members": [name]} for name in people},
            "households": {name: {"members": [name]} for name in people},
        }
    )
    assert simulation.calculate("lifetime_isa_withdrawal_charge", 2026).tolist() == [
        500,
        500,
        0,
        0,
    ]
    assert "lifetime_isa_terminally_ill" in simulation.tax_benefit_system.variables
    assert "is_terminally_ill" not in simulation.tax_benefit_system.variables
