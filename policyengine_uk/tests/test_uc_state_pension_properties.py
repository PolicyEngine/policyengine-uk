"""Property-based tests for State Pension in the Universal Credit means test.

UC Regs 2013 reg. 66(1)(a) counts retirement pension income as unearned
income, and reg. 67(1) gives that phrase its State Pension Credit Act 2002
s. 16 meaning, which covers State Pension (s. 16(1)(za) and (a)) and private
pensions (s. 16(1)(f)) alike. Reg. 22(1)(a) deducts all unearned income from
the maximum amount. Only a mixed-age couple can hold both a UC award and a
State Pension, because UC needs a member under State Pension age.

Invariants, for any generated population of families:

1. Monotone: the UC award, before and after the benefit cap, is
   non-increasing in State Pension, and more State Pension adds exactly that
   much to unearned income without changing the maximum amount.
2. Pound for pound: with no earnings in the family, raising State Pension by
   d lowers the award before the benefit cap by exactly min(d, award).
3. Equivalence: UC with State Pension x equals UC with the same x of private
   pension income received by the same person instead (both are retirement
   pension income, taxed the same way).
4. Property income is outside reg. 66(1)'s list of unearned income, at any
   capital level. With no earnings, replacing State Pension x with ordinary
   property income leaves the award equal to the no-income case, while
   State Pension reduces the pre-cap award by min(x, award). Any tariff
   income from capital remains the same in all three cases.

Invariants 2 and 4 are restricted to families without earnings because the
model deducts the whole benefit unit's income tax from its earnings
(PolicyEngine/policyengine-uk#1942), so tax on State Pension reduces earned
income. Reg. 55(5)(b) and reg. 57 step 3 allow only tax paid in respect of
the employment or trade. The strict xfail below pins that case and will flip
when #1942 is fixed; widen invariants 2 and 4 to all families then.
"""

import numpy as np
import pytest
from hypothesis import HealthCheck, example, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation

PROPERTY_SETTINGS = settings(
    max_examples=10,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)
# 2020 has the temporary standard allowance uplift, 2026 the current rates.
YEARS = [2020, 2026]
TENURES = [
    "RENT_FROM_COUNCIL",
    "RENT_FROM_HA",
    "RENT_PRIVATELY",
    "OWNED_OUTRIGHT",
    "OWNED_WITH_MORTGAGE",
]
# State Pension age is 66 until 2026-27 finishes phasing up; 67 and over is
# unambiguously pension age and 60 and under unambiguously working age.
PENSION_AGE = st.integers(67, 100)
WORKING_AGE = st.integers(18, 60)
SHAPES = {
    "mixed_age": [PENSION_AGE, WORKING_AGE],
    "single_pension": [PENSION_AGE],
    "couple_pension": [PENSION_AGE, PENSION_AGE],
}
money = st.floats(0, 30_000, allow_nan=False, allow_infinity=False)
UC_VARIABLES = [
    "universal_credit",
    "universal_credit_pre_benefit_cap",
    "uc_earned_income",
    "uc_unearned_income",
    "uc_income_reduction",
    "uc_maximum_amount",
]


@st.composite
def families(draw, with_earnings=True):
    # Weight towards mixed-age couples, the only shape UC can reach.
    shape = draw(
        st.sampled_from(["mixed_age", "mixed_age", "single_pension", "couple_pension"])
    )
    earnings = draw(st.one_of(st.just(0.0), money)) if with_earnings else 0.0
    return dict(
        ages=[draw(age) for age in SHAPES[shape]],
        children=[draw(st.integers(0, 15)) for _ in range(draw(st.integers(0, 2)))],
        tenure=draw(st.sampled_from(TENURES)),
        rent=draw(money),
        savings=draw(st.one_of(st.just(0.0), st.floats(0, 20_000))),
        earnings=earnings,
        state_pension=draw(money),
    )


def situation(units, year, income_variable="state_pension", pension_bump=0.0):
    """Build one simulation holding every family.

    The eldest adult receives the family's State Pension (plus
    ``pension_bump``) under ``income_variable``; when that is not
    ``state_pension``, their State Pension is set to zero so the same amount
    arrives as the other income instead. A working-age partner receives the
    family's earnings.
    """
    people, benunits, households = {}, {}, {}
    for i, unit in enumerate(units):
        names = []
        for j, age in enumerate(unit["ages"]):
            name = f"p{i}_{j}"
            # The generated adults are the claimant and partner (a mixed-age
            # couple can include an 18- or 19-year-old partner), as the FRS
            # would record them.
            person = {
                "age": {year: age},
                "state_pension": {year: 0.0},
                "is_claimant_or_partner": {year: True},
            }
            if j == 0:
                amount = unit["state_pension"] + pension_bump
                person[income_variable] = {year: amount}
            elif age < 67:
                person["employment_income"] = {year: unit["earnings"]}
            people[name] = person
            names.append(name)
        for k, age in enumerate(unit["children"]):
            name = f"c{i}_{k}"
            people[name] = {"age": {year: age}, "is_claimant_or_partner": {year: False}}
            names.append(name)
        benunits[f"b{i}"] = {"members": names}
        households[f"h{i}"] = {
            "members": names,
            "rent": {year: unit["rent"]},
            "tenure_type": {year: unit["tenure"]},
            "savings": {year: unit["savings"]},
        }
    return {"people": people, "benunits": benunits, "households": households}


