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
2. Capital identity: for a benefit unit alone in its household, assessable
   capital equals the capital without the rule less the owners' holdings, up
   to the household's corporate wealth that holds them, plus each owner's
   company capital net of trade assets disregarded while they work in the
   trade.
3. Allocation and conservation: in a household of two benefit units that do
   not report their capital, the household's capital less every owner's
   holding (up to its corporate wealth) is shared between the units in
   proportion to their claimants, and each unit adds its own claimants'
   company capital; so the units' capital sums to that pool plus the owners'
   company capital.
4. Earnings identity: earned income before the floor is pay less the
   person's own income tax and NI on the employment, plus the trading total
   floored at zero, less their relievable pension contributions, floored at
   zero. The trading total is their own trading profit or loss plus, for a
   trading company, the company income share (a loss is negative), less the
   income tax and NI on the trade (reg. 57(2) steps 1 to 3); a property-only
   company adds nothing. Where pay and own-trade profit are within 12,000,
   no tax or NI is due and it is exactly pay plus the floored trading total.
5. Floor: the floor applies exactly to claimants in the all work-related
   requirements group, outside a start-up period, who are self-employed or
   own a trading company that is their main employment (reg. 62(1), (5),
   reg. 77(3)(c)), and never to one with limited capability for work and
   work-related activity. It never lowers earned income, and a single
   claimant it applies to has earned income of at least the floor.
6. Monotone: Universal Credit is non-increasing in the company income share,
   among cases where the extra income does not change the benefit cap
   earnings exemption (reg. 82(1)(a): crossing the threshold lifts the cap
   and can raise the award), and in the company's capital; it is
   non-decreasing in the value of the disregarded holding and of disregarded
   trade assets.
7. Property companies: the income share and the main-employment flag never
   change Universal Credit or earned income for a property-only company.
8. Dependants: company income and capital belonging to a dependant (with no
   holding) change neither the award nor its capital or earned income
   (reg. 22(1)(b)).
9. Holdings count for nobody: adding shares to the household's corporate
   wealth as the disregarded holding of a dependant in a family (reporting
   its capital or not) and of an adult in another, unreported benefit unit
   changes no unit's assessable capital.

The strategies make most adults owners of a trading company, keep capital
mostly under the £16,000 limit and put earnings around the floor, so each
property is exercised rather than satisfied vacuously. Pinned examples make
every run reach each reg. 77 earnings and floor branch and a shared-household
holding, whatever the generated examples reach.
"""

import numpy as np
from hypothesis import HealthCheck, example, given, settings
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
    "is_uc_benefit_cap_exempt_earnings",
]
PERSON_VARIABLES = [
    "uc_individual_earned_income",
    "uc_individual_earned_income_before_mif",
    "uc_minimum_income_floor",
    "uc_mif_applies",
    "uc_income_tax_on_earnings",
    "uc_national_insurance_on_earnings",
    "uc_income_tax_on_trade",
    "uc_national_insurance_on_trade",
    "pension_contributions",
    "is_uc_assessed_claimant",
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
        uc_limited_capability_for_WRA=draw(st.sampled_from([False] * 4 + [True])),
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
                # The drawn adults are the claimant and partner, however far
                # apart their ages; the age presumption alone would read a
                # partner 20 or more years younger as the claimant's child.
                "is_claimant_or_partner": {YEAR: True},
                "employment_income": {YEAR: adult["employment_income"]},
                "self_employment_income": {YEAR: adult["self_employment_income"]},
                "uc_is_in_startup_period": {YEAR: adult["uc_is_in_startup_period"]},
                "uc_limited_capability_for_WRA": {
                    YEAR: adult["uc_limited_capability_for_WRA"]
                },
                **{k: {YEAR: v} for k, v in facts.items()},
            }
            names.append(name)
        for k in range(unit["children"]):
            name = f"c{i}_{k}"
            people[name] = {
                "age": {YEAR: 5 + k},
                "is_claimant_or_partner": {YEAR: False},
            }
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
    out["all_requirements"] = (
        np.asarray(sim.calculate("uc_work_related_group_apart_from_earnings", YEAR))
        == "ALL_REQUIREMENTS"
    )
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


def pinned_company(**facts):
    """A pinned example's company: a trading company the adult solely owns."""
    return {
        "stands_as_sole_owner_or_partner_of_company": True,
        "owned_company_carries_on_trade": True,
        "owned_company_carries_on_property_business": False,
        "owned_company_intermediary_earnings_chapter": "NONE",
        "owned_company_intermediary_earnings_from_main_employment": False,
        "owned_company_is_main_employment": False,
        "is_engaged_in_owned_company_trade": False,
        "owned_company_income_share": 0.0,
        "owned_company_capital": 0.0,
        "owned_company_trade_assets": 0.0,
        "owned_company_holding_value": 0.0,
        **facts,
    }


