"""Property-based tests for income from capital in the Universal Credit means test.

UC Regs 2013 reg. 66(1) makes unearned income only income "falling within the
following descriptions", and no description covers actual interest, dividends
or rent (reg. 66(1)(m) reaches only ITTOIA 2005 Part 5 income; interest and
dividends are Part 4, property income Part 3). Capital counts through its
assumed yield under reg. 72(1), which reg. 66(1)(k) brings into unearned
income. Where capital is treated as yielding income, reg. 72(3) treats the
actual income derived from it as capital.
The UC Regs (NI) 2016 are the same on these points.

Invariants, for any generated population of families:

1. Single count (differential): unearned income equals the tariff income
   computed independently from reg. 72(1) on assessable capital, plus the
   other sources on the model's reg. 66(1) list, whatever interest, dividends
   and rent the family receives. So capital yield enters once, as tariff
   income. None of those three is on the list in any year.
2. Invariance: interest, dividends and rent change nothing in unearned income,
   tariff income, eligibility, the maximum amount or the award, whatever the
   family earns, because tax on them never comes off earnings (reg. 55(5)(b),
   reg. 57(2) step 3).
3. Monotone in capital: adding capital to any countable source never raises
   the award, before or after the benefit cap, and never lowers tariff
   income.

Invariant 2's award clause runs with Marriage Allowance switched off. The
model books it on the recipient as the transferor's unused personal allowance
(PolicyEngine/policyengine-uk#1947), so capital income that uses up one
partner's allowance raises the other partner's tax on earnings.
"""

import numpy as np
import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation

PROPERTY_SETTINGS = settings(
    max_examples=10,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)
# 2020 has the temporary standard allowance uplift, 2026 the current rates.
# The capital rules have not changed since 29 April 2013.
YEARS = [2020, 2026]
TENURES = [
    "RENT_FROM_COUNCIL",
    "RENT_FROM_HA",
    "RENT_PRIVATELY",
    "OWNED_OUTRIGHT",
    "OWNED_WITH_MORTGAGE",
]
REGIONS = ["LONDON", "NORTH_WEST", "WALES", "SCOTLAND", "NORTHERN_IRELAND"]
# Countable capital sources (gov.dwp.universal_credit.means_test.capital.sources).
CAPITAL_SOURCES = [
    "savings",
    "other_residential_property_value",
    "non_residential_property_value",
    "corporate_wealth",
]
CAPITAL_INCOME = ["savings_interest_income", "dividend_income", "property_income"]
# Reg. 72(1): £4.35 a month for each £250, or part of £250, above £6,000.
TARIFF_THRESHOLD, TARIFF_STEP, TARIFF_MONTHLY = 6_000, 250, 4.35

WORKING_AGE = st.integers(18, 60)
money = st.floats(0, 30_000, allow_nan=False, allow_infinity=False)
capital = st.one_of(st.just(0.0), st.floats(0, 20_000, allow_nan=False))
UC_VARIABLES = [
    "universal_credit",
    "universal_credit_pre_benefit_cap",
    "uc_earned_income",
    "uc_unearned_income",
    "uc_tariff_income",
    "uc_income_reduction",
    "uc_maximum_amount",
    "uc_assessable_capital",
    "is_uc_eligible",
]


@st.composite
def families(draw):
    earnings = draw(st.one_of(st.just(0.0), money))
    return dict(
        ages=[draw(WORKING_AGE) for _ in range(draw(st.integers(1, 2)))],
        children=[draw(st.integers(0, 15)) for _ in range(draw(st.integers(0, 2)))],
        tenure=draw(st.sampled_from(TENURES)),
        region=draw(st.sampled_from(REGIONS)),
        rent=draw(money),
        capital={source: draw(capital) for source in CAPITAL_SOURCES},
        main_residence_value=draw(st.one_of(st.just(0.0), st.floats(0, 400_000))),
        # Reported capital overrides the household proxy (-1 means unreported).
        reported_capital=draw(st.one_of(st.just(-1.0), capital)),
        earnings=earnings,
        private_pension_income=draw(st.one_of(st.just(0.0), money)),
        capital_income={variable: draw(money) for variable in CAPITAL_INCOME},
        # Which adult receives the capital income.
        recipient=draw(st.integers(0, 1)),
    )


