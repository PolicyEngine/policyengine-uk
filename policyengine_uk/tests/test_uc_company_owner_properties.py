"""Property-based tests for Universal Credit's company owner rule.

The Universal Credit Regulations 2013 reg. 77 treat a person who stands in a
position analogous to a sole owner or partner of a company carrying on a trade
or a property business as that sole owner or partner: their holding in the
company is disregarded and they are treated as possessing the company's
capital (or their share of it), less assets used wholly and exclusively for a
trade while they work in it (reg. 77(2), (3)(a)); a trading company's income
is their self-employed earnings, in addition to any pay from it (reg. 77(3)(b),
(4)); and if the trade is their main employment the minimum income floor
applies (reg. 77(3)(c)). None of it applies where their income from the
company is employed earnings under the intermediaries rules from their main
employment (reg. 77(5)).

Invariants, for any generated benefit units:

1. Inert: when the person is not a company's sole owner or partner, or reg.
   77(5) applies, or the company carries on neither a trade nor a property
   business, no company fact changes Universal Credit, its capital or its
   earned income.
2. Capital identity: assessable capital equals the capital without the rule
   less the owners' holdings (floored at zero), plus each owner's company
   capital net of trade assets disregarded while they work in the trade.
3. Conservation: in a household of two benefit units, the units' assessable
   capital sums to the household's capital less the owners' holdings
   (floored at zero), plus the owners' company capital.
4. Earnings identity: without the floor, gross earned income is pay plus
   self-employment profit plus the company income share (a loss counts as
   nil) for a trading company, and nothing for a property-only company.
5. Floor: a trading-company owner whose main employment it is and who is not
   in a start-up period has earned income of at least the floor.
6. Monotone: Universal Credit is non-increasing in the company income share
   and in the company's capital, and non-decreasing in the value of the
   disregarded holding and of disregarded trade assets.

The strategies make most adults owners of a trading company, keep capital
mostly under the £16,000 limit and put earnings around the floor, so each
property is exercised rather than satisfied vacuously.
"""

import numpy as np
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation

YEAR = 2026
PROPERTY_SETTINGS = settings(
    max_examples=10,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)
COMPANY_FACTS = [
    "stands_as_sole_owner_or_partner_of_company",
    "owned_company_carries_on_trade",
    "owned_company_carries_on_property_business",
    "owned_company_intermediary_earnings_chapter",
    "owned_company_intermediary_earnings_from_main_employment",
    "owned_company_is_main_employment",
    "is_engaged_in_owned_company_trade",
    "owned_company_income_share",
    "owned_company_capital",
    "owned_company_trade_assets",
    "owned_company_holding_value",
]
VARIABLES = [
    "universal_credit",
    "uc_assessable_capital",
    "uc_earned_income",
]
PERSON_VARIABLES = [
    "uc_mif_capped_earned_income",
    "uc_minimum_income_floor",
    "uc_mif_applies",
]

money = st.floats(0, 30_000, allow_nan=False, allow_infinity=False)
company_income = st.floats(-20_000, 40_000, allow_nan=False, allow_infinity=False)
small_capital = st.one_of(st.just(0.0), st.floats(0, 8_000))


def close(a, b):
    # Simulation outputs are float32: allow for its rounding at these sizes.
    return abs(a - b) <= 1e-2 + 1e-6 * abs(b)


@st.composite
def companies(draw):
    company_capital = draw(st.one_of(st.just(0.0), st.floats(0, 12_000)))
    return dict(
        stands_as_sole_owner_or_partner_of_company=draw(
            st.sampled_from([True, True, True, False])
        ),
        owned_company_carries_on_trade=draw(st.sampled_from([True, True, True, False])),
        owned_company_carries_on_property_business=draw(
            st.sampled_from([False, False, True])
        ),
        owned_company_intermediary_earnings_chapter=draw(
            st.sampled_from(["NONE"] * 5 + ["CHAPTER_8", "CHAPTER_9", "CHAPTER_10"])
        ),
        owned_company_intermediary_earnings_from_main_employment=draw(st.booleans()),
        owned_company_is_main_employment=draw(st.booleans()),
        is_engaged_in_owned_company_trade=draw(st.booleans()),
        owned_company_income_share=draw(company_income),
        owned_company_capital=company_capital,
        owned_company_trade_assets=draw(st.floats(0, 1)) * company_capital,
        owned_company_holding_value=draw(small_capital),
    )


