"""Property-based tests for how the means tests value capital.

Universal Credit and each legacy means test calculate capital in the United
Kingdom at its current market or surrender value less 10% where there would
be expenses attributable to sale, and less any encumbrance secured on it (UC
Regs 2013 reg. 49(1); HB Regs 2006 reg. 47; HB (SPC) Regs 2006 reg. 45; IS
Regs 1987 reg. 49; JSA Regs 1996 reg. 111; ESA Regs 2008 reg. 113; SPC Regs
2002 reg. 19). A bank or building society account is valued at its balance
(ADM H1675); land and property always have costs of sale (H1606) and shares
are valued less 10% (H1665). Unit trusts have no costs of sale (H1673-H1674)
and an ISA is valued at what the person would get by withdrawing it (H1656).

corporate_wealth may be itemised into directly_held_shares,
unit_and_investment_trusts and stocks_and_shares_isa; unitemised_corporate_wealth
carries whatever is not itemised, so it is all of corporate_wealth on datasets
without the components and about nil on datasets that build corporate_wealth as
their exact sum. The survey bucket of unit and investment trusts is treated as
having no costs of sale, an approximation for its investment-trust part.

Invariants, for any generated population of single-adult households, whose
share-like holdings are unsplit, split consistently (corporate_wealth equal to
the components' sum), partly split, given as components only, or drawn freely:

1. Non-increasing: every programme's assessable capital is at most the same
   household's capital with the deduction switched off (rate 0, no debt).
2. Cash only: a household holding only savings has the same capital with the
   deduction on or off.
3. Differential: capital equals a direct implementation of the regulation,
   savings + sum over sources of max(0, 90% of value - secured debt), where
   the test itself fixes which assets count and which take the 10% (land,
   property, directly held shares and unitemised corporate wealth; not cash,
   trusts or ISAs), so a wrong parameter list fails it.
4. Monotone: a higher sale-expense rate, or more secured debt, never raises
   capital.
5. Isolation: debt secured on one source never takes capital below the value
   of the household's unencumbered sources, and capital is never negative.
   (Isolation between two encumbered sources is pinned by the differential and
   by a YAML case.)
6. Residual: unitemised_corporate_wealth is never negative and equals
   max(0, corporate_wealth - sum of components).
7. Backward compatibility: with every component nil, every programme's capital
   is bit-for-bit the capital under a reform restoring the source lists used
   before the split.
8. Conservation: at rate 0, a consistent split leaves capital unchanged.
9. Split effect: a consistent split less the unsplit household is rate x
   (trusts + ISA), which lies in [0, rate x corporate_wealth].
10. No double counting: capital is at most the other assets plus
    max(corporate_wealth, sum of components).
11. Aggregates: total_wealth, net_wealth and corporate_sector_wealth do not
    change with the component inputs.
"""

from functools import reduce