def situation(
    units, year, income_scale=1.0, capital_bump=None, marriage_allowance=True
):
    """Build one simulation holding every family.

    ``income_scale`` multiplies each family's interest, dividends and rent;
    ``capital_bump`` is an optional (source, amount) added to every family's
    capital. With ``marriage_allowance=False`` no one claims Marriage
    Allowance.
    """
    people, benunits, households = {}, {}, {}
    for i, unit in enumerate(units):
        names = []
        for j, age in enumerate(unit["ages"]):
            name = f"p{i}_{j}"
            # The generated adults are the claimant and partner; say so, so the
            # claimant-or-partner presumption (a member under 20 and much
            # younger is the head's child) does not apply. Children get False.
            person = {"age": {year: age}, "is_claimant_or_partner": {year: True}}
            if not marriage_allowance:
                person["would_claim_marriage_allowance"] = {year: False}
            if j == 0:
                person["employment_income"] = {year: unit["earnings"]}
                person["private_pension_income"] = {
                    year: unit["private_pension_income"]
                }
            if j == min(unit["recipient"], len(unit["ages"]) - 1):
                for variable, amount in unit["capital_income"].items():
                    person[variable] = {year: amount * income_scale}
            people[name] = person
            names.append(name)
        for k, age in enumerate(unit["children"]):
            name = f"c{i}_{k}"
            people[name] = {"age": {year: age}, "is_claimant_or_partner": {year: False}}
            names.append(name)
        benunit = {"members": names}
        reported = unit["reported_capital"]
        if capital_bump is not None and reported >= 0:
            reported += capital_bump[1]
        benunit["uc_reported_capital"] = {year: reported}
        benunits[f"b{i}"] = benunit
        stocks = dict(unit["capital"])
        if capital_bump is not None:
            stocks[capital_bump[0]] += capital_bump[1]
        households[f"h{i}"] = {
            "members": names,
            "rent": {year: unit["rent"]},
            "tenure_type": {year: unit["tenure"]},
            "region": {year: unit["region"]},
            "main_residence_value": {year: unit["main_residence_value"]},
            **{source: {year: value} for source, value in stocks.items()},
        }
    return {"people": people, "benunits": benunits, "households": households}


def listed_sources(sim, year):
    """The model's reg. 66(1) list for the year, as variable names."""
    parameters = sim.tax_benefit_system.parameters(f"{year}-01-01")
    means_test = parameters.gov.dwp.universal_credit.means_test
    return list(means_test.income_definitions.unearned)


def calculate(units, year, **kwargs):
    sim = Simulation(situation=situation(units, year, **kwargs))
    values = {v: np.asarray(sim.calculate(v, year)) for v in UC_VARIABLES}
    sources = listed_sources(sim, year)
    # No actual income from capital is on the list in any year.
    assert not set(CAPITAL_INCOME) & set(sources), sources
    values["other_listed_sources"] = sum(
        np.asarray(sim.calculate(v, year, map_to="benunit"))
        for v in sources
        if v != "uc_tariff_income"
    )
    return values


def reference_tariff_income(assessable_capital, eligible):
    """Annual assumed yield under reg. 72(1), computed without the model."""
    excess = np.maximum(0.0, assessable_capital - TARIFF_THRESHOLD)
    steps = np.ceil(excess / TARIFF_STEP)
    return np.where(eligible, steps * TARIFF_MONTHLY * 12, 0.0)


