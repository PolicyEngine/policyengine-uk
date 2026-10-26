"""Property-based tests for how the means tests value capital.

Universal Credit and each legacy means test calculate capital in the United
Kingdom at its current market or surrender value less 10% where there would
be expenses attributable to sale, and less any encumbrance secured on it (UC
Regs 2013 reg. 49(1); HB Regs 2006 reg. 47; HB (SPC) Regs 2006 reg. 45; IS
Regs 1987 reg. 49; JSA Regs 1996 reg. 111; ESA Regs 2008 reg. 113; SPC Regs
2002 reg. 19). A bank or building society account is valued at its balance
(ADM H1675); land and property always have costs of sale (H1606) and shares
are valued less 10% (H1665).

Invariants, for any generated population of single-adult households:

1. Non-increasing: every programme's assessable capital is at most the same
   household's capital with the deduction switched off (rate 0, no debt).
2. Cash only: a household holding only savings has the same capital with the
   deduction on or off.
3. Differential: capital equals a direct implementation of the regulation,
   savings + sum over sources of max(0, 90% of value - secured debt), where
   the test itself fixes which assets take the 10% (land, property and
   shares, not cash), so a wrong parameter list fails it.
4. Monotone: a higher sale-expense rate, or more secured debt, never raises
   capital.
5. Isolation: debt secured on one source never takes capital below the value
   of the household's unencumbered sources, and capital is never negative.
   (Isolation between two encumbered sources is pinned by the differential and
   by a YAML case.)
6. Pennies: 90% of any whole-penny value stored as a float32 input is the
   exact figure rounded down (the legacy benefits) or to the nearest penny
   (Universal Credit and Housing Benefit), checked in integer pence up to
   131,071.99, the largest value float32 holds to the penny.
7. Never rounds the wrong way: for any stored value, whole penny or not, the
   result is within a penny below 90% of the exact stored value when rounding
   down, and within half a penny of it when rounding to the nearest penny.
   The same holds for a float32 value widened to float64, as a benefit unit's
   maximum over its household's values is.
8. Whole pennies through the model: every programme counts whole-penny
   savings, shares and Lifetime ISA balances to the penny: savings in full,
   shares at 90% rounded by the programme's rule, and a Lifetime ISA at 75%
   below its charge-free age.
"""

from fractions import Fraction
from functools import reduce

import numpy as np
from hypothesis import HealthCheck, example, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation
from policyengine_uk.utils.capital_valuation import exact_amount, less_sale_expenses

YEAR = 2026
PROPERTY_SETTINGS = settings(
    max_examples=5,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)
# Assessable capital variable -> parameter node holding its sources and
# sale-expense rule. Pension Credit counts only pension-age adults; Housing
# Benefit is checked at both ages, disregarding all capital for pension-age
# Guarantee Credit recipients (HB (SPC) Regs 2006 reg. 26); the others are
# checked on working-age adults.
PROGRAMMES = {
    "uc_assessable_capital": "gov.dwp.universal_credit.means_test.capital",
    "housing_benefit_assessable_capital": "gov.dwp.housing_benefit.means_test.capital",
    "income_support_assessable_capital": "gov.dwp.income_support.means_test.capital",
    "jsa_income_assessable_capital": "gov.dwp.JSA.income.capital",
    "esa_income_assessable_capital": "gov.dwp.ESA.income.capital",
    "pension_credit_assessable_capital": "gov.dwp.pension_credit.income.capital",
}
PENSION_AGE_ONLY = {"pension_credit_assessable_capital"}
# The assets whose sale incurs expenses, fixed here from the law rather than
# read from the parameters: real property always (ADM H1606), shares (H1665);
# never a bank or building society balance (H1675).
SALE_EXPENSE_ASSETS = {
    "owned_land",
    "other_residential_property_value",
    "non_residential_property_value",
    "overseas_property_value",
    "other_property_value",
    "share_like_capital",
}
LEGAL_RATE = 0.1
ASSETS = [
    "savings",
    "cash_isa",
    "owned_land",
    "corporate_wealth",
    "other_residential_property_value",
    "non_residential_property_value",
    "overseas_property_value",
    "other_property_value",
]
DEBTS = {
    "owned_land": "owned_land_secured_debt",
    "other_residential_property_value": "other_residential_property_secured_debt",
    "non_residential_property_value": "non_residential_property_secured_debt",
}
amount = st.one_of(st.just(0.0), st.floats(0, 400_000, allow_nan=False))


@st.composite
def households(draw, cash_only=False):
    assets = {asset: draw(amount) for asset in ASSETS}
    debts = {debt: draw(amount) for debt in DEBTS.values()}
    if cash_only:
        assets = {asset: 0.0 for asset in ASSETS} | {"savings": assets["savings"]}
        debts = {debt: 0.0 for debt in debts}
    # About half the units do not claim Universal Credit, so the Housing
    # Benefit passport cannot remove every working-age unit from the
    # differential below.
    return dict(
        age=draw(st.sampled_from([30, 70])),
        claims_uc=draw(st.booleans()),
        assets=assets,
        debts=debts,
    )