@st.composite
def adults(draw):
    return dict(
        age=draw(st.integers(25, 60)),
        employment_income=draw(st.one_of(st.just(0.0), money)),
        self_employment_income=draw(st.one_of(st.just(0.0), st.floats(0, 15_000))),
        uc_is_in_startup_period=draw(st.sampled_from([False, False, True])),
        company=draw(companies()),
    )


@st.composite
def units(draw):
    return dict(
        adults=draw(st.lists(adults(), min_size=1, max_size=2)),
        children=draw(st.integers(0, 2)),
        rent=draw(st.floats(0, 15_000)),
        savings=draw(small_capital),
        corporate_wealth=draw(small_capital),
    )


def situation(variants):
    """One benefit unit per (unit, company-fact overrides) pair."""
    people, benunits, households = {}, {}, {}
    for i, (unit, overrides) in enumerate(variants):
        names = []
        for j, adult in enumerate(unit["adults"]):
            name = f"p{i}_{j}"
            facts = {**adult["company"], **overrides.get(j, {})}
            people[name] = {
                "age": {YEAR: adult["age"]},
                "employment_income": {YEAR: adult["employment_income"]},
                "self_employment_income": {YEAR: adult["self_employment_income"]},
                "uc_is_in_startup_period": {YEAR: adult["uc_is_in_startup_period"]},
                **{k: {YEAR: v} for k, v in facts.items()},
            }
            names.append(name)
        for k in range(unit["children"]):
            name = f"c{i}_{k}"
            people[name] = {"age": {YEAR: 5 + k}}
            names.append(name)
        benunits[f"b{i}"] = {"members": names, "would_claim_uc": {YEAR: True}}
        households[f"h{i}"] = {
            "members": names,
            "tenure_type": {YEAR: "RENT_PRIVATELY"},
            "rent": {YEAR: unit["rent"]},
            "savings": {YEAR: unit["savings"]},
            "corporate_wealth": {YEAR: unit["corporate_wealth"]},
        }
    return {"people": people, "benunits": benunits, "households": households}


def calculate(variants):
    sim = Simulation(situation=situation(variants))
    out = {v: np.asarray(sim.calculate(v, YEAR)) for v in VARIABLES}
    for v in PERSON_VARIABLES:
        out[v] = np.asarray(sim.calculate(v, YEAR))
    for v in COMPANY_FACTS + [
        "employment_income",
        "self_employment_income",
        "uc_is_in_startup_period",
        "uc_company_owner_treatment_applies",
    ]:
        out[v] = np.asarray(sim.calculate(v, YEAR))
    # People are laid out unit by unit; record each adult's position.
    positions, cursor = [], 0
    for unit, _ in variants:
        positions.append(list(range(cursor, cursor + len(unit["adults"]))))
        cursor += len(unit["adults"]) + unit["children"]
    out["adult_positions"] = positions
    return out


def _empty(value):
    if isinstance(value, bool):
        return False
    if isinstance(value, str):
        return "NONE"
    return 0.0


def no_company(unit):
    return {
        j: {k: _empty(v) for k, v in adult["company"].items()}
        for j, adult in enumerate(unit["adults"])
    }


def applies(company):
    return (
        company["stands_as_sole_owner_or_partner_of_company"]
        and (
            company["owned_company_carries_on_trade"]
            or company["owned_company_carries_on_property_business"]
        )
        and not (
            # Reg. 77(5) as in force from 28 November 2018.
            company["owned_company_intermediary_earnings_chapter"] != "NONE"
            and company["owned_company_intermediary_earnings_from_main_employment"]
        )
    )


