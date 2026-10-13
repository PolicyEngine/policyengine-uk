"""Share-like capital in the means tests, itemised and valued by asset type.

The capital lists name share_like_capital's two parts:
share_like_capital_with_sale_expenses (directly held shares, and all of an
unitemised corporate_wealth), which the sale-expense lists value less 10%, and
share_like_capital_without_sale_expenses (unit and investment trusts, stocks
and shares ISAs), valued in full.

Invariants:
1. share_like_capital is corporate_wealth as supplied (any sign, any fraction)
   unless the itemised components exceed it beyond the rounding tolerance, in
   which case it is their sum.
2. With no itemised holdings, the part with sale expenses is all of
   share_like_capital and the other part is exactly nil; otherwise the part
   with sale expenses is share_like_capital less trusts and ISAs, floored at
   nil, and the two parts add up to share_like_capital.
3. Differential: for identical unitemised inputs, every programme's assessable
   capital and UC eligibility equal those under the lists before itemising
   (corporate_wealth valued less 10%), exactly, annually and monthly.
4. Split effect: a consistent split raises a working-age single adult's UC
   capital by 10% of trusts plus ISAs, against the unitemised lists.
"""

import numpy as np
import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from policyengine_uk import CountryTaxBenefitSystem, Simulation
from policyengine_uk.variables.household.wealth.share_like_capital import (
    RELATIVE_TOLERANCE,
)