def pinned_adult(company=None, **facts):
    return {
        "age": 40,
        "employment_income": 0.0,
        "self_employment_income": 0.0,
        "uc_is_in_startup_period": False,
        "uc_limited_capability_for_WRA": False,
        "company": company
        or pinned_company(stands_as_sole_owner_or_partner_of_company=False),
        **facts,
    }


def pinned_unit(*adults, savings=0.0, corporate_wealth=0.0):
    return dict(
        adults=list(adults),
        children=0,
        rent=0.0,
        savings=savings,
        corporate_wealth=corporate_wealth,
    )


# Every run exercises each reg. 77 earnings and floor branch at least once,
# whatever the generated examples reach.
PINNED_EARNINGS_UNITS = [
    # 77(3)(c): main-employment trading company, no other self-employment.
    pinned_unit(
        pinned_adult(
            pinned_company(
                owned_company_is_main_employment=True,
                owned_company_income_share=6_000.0,
            )
        )
    ),
    # Reg. 57(2) step 2: a company loss against the owner's own trade.
    pinned_unit(
        pinned_adult(
            pinned_company(owned_company_income_share=-3_000.0),
            self_employment_income=8_000.0,
            uc_is_in_startup_period=True,
        )
    ),
    # Reg. 57(2) step 3: the tax on a trade a company loss cancels.
    pinned_unit(
        pinned_adult(
            pinned_company(owned_company_income_share=-20_000.0),
            employment_income=12_000.0,
            self_employment_income=20_000.0,
            uc_is_in_startup_period=True,
        )
    ),
    # Limited capability for work and work-related activity: no floor.
    pinned_unit(
        pinned_adult(
            pinned_company(
                owned_company_is_main_employment=True,
                owned_company_income_share=6_000.0,
            ),
            uc_limited_capability_for_WRA=True,
        )
    ),
]


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
    for v in VARIABLES + ["uc_individual_earned_income", "uc_mif_applies"]:
        np.testing.assert_allclose(got[v], base[v], rtol=0, atol=1e-6, err_msg=v)


