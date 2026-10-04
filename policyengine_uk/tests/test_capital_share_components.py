"""Itemising corporate_wealth never changes a household's capital total.

The means-test capital sources list corporate_wealth's components and
unitemised_corporate_wealth (the part a dataset does not itemise) instead of
corporate_wealth. With no valuation rule that tells the components apart, every
programme's assessable capital must equal what it is when the same holdings are
entered as one unitemised corporate_wealth.
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


@pytest.mark.parametrize("variable", SOURCE_LISTS)
@settings(max_examples=15, deadline=None)
@given(
    savings=amount,
    corporate_wealth=amount,
    components=st.tuples(amount, amount, amount),
)
def test_itemising_never_changes_capital(
    variable, savings, corporate_wealth, components
):
    """Split holdings count exactly as max(corporate_wealth, their sum) does."""
    itemised = {"savings": savings, "corporate_wealth": corporate_wealth}
    itemised.update(dict(zip(COMPONENTS, components)))
    unitemised = {
        "savings": savings,
        "corporate_wealth": max(corporate_wealth, sum(components)),
    }
    assert _capital(variable, itemised) == pytest.approx(
        _capital(variable, unitemised), abs=1e-2
    )