def company_capital_of(company):
    """Capital treated as possessed under reg. 77(2), net of 77(3)(a)."""
    engaged = (
        company["is_engaged_in_owned_company_trade"]
        or company["owned_company_is_main_employment"]
    )
    disregarded = (
        company["owned_company_trade_assets"]
        if company["owned_company_carries_on_trade"] and engaged
        else 0.0
    )
    return max(0.0, company["owned_company_capital"] - disregarded)


@PROPERTY_SETTINGS
@given(st.lists(units(), min_size=2, max_size=4))
def test_rule_is_inert_when_it_does_not_apply(unit_list):
    # Force every adult outside reg. 77 in one of three ways, then compare
    # with the same units carrying no company facts at all.
    variants, baselines = [], []
    for i, unit in enumerate(unit_list):
        excluded = {}
        for j, adult in enumerate(unit["adults"]):
            way = (i + j) % 3
            if way == 0:
                excluded[j] = {"stands_as_sole_owner_or_partner_of_company": False}
            elif way == 1:
                excluded[j] = {
                    "owned_company_intermediary_earnings_chapter": "CHAPTER_10",
                    "owned_company_intermediary_earnings_from_main_employment": True,
                }
            else:
                excluded[j] = {
                    "owned_company_carries_on_trade": False,
                    "owned_company_carries_on_property_business": False,
                }
        variants.append((unit, excluded))
        baselines.append((unit, no_company(unit)))
    got, base = calculate(variants), calculate(baselines)
    assert not got["uc_company_owner_treatment_applies"].any()
    for v in VARIABLES + ["uc_mif_capped_earned_income", "uc_mif_applies"]:
        np.testing.assert_allclose(got[v], base[v], rtol=0, atol=1e-6, err_msg=v)


@PROPERTY_SETTINGS
@given(st.lists(units(), min_size=2, max_size=4))
def test_capital_and_earnings_identities(unit_list):
    got = calculate([(u, {}) for u in unit_list])
    base = calculate([(u, no_company(u)) for u in unit_list])
    for i, unit in enumerate(unit_list):
        holdings, company_capital = 0.0, 0.0
        for j, adult in enumerate(unit["adults"]):
            c = adult["company"]
            k = got["adult_positions"][i][j]
            assert got["uc_company_owner_treatment_applies"][k] == applies(c)
            if applies(c):
                holdings += c["owned_company_holding_value"]
                company_capital += company_capital_of(c)
            # Earnings identity, compared before the floor.
            company_earnings = (
                max(0.0, c["owned_company_income_share"])
                if applies(c) and c["owned_company_carries_on_trade"]
                else 0.0
            )
            gross = (
                adult["employment_income"]
                + adult["self_employment_income"]
                + company_earnings
            )
            capped = got["uc_mif_capped_earned_income"][k]
            if got["uc_mif_applies"][k]:
                floor = got["uc_minimum_income_floor"][k]
                assert close(capped, max(gross, floor))
            else:
                assert close(capped, gross)
            # Floor: reg. 77(3)(c) with reg. 62(5).
            trade_main = (
                applies(c)
                and c["owned_company_carries_on_trade"]
                and c["owned_company_is_main_employment"]
            )
            if trade_main and not adult["uc_is_in_startup_period"]:
                assert got["uc_mif_applies"][k]
                assert capped >= got["uc_minimum_income_floor"][k] - 1e-2
            if adult["uc_is_in_startup_period"]:
                assert not got["uc_mif_applies"][k]
        expected = (
            max(0.0, base["uc_assessable_capital"][i] - holdings) + company_capital
        )
        assert close(got["uc_assessable_capital"][i], expected)


def _owner(unit, **facts):
    """Make the first adult a sole owner of a trading company."""
    company = {
        "stands_as_sole_owner_or_partner_of_company": True,
        "owned_company_carries_on_trade": True,
        "owned_company_intermediary_earnings_chapter": "NONE",
        **facts,
    }
    return {0: company}


