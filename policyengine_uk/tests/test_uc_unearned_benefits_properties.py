"""Property-based tests for the reg. 66(1)(b) benefits in the UC means test.

UC Regs 2013 reg. 66(1)(b) counts contributory employment and support
allowance (ii), carer support payment up to the Carer's Allowance amount
(iiia), maternity allowance (viii) and industrial injuries benefit (ix) as
unearned income, and reg. 22(1)(a) deducts all unearned income from the
maximum amount.

Invariants, for any generated population of working-age families:

1. Monotone: the UC award, before and after the benefit cap, is
   non-increasing in each of the four benefits, the maximum amount does not
   change, and unearned income rises by exactly the amount that counts: the
   whole increase for ESA, maternity allowance and industrial injuries
   benefit, and for carer support payment the increase in
   min(component, a year of Carer's Allowance).
2. Pound for pound: with no earnings in the family, raising one of the
   benefits by d lowers the award before the benefit cap by exactly
   min(counted increase, award).
3. Equivalence: with no earnings in the family, UC before the benefit cap
   with x of the benefit equals UC with the counted amount of private pension
   received by the same person instead. For carer support payment both
   families keep the carer's caring hours, so both get the carer element.

Invariants 2 and 3 are restricted to families without earnings because the
model deducts the whole benefit unit's income tax from its earnings
(PolicyEngine/policyengine-uk#1942), so tax on a taxable benefit or pension
reduces earned income. They compare the award before the benefit cap because
contributory ESA and industrial injuries benefit trigger benefit cap
exemptions and ESA counts towards the cap, which private pension does not.
"""

import numpy as np
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation

PROPERTY_SETTINGS = settings(
    max_examples=10,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)
# 2020 has the temporary standard allowance uplift; 2025 has Carer Support
# Payment without the Scottish Carer Supplement, 2026 with it.
YEARS = [2020, 2025, 2026]
CSP_YEARS = [2025, 2026]
BENEFITS = ["esa_contrib", "maternity_allowance", "iidb"]
TENURES = [
    "RENT_FROM_COUNCIL",
    "RENT_FROM_HA",
    "RENT_PRIVATELY",
    "OWNED_OUTRIGHT",
    "OWNED_WITH_MORTGAGE",
]
WORKING_AGE = st.integers(18, 60)
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
    earnings = draw(st.one_of(st.just(0.0), money)) if with_earnings else 0.0
    return dict(
        ages=[draw(WORKING_AGE) for _ in range(draw(st.integers(1, 2)))],
        children=[draw(st.integers(0, 15)) for _ in range(draw(st.integers(0, 2)))],
        tenure=draw(st.sampled_from(TENURES)),
        rent=draw(money),
        savings=draw(st.one_of(st.just(0.0), st.floats(0, 20_000))),
        earnings=earnings,
        amount=draw(money),
    )


def situation(units, year, income_variable, bump=0.0, carer=False):
    """Build one simulation holding every family.

    The first adult receives the family's ``amount`` (plus ``bump``) under
    ``income_variable``; a partner receives the family's earnings. With
    ``carer``, the first adult cares for 40 hours a week in Scotland and has
    carer support payment set explicitly (zero unless it is the income
    variable), so the carer element applies whatever the income.
    """
    people, benunits, households = {}, {}, {}
    for i, unit in enumerate(units):
        names = []
        for j, age in enumerate(unit["ages"]):
            name = f"p{i}_{j}"
            person = {"age": {year: age}}
            if j == 0:
                if carer:
                    person["care_hours"] = {year: 40}
                    person["carer_support_payment"] = {year: 0.0}
                person[income_variable] = {year: unit["amount"] + bump}
            else:
                person["employment_income"] = {year: unit["earnings"]}
            people[name] = person
            names.append(name)
        for k, age in enumerate(unit["children"]):
            name = f"c{i}_{k}"
            people[name] = {"age": {year: age}}
            names.append(name)
        benunits[f"b{i}"] = {"members": names}
        households[f"h{i}"] = {
            "members": names,
            "rent": {year: unit["rent"]},
            "tenure_type": {year: unit["tenure"]},
            "savings": {year: unit["savings"]},
            "country": {year: "SCOTLAND" if carer else "ENGLAND"},
        }
    return {"people": people, "benunits": benunits, "households": households}