def situation(units, debt_scale=1.0):
    people, benunits, homes = {}, {}, {}
    for i, unit in enumerate(units):
        people[f"p{i}"] = {"age": {YEAR: unit["age"]}}
        benunits[f"b{i}"] = {
            "members": [f"p{i}"],
            "would_claim_uc": {YEAR: unit["claims_uc"]},
        }
        homes[f"h{i}"] = {
            "members": [f"p{i}"],
            **{k: {YEAR: v} for k, v in unit["assets"].items()},
            **{k: {YEAR: v * debt_scale} for k, v in unit["debts"].items()},
        }
    return {"people": people, "benunits": benunits, "households": homes}


def rate_reform(rate):
    return {
        f"{node}.sale_expenses.rate": {str(YEAR): rate} for node in PROGRAMMES.values()
    }


def calculate(units, rate=None, debt_scale=1.0):
    sim = Simulation(
        situation=situation(units, debt_scale),
        reform=None if rate is None else rate_reform(rate),
    )
    values = {v: np.asarray(sim.calculate(v, YEAR), dtype=float) for v in PROGRAMMES}
    values["guarantee_credit"] = np.asarray(sim.calculate("guarantee_credit", YEAR))
    values["hb_passported"] = np.asarray(
        sim.calculate("housing_benefit_on_passporting_benefit", YEAR)
    )
    return sim, values


def parameter_node(sim, path):
    return reduce(getattr, path.split("."), sim.tax_benefit_system.parameters(YEAR))


def applies(variable, unit, guarantee_credit=0.0, hb_passported=False):
    if variable == "housing_benefit_assessable_capital":
        # A family on a passporting benefit has nil HB capital
        # (housing_benefit_on_passporting_benefit, on main since #1927).
        if hb_passported:
            return False
        return unit["age"] < 67 or guarantee_credit <= 0
    return (unit["age"] >= 67) == (variable in PENSION_AGE_ONLY)


def source_value(unit, source):
    """The aggregate-only fixtures exercise the share-like fallback unchanged."""
    input_name = "corporate_wealth" if source == "share_like_capital" else source
    return unit["assets"][input_name]


def expected_capital(unit, node, variable=None):
    """Reg. 49(1) applied source by source, independently of the model."""
    total = 0.0
    if variable == "uc_assessable_capital":
        # Universal Credit values countable property on its own path
        # (property_sources), outside the financial sources.
        for source in [
            "other_residential_property_value",
            "non_residential_property_value",
        ]:
            total += max(
                0.0,
                unit["assets"][source] * (1 - LEGAL_RATE)
                - unit["debts"][DEBTS[source]],
            )
    for source in node.sources:
        value = source_value(unit, source)
        if source in SALE_EXPENSE_ASSETS:
            value *= 1 - LEGAL_RATE
        if source in DEBTS:
            value = max(0.0, value - unit["debts"][DEBTS[source]])
        total += value
    return total


def close(a, b):
    return abs(a - b) <= 1 + 1e-6 * abs(b)


def check_valuation(units):
    """Assert the valuation invariants; count which Housing Benefit branches ran."""
    sim, valued = calculate(units)
    _, full = calculate(units, rate=0.0, debt_scale=0.0)
    hb_checked = {"passported_nil": 0, "working_age_differential": 0}
    for variable, path in PROGRAMMES.items():
        node = parameter_node(sim, path)
        assert node.sale_expenses.rate == LEGAL_RATE
        assert "savings" in node.sources
        counted = set(node.sources)
        assert set(node.sale_expenses.sources) & counted == (
            SALE_EXPENSE_ASSETS & counted
        ), variable
        hb = variable == "housing_benefit_assessable_capital"
        for i, unit in enumerate(units):
            gc = valued["guarantee_credit"][i]
            assert valued[variable][i] >= 0, (variable, unit)
            assert valued[variable][i] <= full[variable][i] + 0.01, (variable, unit)
            if hb and valued["hb_passported"][i]:
                assert valued[variable][i] == 0, unit
                hb_checked["passported_nil"] += 1
            if hb and unit["age"] >= 67 and gc > 0:
                assert valued[variable][i] == 0, unit
            if applies(variable, unit, gc, valued["hb_passported"][i]):
                expected = expected_capital(unit, node, variable)
                assert close(valued[variable][i], expected), (variable, unit)
                if hb and unit["age"] < 67 and expected > 0:
                    hb_checked["working_age_differential"] += 1
                # Debt secured on property never reaches the other assets.
                floor = sum(
                    source_value(unit, s)
                    * (1 - LEGAL_RATE * (s in SALE_EXPENSE_ASSETS))
                    for s in node.sources
                    if s not in DEBTS
                )
                assert valued[variable][i] >= floor - 1, (variable, unit)
    return hb_checked