import numpy as np
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from policyengine_uk import CountryTaxBenefitSystem, Simulation

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
COMPONENTS = (
    "directly_held_shares",
    "unit_and_investment_trusts",
    "stocks_and_shares_isa",
)
RESIDUAL = "unitemised_corporate_wealth"
SHARE_LIKE = (*COMPONENTS, RESIDUAL)
PROPERTY = ("other_residential_property_value", "non_residential_property_value")
# The assets each programme counts, fixed here rather than read from the
# parameters. Universal Credit's list has never included owned_land; that
# predates the capital-valuation work and is outside these properties.
LEGACY_COUNTED = {"savings", "owned_land", *PROPERTY, *SHARE_LIKE}
COUNTED = {
    variable: LEGACY_COUNTED
    for variable in PROGRAMMES
    if variable != "uc_assessable_capital"
} | {"uc_assessable_capital": {"savings", *PROPERTY, *SHARE_LIKE}}
# The assets whose sale incurs expenses, fixed here from the law rather than
# read from the parameters: real property always (ADM H1606) and shares
# (H1665); never a bank or building society balance (H1675), a unit trust
# (H1673-H1674) or an ISA (H1656). The unitemised residual keeps the flat
# treatment corporate_wealth had before it was itemised.
SALE_EXPENSE_ASSETS = {
    "owned_land",
    *PROPERTY,
    "directly_held_shares",
    RESIDUAL,
}
LEGAL_RATE = 0.1
# The source lists in force before corporate_wealth was itemised, for the
# backward-compatibility differential.
PRE_SPLIT_LEGACY_SOURCES = [
    "savings",
    "owned_land",
    "corporate_wealth",
    *PROPERTY,
]
PRE_SPLIT_SOURCES = {
    "gov.dwp.universal_credit.means_test.capital": [
        "savings",
        *PROPERTY,
        "corporate_wealth",
    ],
    "gov.dwp.housing_benefit.means_test.capital": PRE_SPLIT_LEGACY_SOURCES,
    "gov.dwp.income_support.means_test.capital": PRE_SPLIT_LEGACY_SOURCES,
    "gov.dwp.JSA.income.capital": PRE_SPLIT_LEGACY_SOURCES,
    "gov.dwp.ESA.income.capital": PRE_SPLIT_LEGACY_SOURCES,
    "gov.dwp.pension_credit.income.capital": [
        "savings",
        "owned_land",
        *PROPERTY,
        "corporate_wealth",
    ],
}
PRE_SPLIT_SALE_EXPENSE_SOURCES = ["owned_land", *PROPERTY, "corporate_wealth"]
BASE_ASSETS = ["savings", "owned_land", "corporate_wealth", *PROPERTY]
DEBTS = {
    "owned_land": "owned_land_secured_debt",
    "other_residential_property_value": "other_residential_property_secured_debt",
    "non_residential_property_value": "non_residential_property_secured_debt",
}
SPLIT_MODES = ("unsplit", "consistent", "partial", "components_only", "free")
amount = st.one_of(st.just(0.0), st.floats(0, 400_000, allow_nan=False))


@st.composite
def households(draw, mode=None, cash_only=False, dividends=False):
    mode = mode or draw(st.sampled_from(SPLIT_MODES))
    assets = {asset: draw(amount) for asset in BASE_ASSETS}
    components = {component: draw(amount) for component in COMPONENTS}
    if mode == "unsplit":
        components = {component: 0.0 for component in COMPONENTS}
    elif mode == "consistent":
        assets["corporate_wealth"] = sum(components.values())
    elif mode == "partial":
        components = {
            component: value if draw(st.booleans()) else 0.0
            for component, value in components.items()
        }
        assets["corporate_wealth"] = sum(components.values()) + draw(amount)
    elif mode == "components_only":
        assets["corporate_wealth"] = 0.0
    assets |= components
    debts = {debt: draw(amount) for debt in DEBTS.values()}
    if cash_only:
        assets = {asset: 0.0 for asset in assets} | {"savings": assets["savings"]}
        debts = {debt: 0.0 for debt in debts}
    unit = dict(age=draw(st.sampled_from([30, 70])), assets=assets, debts=debts)
    if dividends:
        unit["dividend_income"] = draw(st.floats(0, 50_000, allow_nan=False))
    return unit


def situation(units, debt_scale=1.0, dividends=True):
    people, benunits, homes = {}, {}, {}
    for i, unit in enumerate(units):
        people[f"p{i}"] = {"age": {YEAR: unit["age"]}}
        if dividends and "dividend_income" in unit:
            people[f"p{i}"]["dividend_income"] = {YEAR: unit["dividend_income"]}
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


PRE_SPLIT_REFORM = {
    f"{node}.{parameter}": {str(YEAR): value}
    for node, sources in PRE_SPLIT_SOURCES.items()
    for parameter, value in (
        ("sources", sources),
        ("sale_expenses.sources", PRE_SPLIT_SALE_EXPENSE_SOURCES),
    )
}
EXTRA_OUTPUTS = (
    "guarantee_credit",
    RESIDUAL,
    "uc_tariff_income",
    "uc_unearned_income",
    "pension_credit_deemed_income",
    "total_wealth",
    "net_wealth",
    "corporate_sector_wealth",
)