@PROPERTY_SETTINGS
@given(
    units=st.lists(families(), min_size=1, max_size=20),
    year=st.sampled_from(YEARS),
)
def test_capital_yield_is_counted_once_as_tariff_income(units, year):
    values = calculate(units, year)
    eligible = values["is_uc_eligible"].astype(bool)
    tariff = reference_tariff_income(values["uc_assessable_capital"], eligible)
    np.testing.assert_allclose(
        values["uc_tariff_income"], tariff, atol=0.01, err_msg=str(units)
    )
    np.testing.assert_allclose(
        values["uc_unearned_income"],
        tariff + values["other_listed_sources"],
        atol=0.01,
        err_msg=str(units),
    )


@PROPERTY_SETTINGS
@given(
    units=st.lists(families(), min_size=1, max_size=20),
    scale=st.sampled_from([0.0, 0.5, 3.0]),
    year=st.sampled_from(YEARS),
)
def test_interest_dividends_and_rent_do_not_enter_the_means_test(units, scale, year):
    base = calculate(units, year)
    scaled = calculate(units, year, income_scale=scale)
    for variable in [
        "uc_unearned_income",
        "uc_tariff_income",
        "uc_assessable_capital",
        "is_uc_eligible",
        "uc_maximum_amount",
    ]:
        np.testing.assert_allclose(
            scaled[variable], base[variable], atol=0.01, err_msg=f"{variable}: {units}"
        )


@PROPERTY_SETTINGS
@given(
    units=st.lists(families(), min_size=1, max_size=20),
    scale=st.sampled_from([0.0, 0.5, 3.0]),
    year=st.sampled_from(YEARS),
)
def test_interest_dividends_and_rent_leave_the_award_unchanged(units, scale, year):
    base = calculate(units, year, marriage_allowance=False)
    scaled = calculate(units, year, income_scale=scale, marriage_allowance=False)
    for variable in UC_VARIABLES:
        np.testing.assert_allclose(
            scaled[variable], base[variable], atol=0.01, err_msg=f"{variable}: {units}"
        )


@PROPERTY_SETTINGS
@given(
    units=st.lists(families(), min_size=1, max_size=20),
    source=st.sampled_from(CAPITAL_SOURCES),
    bump=st.floats(0, 20_000, allow_nan=False, allow_infinity=False),
    year=st.sampled_from(YEARS),
)
def test_uc_is_non_increasing_in_capital(units, source, bump, year):
    low = calculate(units, year)
    high = calculate(units, year, capital_bump=(source, bump))
    for variable in ["universal_credit", "universal_credit_pre_benefit_cap"]:
        assert np.all(high[variable] <= low[variable] + 0.01), (variable, units)
    both_eligible = low["is_uc_eligible"].astype(bool) & high["is_uc_eligible"].astype(
        bool
    )
    assert np.all(
        high["uc_tariff_income"][both_eligible]
        >= low["uc_tariff_income"][both_eligible] - 0.01
    ), units
    # More capital never makes an ineligible family eligible.
    assert not np.any(
        high["is_uc_eligible"].astype(bool) & ~low["is_uc_eligible"].astype(bool)
    ), units


def test_tax_on_dividends_does_not_raise_a_working_familys_award():
    # 2026: single claimant aged 30 earning 10,000, under the personal
    # allowance and the NI primary threshold, so no tax or NI is paid in
    # respect of the employment. The 30,000 of dividends is taxed, but that
    # tax is not in respect of the employment (reg. 55(5)(b)), so earned
    # income stays 10,000.
    unit = dict(
        ages=[30],
        children=[],
        tenure="OWNED_OUTRIGHT",
        region="LONDON",
        rent=0.0,
        capital={source: 0.0 for source in CAPITAL_SOURCES},
        main_residence_value=0.0,
        reported_capital=-1.0,
        earnings=10_000.0,
        private_pension_income=0.0,
        capital_income={
            "savings_interest_income": 0.0,
            "dividend_income": 30_000.0,
            "property_income": 0.0,
        },
        recipient=0,
    )
    values = calculate([unit], 2026)
    assert values["uc_earned_income"][0] == pytest.approx(10_000, abs=0.01)
