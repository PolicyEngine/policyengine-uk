"""Property-based tests for how the means tests value capital.

Universal Credit and each legacy means test calculate capital in the United
Kingdom at its current market or surrender value less 10% where there would
be expenses attributable to sale, and less any encumbrance secured on it (UC
Regs 2013 reg. 49(1); HB Regs 2006 reg. 47; HB (SPC) Regs 2006 reg. 45; IS
Regs 1987 reg. 49; JSA Regs 1996 reg. 111; ESA Regs 2008 reg. 113; SPC Regs
2002 reg. 19). Savings in a bank or building society incur no sale expenses;
land, property and shares do.

Invariants, for any generated population of single-adult households:

1. Non-increasing: every programme's assessable capital is at most the same
   household's capital with the deduction switched off (rate 0, no debt).
2. Cash only: a household holding only savings has the same capital with the
   deduction on or off.
3. Differential: capital equals a direct implementation of the regulation,
   savings + sum over sources of max(0, 90% of value - secured debt).
4. Monotone: a higher sale-expense rate, or more secured debt, never raises
   capital.
5. Isolation: debt secured on one asset never takes capital below the value
   of the household's other assets, and capital is never negative.
"""

from functools import reduce

import numpy as np
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation

YEAR = 2026
PROPERTY_SETTINGS = settings(
    max_examples=5,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)
# Assessable capital variable -> parameter node holding its sources and
# sale-expense rule. Pension Credit counts only pension-age adults; the
# others are tested on working-age adults (pension-age Housing Benefit
# disregards all capital for Guarantee Credit recipients).
PROGRAMMES = {
    "uc_assessable_capital": "gov.dwp.universal_credit.means_test.capital",
    "housing_benefit_assessable_capital": "gov.dwp.housing_benefit.means_test.capital",
    "income_support_assessable_capital": "gov.dwp.income_support.means_test.capital",
    "jsa_income_assessable_capital": "gov.dwp.JSA.income.capital",
    "esa_income_assessable_capital": "gov.dwp.ESA.income.capital",
    "pension_credit_assessable_capital": "gov.dwp.pension_credit.income.capital",
}
PENSION_AGE_ONLY = {"pension_credit_assessable_capital"}
ASSETS = [
    "savings",
    "owned_land",
    "corporate_wealth",
    "other_residential_property_value",
    "non_residential_property_value",
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
    return dict(age=draw(st.sampled_from([30, 70])), assets=assets, debts=debts)


def situation(units, debt_scale=1.0):
    people, benunits, homes = {}, {}, {}
    for i, unit in enumerate(units):
        people[f"p{i}"] = {"age": {YEAR: unit["age"]}}
        benunits[f"b{i}"] = {"members": [f"p{i}"]}
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
    return sim, {v: np.asarray(sim.calculate(v, YEAR), dtype=float) for v in PROGRAMMES}


def parameter_node(sim, path):
    return reduce(getattr, path.split("."), sim.tax_benefit_system.parameters(YEAR))


def applies(variable, unit):
    return (unit["age"] >= 67) == (variable in PENSION_AGE_ONLY)


def expected_capital(unit, node):
    """Reg. 49(1) applied source by source, independently of the model."""
    total = 0.0
    for source in node.sources:
        value = unit["assets"][source]
        if source in node.sale_expenses.sources:
            value *= 1 - node.sale_expenses.rate
        if source in DEBTS:
            value = max(0.0, value - unit["debts"][DEBTS[source]])
        total += value
    return total


def close(a, b):
    return abs(a - b) <= 1 + 1e-6 * abs(b)


@PROPERTY_SETTINGS
@given(st.lists(households(), min_size=1, max_size=30))
def test_valuation_matches_the_regulation_and_never_adds_capital(units):
    sim, valued = calculate(units)
    _, full = calculate(units, rate=0.0, debt_scale=0.0)
    for variable, path in PROGRAMMES.items():
        node = parameter_node(sim, path)
        assert node.sale_expenses.rate == 0.1
        assert "savings" in node.sources
        assert "savings" not in node.sale_expenses.sources
        for i, unit in enumerate(units):
            assert valued[variable][i] >= 0, (variable, unit)
            assert valued[variable][i] <= full[variable][i] + 0.01, (variable, unit)
            if applies(variable, unit):
                expected = expected_capital(unit, node)
                assert close(valued[variable][i], expected), (variable, unit)
                # Debt secured on property never reaches the other assets.
                floor = sum(
                    unit["assets"][s]
                    * (1 - node.sale_expenses.rate * (s in node.sale_expenses.sources))
                    for s in node.sources
                    if s not in DEBTS
                )
                assert valued[variable][i] >= floor - 1, (variable, unit)


@PROPERTY_SETTINGS
@given(st.lists(households(cash_only=True), min_size=1, max_size=30))
def test_cash_only_households_have_no_deduction(units):
    _, valued = calculate(units)
    _, full = calculate(units, rate=0.0)
    for variable in PROGRAMMES:
        assert np.allclose(valued[variable], full[variable]), variable
        for i, unit in enumerate(units):
            if applies(variable, unit):
                assert close(valued[variable][i], unit["assets"]["savings"]), variable


@PROPERTY_SETTINGS
@given(
    st.lists(households(), min_size=1, max_size=30),
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