COMPONENTS = (
    "directly_held_shares",
    "unit_and_investment_trusts",
    "stocks_and_shares_isa",
)
WITH, WITHOUT = (
    "share_like_capital_with_sale_expenses",
    "share_like_capital_without_sale_expenses",
)
LEGAL_RATE = 0.1
NODES = {
    "uc_assessable_capital": "gov.dwp.universal_credit.means_test.capital",
    "housing_benefit_assessable_capital": "gov.dwp.housing_benefit.means_test.capital",
    "income_support_assessable_capital": "gov.dwp.income_support.means_test.capital",
    "jsa_income_assessable_capital": "gov.dwp.JSA.income.capital",
    "esa_income_assessable_capital": "gov.dwp.ESA.income.capital",
    "pension_credit_assessable_capital": "gov.dwp.pension_credit.income.capital",
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


def _unitemised(sources):
    """The list before itemising: corporate_wealth where the share parts are."""
    out = []
    for source in sources:
        if source == WITHOUT:
            continue
        out.append("corporate_wealth" if source == WITH else source)
    return out


UNITEMISED_REFORM = {
    f"{node}.{name}": {str(YEAR): _unitemised(_parameter(f"{node}.{name}"))}
    for node in NODES.values()
    for name in ("sources", "sale_expenses.sources")
}

money = st.floats(min_value=0, max_value=200_000, allow_nan=False, width=32)
signed_money = st.floats(min_value=-5_000, max_value=200_000, allow_nan=False, width=32)


def _situation(households, age=None):
    people, benunits, hhs = {}, {}, {}
    for i, assets in enumerate(households):
        people[f"p{i}"] = {"age": {YEAR: age or (70 if i % 2 else 30)}}
        benunits[f"b{i}"] = {"members": [f"p{i}"], "would_claim_uc": {YEAR: True}}
        hhs[f"h{i}"] = {
            "members": [f"p{i}"],
            **{name: {YEAR: float(value)} for name, value in assets.items()},
        }
    return {"people": people, "benunits": benunits, "households": hhs}


def _results(households, reform=None, period=YEAR, age=None):
    sim = Simulation(situation=_situation(households, age), reform=reform)
    out = {v: sim.calculate(v, period) for v in NODES}
    out["is_uc_eligible"] = sim.calculate("is_uc_eligible", period)
    for v in ("share_like_capital", WITH, WITHOUT):
        out[v] = sim.calculate(v, YEAR)
    return out


@pytest.mark.parametrize("variable", NODES)
def test_lists_name_the_two_parts(variable):
    sources = list(_parameter(f"{NODES[variable]}.sources"))
    sale = list(_parameter(f"{NODES[variable]}.sale_expenses.sources"))
    assert WITH in sources and WITHOUT in sources
    assert not {"corporate_wealth", "share_like_capital", *COMPONENTS} & set(sources)
    assert WITH in sale and WITHOUT not in sale
    assert not {"corporate_wealth", *COMPONENTS} & set(sale)
    without = set(_parameter("gov.dwp.share_like_capital.without_sale_expenses"))
    assert without == {"unit_and_investment_trusts", "stocks_and_shares_isa"}


@SETTINGS
@given(
    st.lists(
        st.tuples(signed_money, st.tuples(money, money, money), st.booleans()),
        min_size=1,
        max_size=40,
    )
)
def test_share_like_capital_and_its_parts(rows):
    households = []
    for corporate_wealth, components, itemise in rows:
        assets = {"corporate_wealth": corporate_wealth}
        if itemise:
            assets |= dict(zip(COMPONENTS, components))
        households.append(assets)
    got = _results(households)
    for i, assets in enumerate(households):
        cw = np.float32(assets["corporate_wealth"])
        values = [np.float32(assets.get(c, 0)) for c in COMPONENTS]
        # The engine's float32 grouping: components added left to right, the
        # exempt holdings summed before they are subtracted.
        itemised = np.float32(np.float32(values[0] + values[1]) + values[2])
        exempt = np.float32(values[1] + values[2])
        tolerance = RELATIVE_TOLERANCE * max(abs(cw), itemised)
        share_like = got["share_like_capital"][i]
        if itemised > 0 and itemised > cw + tolerance:
            assert share_like == itemised
        else:
            assert share_like == cw
        if itemised == 0:
            assert got[WITH][i] == share_like and got[WITHOUT][i] == 0
        else:
            assert got[WITH][i] == max(np.float32(0), np.float32(share_like - exempt))
            assert got[WITHOUT][i] == np.float32(share_like - got[WITH][i])


def test_float32_grouping_of_the_exempt_holdings():
    """Trusts and ISA summed first: £400,000 less £399,999.98 rounds to nil."""
    households = [
        {
            "corporate_wealth": 399_999.984375,
            "unit_and_investment_trusts": 200_000,
            "stocks_and_shares_isa": 199_999.984375,
        }
    ]
    got = _results(households)
    assert got[WITH][0] == 0


def test_an_empty_exempt_list_values_everything_less_10_percent():
    """A ruling that every share-like holding takes the 10% is a parameter edit."""
    reform = {"gov.dwp.share_like_capital.without_sale_expenses": {str(YEAR): []}}
    households = [
        {"savings": 1_000, "corporate_wealth": 12_000},
        {
            "savings": 1_000,
            "directly_held_shares": 4_000,
            "unit_and_investment_trusts": 3_000,
            "stocks_and_shares_isa": 5_000,
        },
    ]
    got = _results(households, reform=reform, age=30)
    assert list(got[WITH]) == [12_000, 12_000]
    assert list(got[WITHOUT]) == [0, 0]
    # £1,000 + 90% of £12,000 either way.
    assert got["uc_assessable_capital"] == pytest.approx([11_800, 11_800])


@pytest.mark.parametrize(
    "variable", ["income_support_assessable_capital", "jsa_income_assessable_capital"]
)
def test_legacy_capital_before_universal_credit(variable):
    """2012: the legacy lists apply, and so does the exempt list (from 1996)."""
    situation = _situation([{"savings": 1_000, "corporate_wealth": 12_000}], age=30)
    for entity in situation.values():
        for name, values in entity.items():
            for key, by_year in list(values.items()):
                if isinstance(by_year, dict) and YEAR in by_year:
                    values[key] = {2012: by_year[YEAR]}
    capital = Simulation(situation=situation).calculate(variable, 2012)[0]
    assert capital == pytest.approx(11_800)


@SETTINGS
@given(
    st.lists(st.tuples(money, signed_money), min_size=1, max_size=30),
)
def test_unitemised_inputs_match_the_lists_before_itemising(rows):
    households = [{"savings": s, "corporate_wealth": cw} for s, cw in rows]
    households += [
        {"savings": 6_001, "corporate_wealth": -2},
        {"savings": 0, "corporate_wealth": 17_777.78},  # 90% is £16,000.002
    ]
    for period in (YEAR, f"{YEAR}-01"):
        new = _results(households, period=period)
        old = _results(households, reform=UNITEMISED_REFORM, period=period)
        for variable in (*NODES, "is_uc_eligible"):
            assert np.array_equal(new[variable], old[variable]), (variable, period)


@SETTINGS
@given(
    st.lists(st.tuples(money, st.tuples(money, money, money)), min_size=1, max_size=30)
)
def test_a_consistent_split_exempts_trusts_and_isas(rows):
    households = [
        {
            "savings": savings,
            "corporate_wealth": float(sum(components)),
            **dict(zip(COMPONENTS, components)),
        }
        for savings, components in rows
    ]
    new = _results(households, age=30)
    old = _results(households, reform=UNITEMISED_REFORM, age=30)
    for i, (_, (_, trusts, isa)) in enumerate(rows):
        exempt = np.float32(trusts) + np.float32(isa)
        assert new["uc_assessable_capital"][i] - old["uc_assessable_capital"][
            i
        ] == pytest.approx(LEGAL_RATE * exempt, rel=1e-5, abs=0.05)


def test_components_alone_are_valued_by_type():
    households = [
        {
            "savings": 1_000,
            "directly_held_shares": 4_000,
            "unit_and_investment_trusts": 3_000,
            "stocks_and_shares_isa": 5_000,
        }
    ]
    got = _results(households, age=30)
    assert got["share_like_capital"][0] == 12_000
    assert got[WITH][0] == 4_000 and got[WITHOUT][0] == 8_000
    # £1,000 + 90% of £4,000 + £3,000 + £5,000.
    assert got["uc_assessable_capital"][0] == pytest.approx(12_600)
