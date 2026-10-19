"""Property-based tests for Carer's Allowance's pension contribution share.

The Carer's Allowance earnings limit tests net earnings under the Social
Security Benefit (Computation of Earnings) Regulations 1996, which deduct one
half of pension contributions from an employed earner's net earnings (reg.
10(4)(b)) and one half of pension premiums from a self-employed earner's net
profit (regs. 13(1)(b)(ii), (4)(c) and (10)(b)). Northern Ireland's 1996
Regulations (SR 1996/520) say the same. The model reads the share from
gov.dwp.carers_allowance.pension_contribution_deduction_rate.

Invariants, for any generated population of working-age carers in any UK
country and year, with pay, trading profit (a loss counts as nil) and
employee and personal pension contributions of at most 30% of earnings, so
that no floor binds:

1. Exactness: when the share moves from 0.5 to r, carers_allowance_earnings
   falls by exactly the person's contributions x (r - 0.5).
2. Locality: the Housing Benefit share is reformed at the same time to a
   different value, so earnings that read Housing Benefit's share would miss
   invariant 1.
3. Eligibility follows earnings through the limit: on both sides the person
   is gainfully employed exactly when weekly earnings, with a fraction of a
   penny disregarded (reg. 5), exceed the limit, and then has no underlying
   entitlement. A lower share can only end entitlement and a higher share can
   only restore it.
4. Current law: the share is 0.5 in every year from 2015 (the first year the
   model simulates) to 2030.
"""

import numpy as np
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation
from policyengine_uk.system import system

CA_SHARE = "gov.dwp.carers_allowance.pension_contribution_deduction_rate"
HB_SHARE = "gov.dwp.housing_benefit.means_test.pension_contribution_deduction_rate"
# Every period the model simulates.
ALL_YEARS = "2000-01-01.2100-12-31"
COUNTRIES = ["ENGLAND", "WALES", "SCOTLAND", "NORTHERN_IRELAND"]
YEARS = [2016, 2020, 2024, 2026, 2030]
# Shares on a grid of twentieths, each exact in binary.
SHARES = [i / 20 for i in range(21) if i != 10]
TOLERANCE = 0.01

PROPERTY_SETTINGS = settings(
    max_examples=6,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)


@st.composite
def carers(draw):
    pay = draw(st.floats(0, 60_000, allow_nan=False))
    profit = draw(st.floats(-20_000, 60_000, allow_nan=False))
    earnings = pay + max(0.0, profit)
    # Net earnings before the pension deduction are more than 60% of
    # earnings in every year and country tested (about 70% at the top of
    # the range), so contributions of at most 30% leave them positive at
    # any share up to one.
    employee_share = draw(st.one_of(st.just(0.0), st.floats(0, 0.15)))
    personal_share = draw(st.one_of(st.just(0.0), st.floats(0, 0.15)))
    return dict(
        country=draw(st.sampled_from(COUNTRIES)),
        age=draw(st.integers(25, 60)),
        employment_income=pay,
        self_employment_income=profit,
        employee_pension_contributions=round(pay * employee_share, 2),
        personal_pension_contributions=round(earnings * personal_share, 2),
    )


@st.composite
def reforms(draw):
    ca, hb = draw(
        st.lists(st.sampled_from(SHARES), min_size=2, max_size=2, unique=True)
    )
    return dict(ca=ca, hb=hb)


def situation(people, year):
    persons, benunits, households = {}, {}, {}
    for i, carer in enumerate(people):
        name = f"carer_{i}"
        persons[name] = {
            key: {year: value} for key, value in carer.items() if key != "country"
        }
        persons[name]["care_hours"] = {year: 40}
        benunits[f"b{i}"] = {"members": [name]}
        households[f"h{i}"] = {
            "members": [name],
            "country": {year: carer["country"]},
        }
    return {"people": persons, "benunits": benunits, "households": households}


VARIABLES = [
    "pension_contributions",
    "carers_allowance_earnings",
    "is_gainfully_employed_for_carers_allowance",
    "carers_allowance_pre_overlap",
]


def calculate(people, year, reform=None):
    sim = Simulation(situation=situation(people, year), reform=reform)
    return {v: np.asarray(sim.calculate(v, year), dtype=float) for v in VARIABLES}


def over_limit(earnings, limit):
    # Reg. 5: a fraction of a penny is disregarded.
    return np.floor(earnings / 52 * 100 + 1e-6) / 100 > limit


@PROPERTY_SETTINGS
@given(
    st.lists(carers(), min_size=1, max_size=24),
    reforms(),
    st.sampled_from(YEARS),
)
def test_earnings_fall_by_contributions_times_the_change_in_share(people, shares, year):
    base = calculate(people, year)
    moved = calculate(
        people,
        year,
        {
            CA_SHARE: {ALL_YEARS: shares["ca"]},
            HB_SHARE: {ALL_YEARS: shares["hb"]},
        },
    )
    limit = system.parameters(f"{year}-01-01").gov.dwp.carers_allowance.earnings_limit
    for i, carer in enumerate(people):
        case = (carer, shares, year)
        contributions = (
            carer["employee_pension_contributions"]
            + carer["personal_pension_contributions"]
        )
        assert abs(base["pension_contributions"][i] - contributions) < TOLERANCE, case
        if contributions > 0:
            # Floors are slack: earnings stay positive on both sides.
            assert base["carers_allowance_earnings"][i] > 0, case
            assert moved["carers_allowance_earnings"][i] > 0, case
        # Invariants 1 and 2: exactly contributions x the change in the
        # Carer's Allowance share, not the Housing Benefit share.
        change = (
            base["carers_allowance_earnings"][i] - moved["carers_allowance_earnings"][i]
        )
        assert abs(change - contributions * (shares["ca"] - 0.5)) < TOLERANCE, case
        # Invariant 3: the gainful-employment test follows earnings.
        for values in (base, moved):
            over = over_limit(values["carers_allowance_earnings"][i], limit)
            gainful = bool(values["is_gainfully_employed_for_carers_allowance"][i])
            assert gainful == over, case
            if gainful:
                assert values["carers_allowance_pre_overlap"][i] == 0, case
        was = bool(base["is_gainfully_employed_for_carers_allowance"][i])
        now = bool(moved["is_gainfully_employed_for_carers_allowance"][i])
        if shares["ca"] < 0.5:
            assert now or not was, case
        else:
            assert was or not now, case


def test_the_share_is_one_half_in_every_year():
    for year in range(2015, 2031):
        for day in ("01-01", "04-30"):
            parameters = system.parameters(f"{year}-{day}")
            share = parameters.gov.dwp.carers_allowance
            assert share.pension_contribution_deduction_rate == 0.5, (year, day)
