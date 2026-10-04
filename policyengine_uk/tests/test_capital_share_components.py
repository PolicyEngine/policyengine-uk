"""The means-test capital sources itemise corporate_wealth.

The lists name corporate_wealth's components and unitemised_corporate_wealth
(the part a dataset does not itemise) instead of corporate_wealth. Since the
sale-expense lists tell the components apart, itemising changes capital by
exactly rate x (trusts + ISA): that, conservation at a zero rate and the other
valuation invariants are in test_capital_valuation_properties.py.
"""

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from policyengine_uk import CountryTaxBenefitSystem, Simulation

COMPONENTS = (
    "directly_held_shares",
    "unit_and_investment_trusts",
    "stocks_and_shares_isa",
)
SHARE_LIKE_SOURCES = (*COMPONENTS, "unitemised_corporate_wealth")
SOURCE_LISTS = {
    "uc_assessable_capital": "gov.dwp.universal_credit.means_test.capital.sources",
    "housing_benefit_assessable_capital": "gov.dwp.housing_benefit.means_test.capital.sources",
    "income_support_assessable_capital": "gov.dwp.income_support.means_test.capital.sources",
    "jsa_income_assessable_capital": "gov.dwp.JSA.income.capital.sources",
    "esa_income_assessable_capital": "gov.dwp.ESA.income.capital.sources",
    "pension_credit_assessable_capital": "gov.dwp.pension_credit.income.capital.sources",
}
AGE = {"pension_credit_assessable_capital": 70}
YEAR = 2026

system = CountryTaxBenefitSystem()
amount = st.integers(min_value=0, max_value=60_000)


def _parameter(path):
    node = system.parameters
    for part in path.split("."):
        node = getattr(node, part)
    return node(f"{YEAR}-01-01")


def _capital(variable, household):
    situation = {
        "people": {"adult": {"age": {YEAR: AGE.get(variable, 30)}}},
        "benunits": {"benunit": {"members": ["adult"], "would_claim_uc": {YEAR: True}}},
        "households": {
            "household": {
                "members": ["adult"],
                **{name: {YEAR: value} for name, value in household.items()},
            }
        },
    }
    return Simulation(situation=situation).calculate(variable, YEAR)[0]


@pytest.mark.parametrize("variable", SOURCE_LISTS)
def test_lists_name_the_components_not_corporate_wealth(variable):
    sources = list(_parameter(SOURCE_LISTS[variable]))
    assert "corporate_wealth" not in sources
    assert set(SHARE_LIKE_SOURCES) <= set(sources)


@settings(max_examples=40, deadline=None)
@given(
    savings=amount,
    corporate_wealth=amount,
    components=st.tuples(amount, amount, amount),
)
def test_unitemised_corporate_wealth_is_the_floored_remainder(
    savings, corporate_wealth, components
):
    household = {"savings": savings, "corporate_wealth": corporate_wealth}
    household.update(dict(zip(COMPONENTS, components)))
    situation = {
        "people": {"adult": {"age": {YEAR: 30}}},
        "households": {
            "household": {
                "members": ["adult"],
                **{name: {YEAR: value} for name, value in household.items()},
            }
        },
    }
    residual = Simulation(situation=situation).calculate(
        "unitemised_corporate_wealth", YEAR
    )[0]
    assert residual == max(0, corporate_wealth - sum(components))