def calculate(units, year, income_variable, **kwargs):
    sim = Simulation(situation=situation(units, year, income_variable, **kwargs))
    values = {v: np.asarray(sim.calculate(v, year)) for v in UC_VARIABLES}
    counted = np.asarray(sim.calculate("uc_unearned_carer_support_payment", year))
    values["counted_csp"] = np.asarray(
        sim.map_result(counted, "person", "benunit", how="sum")
    )
    return values


def assert_same(a, b, variables, message):
    for variable in variables:
        np.testing.assert_allclose(
            a[variable], b[variable], atol=0.01, err_msg=f"{variable}: {message}"
        )


def assert_monotone(low, high, increase, units):
    for variable in ["universal_credit", "universal_credit_pre_benefit_cap"]:
        assert np.all(high[variable] <= low[variable] + 0.01), (variable, units)
    np.testing.assert_allclose(
        high["uc_maximum_amount"], low["uc_maximum_amount"], atol=0.01
    )
    np.testing.assert_allclose(
        high["uc_unearned_income"] - low["uc_unearned_income"],
        increase,
        atol=0.01,
        err_msg=str(units),
    )


@PROPERTY_SETTINGS
@given(
    units=st.lists(families(), min_size=1, max_size=20),
    benefit=st.sampled_from(BENEFITS),
    bump=st.floats(0, 20_000, allow_nan=False, allow_infinity=False),
    year=st.sampled_from(YEARS),
)
def test_uc_is_non_increasing_in_each_benefit(units, benefit, bump, year):
    low = calculate(units, year, benefit)
    high = calculate(units, year, benefit, bump=bump)
    assert_monotone(low, high, bump, units)


@PROPERTY_SETTINGS
@given(
    units=st.lists(families(), min_size=1, max_size=20),
    bump=st.floats(0, 20_000, allow_nan=False, allow_infinity=False),
    year=st.sampled_from(CSP_YEARS),
)
def test_uc_is_non_increasing_in_carer_support_payment(units, bump, year):
    low = calculate(units, year, "carer_support_payment", carer=True)
    high = calculate(units, year, "carer_support_payment", bump=bump, carer=True)
    increase = high["counted_csp"] - low["counted_csp"]
    assert np.all(increase >= -0.01), units
    assert_monotone(low, high, increase, units)


@PROPERTY_SETTINGS
@given(
    units=st.lists(families(with_earnings=False), min_size=1, max_size=20),
    benefit=st.sampled_from(BENEFITS),
    bump=st.floats(0, 20_000, allow_nan=False, allow_infinity=False),
    year=st.sampled_from(YEARS),
)
def test_uc_falls_pound_for_pound_in_each_benefit(units, benefit, bump, year):
    low = calculate(units, year, benefit)
    high = calculate(units, year, benefit, bump=bump)
    award = low["universal_credit_pre_benefit_cap"]
    np.testing.assert_allclose(
        high["universal_credit_pre_benefit_cap"],
        award - np.minimum(bump, award),
        atol=0.01,
        err_msg=str(units),
    )


@PROPERTY_SETTINGS
@given(
    units=st.lists(families(with_earnings=False), min_size=1, max_size=20),
    benefit=st.sampled_from(BENEFITS),
    year=st.sampled_from(YEARS),
)
def test_each_benefit_counts_like_private_pension(units, benefit, year):
    assert_same(
        calculate(units, year, benefit),
        calculate(units, year, "private_pension_income"),
        [v for v in UC_VARIABLES if v != "universal_credit"],
        str(units),
    )


@PROPERTY_SETTINGS
@given(
    units=st.lists(families(with_earnings=False), min_size=1, max_size=20),
    year=st.sampled_from(CSP_YEARS),
)
def test_carer_support_payment_counts_like_capped_private_pension(units, year):
    with_csp = calculate(units, year, "carer_support_payment", carer=True)
    # The same family with the counted amount of Carer Support Payment
    # received as private pension instead.
    counted = [dict(unit, amount=c) for unit, c in zip(units, with_csp["counted_csp"])]
    with_pension = calculate(counted, year, "private_pension_income", carer=True)
    assert_same(
        with_csp,
        with_pension,
        [v for v in UC_VARIABLES if v != "universal_credit"],
        str(units),
    )
