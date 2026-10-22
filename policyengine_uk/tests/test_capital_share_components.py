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
5. A disregarded company holding (UC reg 77(2)) leaves the UC capital pool
   from the part with sale expenses, whether it was entered within
   corporate_wealth or as directly held shares.
6. The exempt list exists from the first date any capital list does.
"""

import numpy as np
import pytest
from hypothesis import HealthCheck, example, given, settings
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


def _node(path):
    node = system.parameters
    for part in path.split("."):
        node = getattr(node, part)
    return node


def _parameter(path):
    return _node(path)(f"{YEAR}-01-01")


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

# Pounds and pence, as a dataset stores them in float64; the engine rounds
# each to float32, which is the rounding the tolerance has to absorb.
money = st.integers(min_value=0, max_value=20_000_000).map(lambda pence: pence / 100)
signed_money = st.integers(min_value=-500_000, max_value=20_000_000).map(
    lambda pence: pence / 100
)


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
# Subtracting trusts and ISA one at a time leaves £0.015625 here; grouped, nil.
@example([(399_999.984375, (0.0, 200_000.0, 199_999.984375), True)])
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
        if itemised > 0 and itemised - cw > tolerance:
            assert share_like == itemised
        else:
            assert share_like == cw
        if itemised == 0:
            assert got[WITH][i] == share_like and got[WITHOUT][i] == 0
        else:
            assert got[WITH][i] == max(np.float32(0), np.float32(share_like - exempt))
            assert got[WITHOUT][i] == np.float32(share_like - got[WITH][i])


def test_float32_grouping_of_the_exempt_holdings():
    """Trusts and ISA summed first: corporate_wealth of £399,999.984375 and
    £200,000 + £199,999.984375 of exempt holdings both round to £400,000 in
    float32, so the part with sale expenses is nil; subtracting the two one at
    a time would leave £0.015625."""
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


def test_the_exempt_list_starts_with_the_first_capital_list():
    exempt = system.parameters.gov.dwp.share_like_capital.without_sale_expenses
    first = min(
        min(entry.instant_str for entry in _node(f"{node}.sources").values_list)
        for node in NODES.values()
    )
    assert first == "1996-10-07"
    assert min(entry.instant_str for entry in exempt.values_list) == first


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
    # A projected year as well, where the inputs are uprated.
    for period in (YEAR, f"{YEAR}-01", YEAR + 1, f"{YEAR + 1}-01"):
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
    # Uprated separately in float32, the components still round to their
    # aggregate in a projected year, so share-like capital is the aggregate.
    sim = Simulation(situation=_situation(households, age=30))
    for year in (YEAR, YEAR + 1):
        assert np.array_equal(
            sim.calculate("share_like_capital", year),
            sim.calculate("corporate_wealth", year),
        ), year


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


def test_a_component_penny_at_the_limit_counts():
    """A penny of shares with no corporate_wealth counts like a penny of it."""
    as_component = [{"savings": 16_000, "directly_held_shares": 0.01}]
    as_aggregate = [{"savings": 16_000, "corporate_wealth": 0.01}]
    for period in (YEAR, f"{YEAR}-01"):
        component = _results(as_component, period=period, age=30)
        aggregate = _results(as_aggregate, period=period, age=30)
        assert component["share_like_capital"][0] == np.float32(0.01)
        for variable in (*NODES, "is_uc_eligible"):
            assert np.array_equal(component[variable], aggregate[variable]), variable
        assert not component["is_uc_eligible"][0]


def test_a_genuine_excess_over_the_aggregate_counts():
    """Ten pence of components above the aggregate is a holding, not rounding."""
    households = [
        {
            "corporate_wealth": 16_000,
            "directly_held_shares": 10_000.10,
            "stocks_and_shares_isa": 6_000,
        }
    ]
    assert _results(households)["share_like_capital"][0] == np.float32(16_000.10)


def test_float32_rounding_at_the_limit_keeps_the_aggregate():
    """Components whose float32 sum overshoots £16,000 by a fraction of a
    penny keep the aggregate; an unitemised penny at the limit counts as
    before itemising."""
    split = [
        {
            "corporate_wealth": 16_000,
            "directly_held_shares": 6_744.81,
            "unit_and_investment_trusts": 6_581.24,
            "stocks_and_shares_isa": 2_673.95,
        }
    ]
    itemised = np.float32(
        np.float32(np.float32(6_744.81) + np.float32(6_581.24)) + np.float32(2_673.95)
    )
    assert itemised > np.float32(16_000)
    assert _results(split)["share_like_capital"][0] == 16_000
    unitemised = [
        {"savings": 15_999.99, "corporate_wealth": 0.01},
        {"savings": 6_001, "corporate_wealth": -2},
    ]
    for period in (YEAR, f"{YEAR}-01"):
        new = _results(unitemised, period=period)
        old = _results(unitemised, reform=UNITEMISED_REFORM, period=period)
        for variable in (*NODES, "is_uc_eligible"):
            assert np.array_equal(new[variable], old[variable]), (variable, period)


def test_one_unit_of_float32_rounding_above_a_power_of_two_keeps_the_aggregate():
    """Pence-valued components whose float32 sum lands one unit in the last place
    (£0.00195) above £16,384.01: more than 1e-7 of the value, less than 1e-6."""
    households = [
        {
            "corporate_wealth": 16_384.01,
            "directly_held_shares": 16_015.98,
            "unit_and_investment_trusts": 286.98,
            "stocks_and_shares_isa": 81.05,
        }
    ]
    itemised = np.float32(
        np.float32(np.float32(16_015.98) + np.float32(286.98)) + np.float32(81.05)
    )
    assert itemised - np.float32(16_384.01) == np.float32(0.001953125)
    assert _results(households)["share_like_capital"][0] == np.float32(16_384.01)


def test_a_disregarded_company_holding_leaves_the_part_with_sale_expenses():
    """UC reg 77(2): the owner's £30,000 holding leaves the pool at the 90% its
    shares are counted at, whether it was entered within corporate_wealth or
    as directly held shares. Two unreported adults share £10,000 of savings."""
    from policyengine_uk.variables.gov.dwp.universal_credit.household_uc_company_holding_pool_scale import (
        HOLDINGS_SOURCE,
    )

    node = NODES["uc_assessable_capital"]
    assert HOLDINGS_SOURCE in _parameter(f"{node}.sources")
    assert HOLDINGS_SOURCE in _parameter(f"{node}.sale_expenses.sources")
    for shares in ({"corporate_wealth": 30_000}, {"directly_held_shares": 30_000}):
        situation = {
            "people": {
                "owner": {
                    "age": {YEAR: 40},
                    "stands_as_sole_owner_or_partner_of_company": {YEAR: True},
                    "owned_company_carries_on_trade": {YEAR: True},
                    "owned_company_holding_value": {YEAR: 30_000},
                },
                "lodger": {"age": {YEAR: 30}},
            },
            "benunits": {
                "owner_unit": {"members": ["owner"]},
                "lodger_unit": {"members": ["lodger"]},
            },
            "households": {
                "household": {
                    "members": ["owner", "lodger"],
                    "savings": {YEAR: 10_000},
                    **{name: {YEAR: value} for name, value in shares.items()},
                }
            },
        }
        sim = Simulation(situation=situation)
        assert sim.calculate("household_uc_company_holding_pool_scale", YEAR)[0] == 1
        # The pool counts the shares at 90%, and the holding leaves it at that.
        assert sim.calculate("household_uc_pool_company_holdings", YEAR)[0] == 27_000
        assert list(sim.calculate("uc_assessable_capital", YEAR)) == [5_000, 5_000]