@PROPERTY_SETTINGS
@given(st.lists(households(), min_size=20, max_size=200))
def test_valuation_matches_the_regulation_and_never_adds_capital(units):
    check_valuation(units)


def test_housing_benefit_branches_are_both_exercised():
    """Fixed units that a passport cannot hide: one claims UC with £5,000 of
    savings (UC passports it to nil HB capital), one declines UC and holds a
    mortgaged second home (its HB capital is checked against reg 47)."""
    no_debt = {debt: 0.0 for debt in DEBTS.values()}
    units = [
        dict(
            age=30,
            claims_uc=True,
            assets={asset: 0.0 for asset in ASSETS} | {"savings": 5_000.0},
            debts=no_debt,
        ),
        dict(
            age=30,
            claims_uc=False,
            assets={asset: 0.0 for asset in ASSETS}
            | {"savings": 2_000.0, "other_residential_property_value": 100_000.0},
            debts=no_debt | {"other_residential_property_secured_debt": 60_000.0},
        ),
    ]
    hb_checked = check_valuation(units)
    assert hb_checked["passported_nil"] >= 1
    assert hb_checked["working_age_differential"] >= 1


@PROPERTY_SETTINGS
@given(st.lists(households(cash_only=True), min_size=20, max_size=200))
def test_cash_only_households_have_no_deduction(units):
    _, valued = calculate(units)
    _, full = calculate(units, rate=0.0)
    for variable in PROGRAMMES:
        assert np.allclose(valued[variable], full[variable]), variable
        for i, unit in enumerate(units):
            if applies(
                variable,
                unit,
                valued["guarantee_credit"][i],
                valued["hb_passported"][i],
            ):
                assert close(valued[variable][i], unit["assets"]["savings"]), variable


@PROPERTY_SETTINGS
@given(
    st.lists(households(), min_size=20, max_size=200),
    st.floats(0, 0.5),
    st.floats(0, 0.5),
    st.floats(0, 2),
)
def test_capital_is_non_increasing_in_rate_and_secured_debt(units, r1, r2, scale):
    low, high = sorted([r1, r2])
    _, at_low = calculate(units, rate=low)
    _, at_high = calculate(units, rate=high)
    _, more_debt = calculate(units, rate=low, debt_scale=1 + scale)
    for variable in PROGRAMMES:
        assert np.all(at_high[variable] <= at_low[variable] + 0.01), variable
        assert np.all(more_debt[variable] <= at_low[variable] + 0.01), variable


@settings(max_examples=200, deadline=None, derandomize=True)
@given(st.lists(st.integers(0, 13_107_199), min_size=1, max_size=1_000))
# 16,001 is 14,400.8994 after a float32 multiplication; 1,000.10 is stored as
# 1,000.0999756; 90% of 2.30 is 206.99999999999997 pence in float64; 90% of
# 16,666.65 is 14,999.985, a half penny.
@example([1_600_100, 100_010, 230, 1_666_665])
def test_sale_expenses_round_to_the_penny(pence):
    stored = np.asarray(pence, dtype=np.int64).astype(np.float32) / np.float32(100)
    # A benefit unit's maximum over its household's float32 values is float64.
    for value in (stored, stored.astype(np.float64)):
        assert np.round(exact_amount(value) * 100).astype(np.int64).tolist() == pence
        down = less_sale_expenses(value, LEGAL_RATE, True)
        nearest = less_sale_expenses(value, LEGAL_RATE, False)
        assert down.dtype == nearest.dtype == np.float64
        assert np.round(down * 100).astype(np.int64).tolist() == [
            9 * amount // 10 for amount in pence
        ]
        assert np.round(nearest * 100).astype(np.int64).tolist() == [
            (9 * amount + 5) // 10 for amount in pence
        ]


def test_share_valuation_matches_the_adm_worked_example():
    # ADM H1665 and DMG 84763: 250 shares at 4.1375 are 1,034.375, and less
    # 10% for the expenses of sale that is 930.9375: 930.93 rounded down, as
    # the legacy benefits do, or 930.94 to the nearest penny, as Universal
    # Credit does (UC Regs 2013 reg. 6(1)).
    for stored in (1034.375, np.float32(1034.375)):
        assert less_sale_expenses(stored, LEGAL_RATE, True) == 930.93
        assert less_sale_expenses(stored, LEGAL_RATE, False) == 930.94


