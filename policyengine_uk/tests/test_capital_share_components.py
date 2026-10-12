"""share_like_capital replaces corporate_wealth in the means-test capital lists.

Invariants:
1. share_like_capital is corporate_wealth as supplied (any sign, any fraction)
   unless the itemised components add up to more than it by more than the
   rounding tolerance, in which case it is their sum.
2. Differential: for identical inputs that carry no components, or components
   consistent with corporate_wealth, every programme's assessable capital and
   eligibility equal those under the original lists (corporate_wealth),
   exactly, annually and monthly.
3. A household given only the components has them counted.
"""

import numpy as np
import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from policyengine_uk import CountryTaxBenefitSystem, Simulation
from policyengine_uk.variables.household.wealth.share_like_capital import (
    ABSOLUTE_TOLERANCE,
    RELATIVE_TOLERANCE,
)

COMPONENTS = (
    "directly_held_shares",
    "unit_and_investment_trusts",
    "stocks_and_shares_isa",
)
SOURCE_LISTS = {
    "uc_assessable_capital": "gov.dwp.universal_credit.means_test.capital.sources",
    "housing_benefit_assessable_capital": "gov.dwp.housing_benefit.means_test.capital.sources",
    "income_support_assessable_capital": "gov.dwp.income_support.means_test.capital.sources",
    "jsa_income_assessable_capital": "gov.dwp.JSA.income.capital.sources",
    "esa_income_assessable_capital": "gov.dwp.ESA.income.capital.sources",
    "pension_credit_assessable_capital": "gov.dwp.pension_credit.income.capital.sources",
}
YEAR = 2026
SETTINGS = settings(
    max_examples=25,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)

system = CountryTaxBenefitSystem()


def _parameter(path):
    node = system.parameters
    for part in path.split("."):
        node = getattr(node, part)
    return node(f"{YEAR}-01-01")


ORIGINAL_LISTS = {
    path: [
        "corporate_wealth" if source == "share_like_capital" else source
        for source in _parameter(path)
    ]
    for path in SOURCE_LISTS.values()
}
ORIGINAL_REFORM = {
    path: {str(YEAR): sources} for path, sources in ORIGINAL_LISTS.items()
}

money = st.floats(min_value=0, max_value=200_000, allow_nan=False, width=32)
signed_money = st.floats(min_value=-5_000, max_value=200_000, allow_nan=False, width=32)


def _situation(households):
    """One single-adult household per entry; ages alternate 30 and 70."""
    people, benunits, hhs = {}, {}, {}
    for i, assets in enumerate(households):
        people[f"p{i}"] = {"age": {YEAR: 70 if i % 2 else 30}}
        benunits[f"b{i}"] = {"members": [f"p{i}"], "would_claim_uc": {YEAR: True}}
        hhs[f"h{i}"] = {
            "members": [f"p{i}"],
            **{name: {YEAR: float(value)} for name, value in assets.items()},
        }
    return {"people": people, "benunits": benunits, "households": hhs}


def _results(households, reform=None, period=YEAR):
    sim = Simulation(situation=_situation(households), reform=reform)
    out = {v: sim.calculate(v, period) for v in SOURCE_LISTS}
    out["is_uc_eligible"] = sim.calculate("is_uc_eligible", period)
    out["share_like_capital"] = sim.calculate("share_like_capital", YEAR)
    return out


def _assert_same_as_original(households):
    for period in (YEAR, f"{YEAR}-01"):
        new = _results(households, period=period)
        old = _results(households, reform=ORIGINAL_REFORM, period=period)
        for variable in (*SOURCE_LISTS, "is_uc_eligible"):
            assert np.array_equal(new[variable], old[variable]), (variable, period)


@pytest.mark.parametrize("variable", SOURCE_LISTS)
def test_lists_name_share_like_capital_only(variable):
    sources = list(_parameter(SOURCE_LISTS[variable]))
    assert "share_like_capital" in sources
    assert "corporate_wealth" not in sources
    assert not set(COMPONENTS) & set(sources)


@SETTINGS
@given(
    st.lists(
        st.tuples(signed_money, st.tuples(money, money, money), st.booleans()),
        min_size=1,
        max_size=40,
    )
)
def test_share_like_capital_keeps_the_supplied_aggregate(rows):
    households = []
    for corporate_wealth, components, itemise in rows:
        assets = {"corporate_wealth": corporate_wealth}
        if itemise:
            assets |= dict(zip(COMPONENTS, components))
        households.append(assets)
    got = _results(households)["share_like_capital"]
    for value, assets in zip(got, households):
        cw = np.float32(assets["corporate_wealth"])
        itemised = np.float32(sum(np.float32(assets.get(c, 0)) for c in COMPONENTS))
        tolerance = RELATIVE_TOLERANCE * abs(cw) + ABSOLUTE_TOLERANCE
        expected = itemised if itemised > 0 and itemised > cw + tolerance else cw
        assert value == pytest.approx(expected, rel=1e-6, abs=1e-3)
        if not (itemised > 0 and itemised > cw + tolerance):
            assert value == cw  # exactly the supplied aggregate


@SETTINGS
@given(
    st.lists(
        st.tuples(money, signed_money, st.tuples(money, money, money), st.booleans()),
        min_size=1,
        max_size=30,
    )
)
def test_capital_matches_the_original_lists(rows):
    """Unsplit, or split consistently: identical to listing corporate_wealth."""
    households = []
    for savings, corporate_wealth, components, split in rows:
        assets = {"savings": savings, "corporate_wealth": corporate_wealth}
        if split:
            assets |= dict(zip(COMPONENTS, components))
            assets["corporate_wealth"] = float(sum(components))
        households.append(assets)
    _assert_same_as_original(households)


def test_float32_rounding_at_the_limit_keeps_eligibility():
    """Components whose float32 sum overshoots £16,000 by a fraction of a penny."""
    households = [
        {
            "savings": 0,
            "corporate_wealth": 16_000,
            "directly_held_shares": 6_744.81,
            "unit_and_investment_trusts": 6_581.24,
            "stocks_and_shares_isa": 2_673.95,
        },
        {"savings": 6_001, "corporate_wealth": -2},
        {"savings": 15_999.99, "corporate_wealth": 0.01},
    ]
    _assert_same_as_original(households)
    assert _results(households)["share_like_capital"][0] == 16_000


def test_components_alone_are_counted():
    households = [
        {
            "savings": 1_000,
            "directly_held_shares": 4_000,
            "unit_and_investment_trusts": 3_000,
            "stocks_and_shares_isa": 5_000,
        }
    ]
    got = _results(households)
    assert got["share_like_capital"][0] == 12_000
    assert got["uc_assessable_capital"][0] == 13_000
