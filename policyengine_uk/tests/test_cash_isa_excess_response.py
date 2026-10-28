"""The opt-in response to cash above the cash ISA limit changes tax, not income.

A basic-rate taxpayer who already uses their personal savings allowance puts
GBP 20,000 into cash ISAs in fiscal 2027-28. With all of the GBP 8,000 above
the GBP 12,000 limit held in taxable savings, its interest at the default
rate is taxed at the savings basic rate. Restoring a GBP 20,000 cash limit
removes that tax, which is how a reversal of the limit scores.
"""

import pytest

from policyengine_uk import CountryTaxBenefitSystem, Simulation

YEAR = 2027
RESPONSE = "gov.contrib.behavioral_responses.cash_isa_excess"
SPAN = f"{YEAR}-01-01.{YEAR}-12-31"
TAXABLE = {f"{RESPONSE}.taxable_savings_share": {SPAN: 1}}
SITUATION = {
    "people": {
        "saver": {
            "age": {YEAR: 40},
            "employment_income": {YEAR: 30_000},
            "savings_interest_income": {YEAR: 1_000},
            "cash_isa_subscriptions": {YEAR: 20_000},
        }
    },
    "benunits": {"benunit": {"members": ["saver"]}},
    "households": {"household": {"members": ["saver"], "region": "LONDON"}},
}


def _calculate(reform, variable):
    simulation = Simulation(situation=SITUATION, reform=reform)
    return float(simulation.calculate(variable, YEAR)[0])


def test_response_taxes_the_displaced_interest_without_adding_income():
    parameters = CountryTaxBenefitSystem().parameters
    rate = parameters.get_child(f"{RESPONSE}.interest_rate")(f"{YEAR}-04-30")
    savings_basic_rate = parameters.gov.hmrc.income_tax.rates.savings.basic(
        f"{YEAR}-04-30"
    )
    expected_tax = 8_000 * rate * savings_basic_rate

    tax_change = _calculate(TAXABLE, "income_tax") - _calculate({}, "income_tax")
    assert tax_change == pytest.approx(expected_tax, abs=0.01)
    for variable in ("household_market_income", "household_gross_income"):
        assert _calculate(TAXABLE, variable) == pytest.approx(
            _calculate({}, variable), abs=0.01
        ), variable


def test_restoring_the_cash_limit_removes_the_tax_on_displaced_interest():
    restored = {
        **TAXABLE,
        "gov.hmrc.isa.cash.subscription_limit": {SPAN: 20_000},
    }
    assert _calculate(restored, "cash_isa_excess_savings_interest") == 0
    assert _calculate(restored, "income_tax") == pytest.approx(
        _calculate({}, "income_tax"), abs=0.01
    )


def test_shares_above_one_are_rejected():
    reform = {
        f"{RESPONSE}.stocks_and_shares_isa_share": {SPAN: 0.6},
        f"{RESPONSE}.taxable_savings_share": {SPAN: 0.6},
    }
    with pytest.raises(ValueError, match="sum to at most one"):
        _calculate(reform, "cash_isa_excess_savings_interest")