def calculate(units, rate=None, debt_scale=1.0, reform=None, dividends=True):
    if rate is not None:
        reform = (reform or {}) | rate_reform(rate)
    sim = Simulation(
        situation=situation(units, debt_scale, dividends),
        reform=reform,
    )
    values = {
        v: np.asarray(sim.calculate(v, YEAR), dtype=float)
        for v in (*PROGRAMMES, *EXTRA_OUTPUTS)
    }
    return sim, values


def without_components(unit):
    """The same household with corporate_wealth left unitemised."""
    assets = unit["assets"] | {component: 0.0 for component in COMPONENTS}
    return unit | {"assets": assets}


def parameter_node(sim, path):
    return reduce(getattr, path.split("."), sim.tax_benefit_system.parameters(YEAR))


def applies(variable, unit, guarantee_credit=0.0):
    if variable == "housing_benefit_assessable_capital":
        return unit["age"] < 67 or guarantee_credit <= 0
    return (unit["age"] >= 67) == (variable in PENSION_AGE_ONLY)


def residual(unit):
    assets = unit["assets"]
    return max(0.0, assets["corporate_wealth"] - sum(assets[c] for c in COMPONENTS))


def share_like_total(unit):
    """max(corporate_wealth, sum of components): the share-like holdings once."""
    return sum(unit["assets"][c] for c in COMPONENTS) + residual(unit)


def expected_capital(unit, variable, rate=LEGAL_RATE):
    """Reg. 49(1) applied source by source, independently of the model."""
    values = unit["assets"] | {RESIDUAL: residual(unit)}
    total = 0.0
    for source in COUNTED[variable]:
        value = values[source]
        if source in SALE_EXPENSE_ASSETS:
            value *= 1 - rate
        if source in DEBTS:
            value = max(0.0, value - unit["debts"][DEBTS[source]])
        total += value
    return total


def close(a, b, scale=0.0):
    """Equal up to float32 rounding of totals as large as ``b`` or ``scale``."""
    return abs(a - b) <= 1 + 1e-6 * max(abs(b), abs(scale))


def test_source_lists_match_the_legal_asset_sets():
    parameters = CountryTaxBenefitSystem().parameters(YEAR)
    for variable, path in PROGRAMMES.items():
        node = reduce(getattr, path.split("."), parameters)
        assert set(node.sources) == COUNTED[variable], variable
        assert set(node.sale_expenses.sources) == SALE_EXPENSE_ASSETS, variable
        assert "corporate_wealth" not in node.sources, variable
        assert node.sale_expenses.rate == LEGAL_RATE, variable


@PROPERTY_SETTINGS
@given(st.lists(households(), min_size=20, max_size=200))
def test_valuation_matches_the_regulation_and_never_adds_capital(units):
    sim, valued = calculate(units)
    _, full = calculate(units, rate=0.0, debt_scale=0.0)
    for variable, path in PROGRAMMES.items():
        node = parameter_node(sim, path)
        assert node.sale_expenses.rate == LEGAL_RATE
        assert set(node.sale_expenses.sources) == SALE_EXPENSE_ASSETS, variable
        for i, unit in enumerate(units):
            gc = valued["guarantee_credit"][i]
            assert valued[variable][i] >= 0, (variable, unit)
            assert valued[variable][i] <= full[variable][i] + 0.01, (variable, unit)
            if variable == "housing_benefit_assessable_capital" and unit["age"] >= 67:
                if gc > 0:
                    assert valued[variable][i] == 0, unit
            if applies(variable, unit, gc):
                expected = expected_capital(unit, variable)
                assert close(valued[variable][i], expected), (variable, unit)
                # Debt secured on property never reaches the other assets.
                values = unit["assets"] | {RESIDUAL: residual(unit)}
                floor = sum(
                    values[s] * (1 - LEGAL_RATE * (s in SALE_EXPENSE_ASSETS))
                    for s in COUNTED[variable]
                    if s not in DEBTS
                )
                assert valued[variable][i] >= floor - 1, (variable, unit)
                # Each share-like holding is counted at most once.
                other = sum(
                    unit["assets"][s] for s in COUNTED[variable] if s not in SHARE_LIKE
                )
                ceiling = other + share_like_total(unit)
                assert valued[variable][i] <= ceiling + 1 + 1e-6 * ceiling, (
                    variable,
                    unit,
                )