@PROPERTY_SETTINGS
@given(st.lists(units(), min_size=2, max_size=4))
@example(PINNED_EARNINGS_UNITS)
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
            # Earnings identity, before the floor: reg. 77(3)(b) adds the
            # company's profit or loss to the person's own trade (reg. 57(2)
            # step 2), the tax and NI on the trade come off that total (step
            # 3), and a negative result becomes nil; pay is net of the tax and
            # NI on the employment (reg. 55(5)).
            company_profit_or_loss = (
                c["owned_company_income_share"]
                if applies(c) and c["owned_company_carries_on_trade"]
                else 0.0
            )
            trade_deductions = (
                got["uc_income_tax_on_trade"][k]
                + got["uc_national_insurance_on_trade"][k]
            )
            self_employed = max(
                0.0,
                adult["self_employment_income"]
                + company_profit_or_loss
                - trade_deductions,
            )
            employment_deductions = (
                got["uc_income_tax_on_earnings"][k]
                + got["uc_national_insurance_on_earnings"][k]
                - trade_deductions
            )
            before = got["uc_individual_earned_income_before_mif"][k]
            assert close(
                before,
                max(
                    0.0,
                    adult["employment_income"]
                    - employment_deductions
                    + self_employed
                    - got["pension_contributions"][k],
                ),
            )
            # Independently of the model's tax: earnings within the personal
            # allowance, the primary threshold and the lower profits limit
            # bear no income tax or NI, so earned income is pay plus the nil
            # floored trading total.
            if (
                adult["employment_income"] + adult["self_employment_income"] <= 12_000
                and got["pension_contributions"][k] == 0
            ):
                assert close(
                    before,
                    adult["employment_income"]
                    + max(
                        0.0, adult["self_employment_income"] + company_profit_or_loss
                    ),
                )
            # Floor trigger: reg. 62(1) and (5), with reg. 77(3)(c).
            trade_main = (
                applies(c)
                and c["owned_company_carries_on_trade"]
                and c["owned_company_is_main_employment"]
            )
            # The model's stored (float32) self-employment income: a generated
            # amount too small for float32 is zero there.
            gainful = got["self_employment_income"][k] != 0 or trade_main
            assert got["uc_mif_applies"][k] == (
                got["all_requirements"][k]
                and gainful
                and not adult["uc_is_in_startup_period"]
            )
            # Independently of the model's groups: limited capability for
            # work and work-related activity puts a claimant in the no
            # work-related requirements group (Welfare Reform Act 2012
            # s. 19(2)(a)), so no floor (reg. 62(1)(b)).
            if adult["uc_limited_capability_for_WRA"]:
                assert not got["uc_mif_applies"][k]
            earned = got["uc_individual_earned_income"][k]
            floor_can_apply = (
                got["uc_mif_applies"][k] and got["is_uc_assessed_claimant"][k]
            )
            if floor_can_apply:
                assert earned >= before - 1e-2
                if len(unit["adults"]) == 1:
                    floor = got["uc_minimum_income_floor"][k]
                    assert close(earned, max(before, floor))
            else:
                assert close(earned, before)
        disregarded = min(holdings, unit["corporate_wealth"])
        expected = base["uc_assessable_capital"][i] - disregarded + company_capital
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
    got = calculate(variants)
    uc = got["universal_credit"].reshape(-1, 6)
    exempt = got["is_uc_benefit_cap_exempt_earnings"].reshape(-1, 6)
    tol = 1e-6
    base, more_income, more_capital, more_holding, more_assets, engaged = uc.T
    # Extra earnings that lift the benefit cap (reg. 82(1)(a)) can raise the
    # award, so income monotonicity holds where the exemption is unchanged.
    same_exemption = exempt[:, 0] == exempt[:, 1]
    assert (more_income[same_exemption] <= base[same_exemption] + tol).all()
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
@example(
    [
        (
            pinned_unit(
                pinned_adult(pinned_company(owned_company_holding_value=30_000.0)),
                savings=10_000.0,
                corporate_wealth=30_000.0,
            ),
            pinned_unit(pinned_adult()),
        )
    ]
)
def test_household_capital_is_allocated_and_conserved_across_benefit_units(pairs):
    # Each household holds two benefit units: the first unit's adults and the
    # second's, with the first unit's savings and corporate wealth. No unit
    # reports its own capital, so every owner's holding leaves the household
    # pool, the rest is shared in proportion to each unit's claimants (all
    # adults here), and each unit adds its own claimants' company capital.
    people, benunits, households = {}, {}, {}
    expected_units, expected_households = [], []
    for h, (first, second) in enumerate(pairs):
        names, holdings, unit_company_capital = [], 0.0, []
        for b, unit in enumerate((first, second)):
            members, company_capital = [], 0.0
            for j, adult in enumerate(unit["adults"]):
                name = f"h{h}_b{b}_p{j}"
                c = adult["company"]
                people[name] = {
                    "age": {YEAR: adult["age"]},
                    # Each unit's adults are its claimant and partner.
                    "is_claimant_or_partner": {YEAR: True},
                    **{k: {YEAR: v} for k, v in c.items()},
                }
                if applies(c):
                    holdings += c["owned_company_holding_value"]
                    company_capital += company_capital_of(c)
                members.append(name)
            benunits[f"h{h}_b{b}"] = {"members": members}
            unit_company_capital.append(company_capital)
            names += members
        households[f"h{h}"] = {
            "members": names,
            "savings": {YEAR: first["savings"]},
            "corporate_wealth": {YEAR: first["corporate_wealth"]},
        }
        disregarded = min(holdings, first["corporate_wealth"])
        pool = first["savings"] + first["corporate_wealth"] - disregarded
        claimants = [len(first["adults"]), len(second["adults"])]
        for n, company_capital in zip(claimants, unit_company_capital):
            expected_units.append(pool * n / sum(claimants) + company_capital)
        expected_households.append(pool + sum(unit_company_capital))
    sim = Simulation(
        situation={"people": people, "benunits": benunits, "households": households}
    )
    capital = np.asarray(sim.calculate("uc_assessable_capital", YEAR))
    assert (capital >= 0).all()
    for got, want in zip(capital, expected_units):
        assert close(got, want)
    per_household = capital.reshape(-1, 2).sum(axis=1)
    for got, want in zip(per_household, expected_households):
        assert close(got, want)