def calculate(units, year, **kwargs):
    sim = Simulation(situation=situation(units, year, **kwargs))
    return {v: np.asarray(sim.calculate(v, year)) for v in UC_VARIABLES}


def assert_same(a, b, message):
    for variable in UC_VARIABLES:
        np.testing.assert_allclose(
            a[variable], b[variable], atol=0.01, err_msg=f"{variable}: {message}"
        )


@PROPERTY_SETTINGS
@given(
    units=st.lists(families(), min_size=1, max_size=20),
    bump=st.floats(0, 20_000, allow_nan=False, allow_infinity=False),
    year=st.sampled_from(YEARS),
)
def test_uc_is_non_increasing_in_state_pension(units, bump, year):
    low = calculate(units, year)
    high = calculate(units, year, pension_bump=bump)
    for variable in ["universal_credit", "universal_credit_pre_benefit_cap"]:
        assert np.all(high[variable] <= low[variable] + 0.01), (variable, units)
    # State Pension changes nothing in the maximum amount, and all of it is
    # unearned income.
    np.testing.assert_allclose(
        high["uc_maximum_amount"], low["uc_maximum_amount"], atol=0.01
    )
    np.testing.assert_allclose(
        high["uc_unearned_income"] - low["uc_unearned_income"],
        bump,
        atol=0.01,
        err_msg=str(units),
    )
    # Families with no working-age adult never get UC.
    no_working_age_adult = np.array([min(unit["ages"]) >= 67 for unit in units])
    assert np.all(high["universal_credit"][no_working_age_adult] == 0), units


@PROPERTY_SETTINGS
@given(
    units=st.lists(families(with_earnings=False), min_size=1, max_size=20),
    bump=st.floats(0, 20_000, allow_nan=False, allow_infinity=False),
    year=st.sampled_from(YEARS),
)
def test_uc_falls_pound_for_pound_in_state_pension(units, bump, year):
    low = calculate(units, year)
    high = calculate(units, year, pension_bump=bump)
    award = low["universal_credit_pre_benefit_cap"]
    np.testing.assert_allclose(
        high["universal_credit_pre_benefit_cap"],
        award - np.minimum(bump, award),
        atol=0.01,
        err_msg=str(units),
    )


@PROPERTY_SETTINGS
@given(
    units=st.lists(families(), min_size=1, max_size=20),
    year=st.sampled_from(YEARS),
)
def test_state_pension_counts_like_private_pension(units, year):
    assert_same(
        calculate(units, year),
        calculate(units, year, income_variable="private_pension_income"),
        str(units),
    )


@PROPERTY_SETTINGS
@given(
    units=st.lists(families(with_earnings=False), min_size=1, max_size=20),
    year=st.sampled_from(YEARS),
)
@example(
    units=[
        dict(
            ages=[70, 60],
            children=[],
            tenure="RENT_FROM_COUNCIL",
            rent=6_240.0,
            savings=0.0,
            earnings=0.0,
            state_pension=9_000.0,
        )
    ],
    year=2026,
)
def test_property_income_is_excluded_while_state_pension_counts(units, year):
    pension = calculate(units, year)
    property_income = calculate(units, year, income_variable="property_income")
    without_income = calculate([{**unit, "state_pension": 0.0} for unit in units], year)
    assert_same(property_income, without_income, str(units))
    pensions = np.array([unit["state_pension"] for unit in units])
    np.testing.assert_allclose(
        pension["uc_unearned_income"] - property_income["uc_unearned_income"],
        pensions,
        atol=0.01,
        err_msg=str(units),
    )
    np.testing.assert_allclose(
        pension["universal_credit_pre_benefit_cap"],
        np.maximum(0, property_income["universal_credit_pre_benefit_cap"] - pensions),
        atol=0.01,
        err_msg=str(units),
    )


@pytest.mark.xfail(
    strict=True,
    reason=(
        "PolicyEngine/policyengine-uk#1942: uc_earned_income deducts the whole "
        "benefit unit's income tax, including the pensioner's tax on State "
        "Pension, from the partner's earnings"
    ),
)
def test_tax_on_state_pension_does_not_reduce_partners_earned_income():
    # 2026: pensioner aged 70 with State Pension 16,000 pays income tax of
    # (16,000 - 12,570) x 20% = 686. The partner aged 45 earns 13,000 and pays
    # income tax of 86 and NI of 34.40 (above the personal allowance, so no
    # marriage allowance). Council rent 20,000.
    # Earned income = 13,000 - 86 - 34.40 = 12,879.60 (reg. 55(5)(b)).
    # Maximum amount = 12 x 666.97 + 20,000 = 28,003.64.
    # UC = 28,003.64 - (0.55 x 12,879.60 + 16,000) = 4,919.86.
    unit = dict(
        ages=[70, 45],
        children=[],
        tenure="RENT_FROM_COUNCIL",
        rent=20_000.0,
        savings=0.0,
        earnings=13_000.0,
        state_pension=16_000.0,
    )
    values = calculate([unit], 2026)
    assert values["uc_earned_income"][0] == pytest.approx(12_879.60, abs=0.01)
    assert values["universal_credit"][0] == pytest.approx(4_919.86, abs=0.01)