@PROPERTY_SETTINGS
@given(st.lists(households(), min_size=20, max_size=200))
def test_residual_is_corporate_wealth_less_its_components_floored_at_nil(units):
    _, valued = calculate(units)
    for i, unit in enumerate(units):
        assert valued[RESIDUAL][i] >= 0, unit
        assert close(valued[RESIDUAL][i], residual(unit)), unit
        if all(unit["assets"][c] == 0 for c in COMPONENTS):
            assert valued[RESIDUAL][i] == np.float32(unit["assets"]["corporate_wealth"])


@PROPERTY_SETTINGS
@given(st.lists(households(mode="unsplit"), min_size=20, max_size=200))
def test_unsplit_datasets_match_the_pre_split_source_lists_exactly(units):
    _, split_lists = calculate(units)
    _, pre_split = calculate(units, reform=PRE_SPLIT_REFORM)
    for variable in (
        *PROGRAMMES,
        "guarantee_credit",
        "uc_tariff_income",
        "uc_unearned_income",
        "pension_credit_deemed_income",
    ):
        assert np.array_equal(split_lists[variable], pre_split[variable]), variable


@PROPERTY_SETTINGS
@given(
    st.lists(households(mode="consistent"), min_size=20, max_size=200),
    st.one_of(st.just(LEGAL_RATE), st.floats(0, 0.5)),
)
def test_a_consistent_split_moves_capital_only_by_the_exempt_holdings(units, rate):
    unsplit_units = [without_components(unit) for unit in units]
    _, split0 = calculate(units, rate=0.0)
    _, unsplit0 = calculate(unsplit_units, rate=0.0)
    _, split = calculate(units, rate=rate)
    _, unsplit = calculate(unsplit_units, rate=rate)
    for variable in PROGRAMMES:
        for i, unit in enumerate(units):
            if not (
                applies(variable, unit, split0["guarantee_credit"][i])
                and applies(variable, unit, unsplit0["guarantee_credit"][i])
            ):
                continue
            # At rate 0 itemising corporate_wealth conserves capital.
            assert close(split0[variable][i], unsplit0[variable][i]), (variable, unit)
            if not (
                applies(variable, unit, split["guarantee_credit"][i])
                and applies(variable, unit, unsplit["guarantee_credit"][i])
            ):
                continue
            exempt = (
                unit["assets"]["unit_and_investment_trusts"]
                + unit["assets"]["stocks_and_shares_isa"]
            )
            difference = split[variable][i] - unsplit[variable][i]
            scale = max(split[variable][i], unsplit[variable][i])
            assert close(difference, rate * exempt, scale), (variable, unit, rate)
            cap = rate * unit["assets"]["corporate_wealth"]
            slack = 1 + 1e-6 * scale
            assert -slack <= difference <= cap + slack, (variable, unit, rate)


@PROPERTY_SETTINGS
@given(st.lists(households(), min_size=20, max_size=200))
def test_wealth_aggregates_ignore_the_components(units):
    _, itemised = calculate(units)
    _, unitemised = calculate([without_components(unit) for unit in units])
    for variable in ("total_wealth", "net_wealth", "corporate_sector_wealth"):
        assert np.array_equal(itemised[variable], unitemised[variable]), variable


@PROPERTY_SETTINGS
@given(st.lists(households(cash_only=True), min_size=20, max_size=200))
def test_cash_only_households_have_no_deduction(units):
    _, valued = calculate(units)
    _, full = calculate(units, rate=0.0)
    for variable in PROGRAMMES:
        assert np.allclose(valued[variable], full[variable]), variable
        for i, unit in enumerate(units):
            if applies(variable, unit, valued["guarantee_credit"][i]):
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