@PROPERTY_SETTINGS
@given(
    st.lists(units(), min_size=1, max_size=3),
    st.floats(1, 40_000),
    st.floats(1, 50_000),
    st.booleans(),
)
def test_dependant_company_does_not_change_the_award(unit_list, income, capital, main):
    # A qualifying young person in each unit is the sole owner of a trading
    # company with income and capital. Its income is theirs, not a
    # claimant's (reg. 22(1)(b), reg. 82(1)(a)), and only a claimant's or
    # partner's company capital counts. With no holding in the household's
    # capital, the award matches the same unit without the company.
    company = {
        "stands_as_sole_owner_or_partner_of_company": True,
        "owned_company_carries_on_trade": True,
        "owned_company_carries_on_property_business": False,
        "owned_company_intermediary_earnings_chapter": "NONE",
        "owned_company_intermediary_earnings_from_main_employment": False,
        "owned_company_is_main_employment": main,
        "is_engaged_in_owned_company_trade": False,
        "owned_company_income_share": income,
        "owned_company_capital": capital,
        "owned_company_trade_assets": 0.0,
        "owned_company_holding_value": 0.0,
    }
    none = {k: _empty(v) for k, v in company.items()}

    def build(facts):
        people, benunits, households, dependants = {}, {}, {}, []
        for i, unit in enumerate(unit_list):
            names = []
            for j, adult in enumerate(unit["adults"]):
                name = f"p{i}_{j}"
                people[name] = {
                    "age": {YEAR: adult["age"]},
                    "is_claimant_or_partner": {YEAR: True},
                    "employment_income": {YEAR: adult["employment_income"]},
                    "self_employment_income": {YEAR: adult["self_employment_income"]},
                }
                names.append(name)
            people[f"d{i}"] = {
                "age": {YEAR: 17},
                "is_claimant_or_partner": {YEAR: False},
                "is_in_non_advanced_education": {YEAR: True},
                **{k: {YEAR: v} for k, v in facts.items()},
            }
            names.append(f"d{i}")
            dependants.append(len(people) - 1)
            benunits[f"b{i}"] = {"members": names, "would_claim_uc": {YEAR: True}}
            households[f"h{i}"] = {
                "members": names,
                "tenure_type": {YEAR: "RENT_PRIVATELY"},
                "rent": {YEAR: unit["rent"]},
                "savings": {YEAR: unit["savings"]},
            }
        sim = Simulation(
            situation={
                "people": people,
                "benunits": benunits,
                "households": households,
            }
        )
        claimant = np.asarray(sim.calculate("is_uc_assessed_claimant", YEAR))
        assert not claimant[dependants].any()
        earnings = np.asarray(sim.calculate("uc_company_self_employed_earnings", YEAR))
        assert (earnings[dependants] == facts["owned_company_income_share"]).all()
        return {v: np.asarray(sim.calculate(v, YEAR)) for v in VARIABLES}

    got, base = build(company), build(none)
    for v in VARIABLES:
        np.testing.assert_allclose(got[v], base[v], rtol=0, atol=1e-6, err_msg=v)


@PROPERTY_SETTINGS
@given(
    st.lists(st.tuples(units(), units()), min_size=1, max_size=3),
    st.floats(1, 20_000),
    st.floats(1, 20_000),
    st.one_of(st.none(), st.floats(0, 20_000)),
)
def test_disregarded_holdings_count_for_no_benefit_unit(
    pairs, dependant_holding, owner_holding, reported
):
    # Each household holds a family (the first unit's adults and a
    # qualifying young person), which reports its capital unless `reported`
    # is None, and a second, unreported benefit unit. The young person and
    # the second unit's first adult each hold shares in a company they stand
    # as sole owner of; the shares are in the household's corporate_wealth.
    # Reg. 77(2) disregards both holdings, and a dependant's capital is no
    # claimant's, so adding the shares changes no unit's capital.
    def build(with_holdings):
        people, benunits, households = {}, {}, {}
        for h, (family, other) in enumerate(pairs):
            family_names = []
            for j, adult in enumerate(family["adults"]):
                people[f"h{h}_f{j}"] = {
                    "age": {YEAR: adult["age"]},
                    "is_claimant_or_partner": {YEAR: True},
                }
                family_names.append(f"h{h}_f{j}")
            dependant = {
                "age": {YEAR: 17},
                "is_claimant_or_partner": {YEAR: False},
                "is_in_non_advanced_education": {YEAR: True},
            }
            other_names = []
            for j, adult in enumerate(other["adults"]):
                people[f"h{h}_o{j}"] = {
                    "age": {YEAR: adult["age"]},
                    "is_claimant_or_partner": {YEAR: True},
                }
                other_names.append(f"h{h}_o{j}")
            shares = 0.0
            if with_holdings:
                owner = {
                    "stands_as_sole_owner_or_partner_of_company": {YEAR: True},
                    "owned_company_carries_on_trade": {YEAR: True},
                }
                dependant.update(
                    owner, owned_company_holding_value={YEAR: dependant_holding}
                )
                people[other_names[0]].update(
                    owner, owned_company_holding_value={YEAR: owner_holding}
                )
                shares = dependant_holding + owner_holding
            people[f"h{h}_d"] = dependant
            family_names.append(f"h{h}_d")
            benunits[f"h{h}_family"] = {"members": family_names}
            if reported is not None:
                benunits[f"h{h}_family"]["uc_reported_capital"] = {YEAR: reported}
            benunits[f"h{h}_other"] = {"members": other_names}
            households[f"h{h}"] = {
                "members": family_names + other_names,
                "savings": {YEAR: family["savings"]},
                "corporate_wealth": {YEAR: family["corporate_wealth"] + shares},
            }
        sim = Simulation(
            situation={
                "people": people,
                "benunits": benunits,
                "households": households,
            }
        )
        return np.asarray(sim.calculate("uc_assessable_capital", YEAR))

    with_holdings, without = build(True), build(False)
    for got, want in zip(with_holdings, without):
        assert close(got, want)