@PROPERTY_SETTINGS
@given(
    st.lists(units(), min_size=1, max_size=3),
    st.floats(1, 30_000),
    st.floats(1, 30_000),
)
def test_universal_credit_monotone_in_company_facts(unit_list, bump, asset_bump):
    variants = []
    for unit in unit_list:
        c = unit["adults"][0]["company"]
        low = _owner(unit)
        variants += [
            (unit, low),
            (
                unit,
                _owner(
                    unit,
                    owned_company_income_share=c["owned_company_income_share"] + bump,
                ),
            ),
            (
                unit,
                _owner(unit, owned_company_capital=c["owned_company_capital"] + bump),
            ),
            (
                unit,
                _owner(
                    unit,
                    owned_company_holding_value=c["owned_company_holding_value"] + bump,
                ),
            ),
            (
                unit,
                _owner(
                    unit,
                    is_engaged_in_owned_company_trade=True,
                    owned_company_capital=c["owned_company_capital"] + asset_bump,
                    owned_company_trade_assets=c["owned_company_trade_assets"]
                    + asset_bump,
                ),
            ),
            (unit, _owner(unit, is_engaged_in_owned_company_trade=True)),
        ]
    uc = calculate(variants)["universal_credit"].reshape(-1, 6)
    tol = 1e-6
    base, more_income, more_capital, more_holding, more_assets, engaged = uc.T
    assert (more_income <= base + tol).all()
    assert (more_capital <= base + tol).all()
    assert (more_holding >= base - tol).all()
    # Extra capital that is itself a disregarded trade asset changes nothing
    # once the owner works in the trade.
    np.testing.assert_allclose(more_assets, engaged, rtol=0, atol=1e-6)


@PROPERTY_SETTINGS
@given(st.lists(units(), min_size=1, max_size=3), money)
def test_property_company_gives_no_earnings(unit_list, share):
    variants = []
    for unit in unit_list:
        facts = dict(
            owned_company_carries_on_trade=False,
            owned_company_carries_on_property_business=True,
        )
        variants += [
            (
                unit,
                _owner(
                    unit,
                    **facts,
                    owned_company_income_share=0.0,
                    owned_company_is_main_employment=False,
                ),
            ),
            (
                unit,
                _owner(
                    unit,
                    **facts,
                    owned_company_income_share=share,
                    owned_company_is_main_employment=True,
                ),
            ),
        ]
    got = calculate(variants)
    for v in ["universal_credit", "uc_earned_income"]:
        a, b = got[v].reshape(-1, 2).T
        np.testing.assert_allclose(a, b, rtol=0, atol=1e-6, err_msg=v)


@PROPERTY_SETTINGS
@given(st.lists(st.tuples(units(), units()), min_size=1, max_size=3))
def test_household_capital_is_conserved_across_benefit_units(pairs):
    # Each household holds two benefit units: the first unit's adults and the
    # second's, with the first unit's savings and corporate wealth. No unit
    # reports its own capital, so the household pool is shared by adults.
    people, benunits, households = {}, {}, {}
    expected = []
    for h, (first, second) in enumerate(pairs):
        names, holdings, company_capital = [], 0.0, 0.0
        for b, unit in enumerate((first, second)):
            members = []
            for j, adult in enumerate(unit["adults"]):
                name = f"h{h}_b{b}_p{j}"
                c = adult["company"]
                people[name] = {
                    "age": {YEAR: adult["age"]},
                    **{k: {YEAR: v} for k, v in c.items()},
                }
                if applies(c):
                    holdings += c["owned_company_holding_value"]
                    company_capital += company_capital_of(c)
                members.append(name)
            benunits[f"h{h}_b{b}"] = {"members": members}
            names += members
        households[f"h{h}"] = {
            "members": names,
            "savings": {YEAR: first["savings"]},
            "corporate_wealth": {YEAR: first["corporate_wealth"]},
        }
        pool = first["savings"] + first["corporate_wealth"]
        expected.append(max(0.0, pool - holdings) + company_capital)
    sim = Simulation(
        situation={"people": people, "benunits": benunits, "households": households}
    )
    capital = np.asarray(sim.calculate("uc_assessable_capital", YEAR))
    assert (capital >= 0).all()
    per_household = capital.reshape(-1, 2).sum(axis=1)
    for got, want in zip(per_household, expected):
        assert close(got, want)