@settings(max_examples=200, deadline=None, derandomize=True)
@given(
    st.lists(
        st.floats(0, 1_000_000, allow_nan=False, width=32), min_size=1, max_size=500
    )
)
@example([1034.375, 10352.055, 0.005, 999_999.875, 140_000.015625])
def test_sale_expenses_never_round_the_wrong_way(values):
    stored = np.asarray(values, dtype=np.float32)
    exact = exact_amount(stored)
    assert np.array_equal(exact, exact_amount(stored.astype(np.float64)))
    # From 131,072 float32 cannot hold every penny, so no penny is identified
    # and the value is kept as stored: 140,000.01 and 140,000.02 are both
    # stored as 140,000.015625, which rounds down to 140,000.01.
    large = stored >= 131_072
    assert np.array_equal(exact[large], stored[large].astype(np.float64))
    # Storage error is removed only within half a unit of the stored value's
    # own precision, so a value is never moved to a penny it was not stored
    # from.
    assert np.all(
        np.abs(exact - stored.astype(np.float64))
        <= np.spacing(np.abs(stored)).astype(np.float64) / 2
    )
    down = less_sale_expenses(stored, LEGAL_RATE, True)
    nearest = less_sale_expenses(stored, LEGAL_RATE, False)
    for value, low, near in zip(exact.tolist(), down.tolist(), nearest.tolist()):
        # Exact rational arithmetic on the value the helper works from, with
        # the helper's millionth-of-a-penny allowance for binary noise.
        target = Fraction(value) * Fraction(9, 10)
        noise = Fraction(1, 100_000_000)
        assert target - Fraction(1, 100) - noise < Fraction(low) <= target + noise
        assert abs(Fraction(near) - target) <= Fraction(1, 200) + noise


ROUNDS_DOWN = {
    "uc_assessable_capital": False,
    "housing_benefit_assessable_capital": False,
    "income_support_assessable_capital": True,
    "jsa_income_assessable_capital": True,
    "esa_income_assessable_capital": True,
    "pension_credit_assessable_capital": True,
}


def whole_penny_situation(rows):
    people, benunits, homes = {}, {}, {}
    for i, (savings, shares, lisa_quarters, age) in enumerate(rows):
        people[f"p{i}"] = {
            "age": {YEAR: age},
            "lifetime_isa_balance": {YEAR: 4 * lisa_quarters / 100},
        }
        benunits[f"b{i}"] = {"members": [f"p{i}"]}
        homes[f"h{i}"] = {
            "members": [f"p{i}"],
            "savings": {YEAR: savings / 100},
            "corporate_wealth": {YEAR: shares / 100},
        }
    return {"people": people, "benunits": benunits, "households": homes}


@PROPERTY_SETTINGS
@given(
    st.lists(
        st.tuples(
            st.integers(0, 6_000_000),
            st.integers(0, 6_000_000),
            st.integers(0, 375_000),
            st.sampled_from([30, 70]),
        ),
        min_size=20,
        max_size=100,
    )
)
# 16,000.01 of savings is over every 16,000 limit; 1,000.10 and 12,345.67
# lose a penny if float32 storage error reaches a floor; a Lifetime ISA of
# 0.24 or 1,000.04 counts 0.18 or 750.03 under 60.
@example(
    [
        (1_600_001, 0, 0, 30),
        (100_010, 0, 0, 30),
        (1_234_567, 0, 0, 70),
        (159_992, 1_600_010, 0, 30),
        (0, 0, 6, 30),
        (0, 0, 25_001, 30),
    ]
    * 4
)
def test_whole_pennies_are_counted_to_the_penny(rows):
    sim = Simulation(situation=whole_penny_situation(rows))
    values = {v: np.asarray(sim.calculate(v, YEAR), dtype=float) for v in PROGRAMMES}
    gc = np.asarray(sim.calculate("guarantee_credit", YEAR))
    passported = np.asarray(
        sim.calculate("housing_benefit_on_passporting_benefit", YEAR)
    )
    savings_credit_only = np.asarray(
        sim.calculate("in_receipt_of_savings_credit_only", YEAR)
    )
    for variable, round_down in ROUNDS_DOWN.items():
        for i, (savings, shares, lisa_quarters, age) in enumerate(rows):
            if not applies(variable, {"age": age}, gc[i], passported[i]):
                continue
            # Housing Benefit takes Pension Credit's capital for a savings
            # credit only award (HB (SPC) Regs 2006 reg. 27(6)).
            down = round_down or (
                variable == "housing_benefit_assessable_capital"
                and savings_credit_only[i]
            )
            share_pence = (9 * shares + (0 if down else 5)) // 10
            lisa_pence = 4 * lisa_quarters if age >= 60 else 3 * lisa_quarters
            expected = (savings + share_pence + lisa_pence) / 100
            # The model stores float32, which holds every penny below 131,072.
            assert abs(values[variable][i] - expected) < 0.004, (
                variable,
                rows[i],
                values[variable][i],
                expected,
            )
