"""Property-based tests for Universal Credit earned income before the work
allowance, and the two rules that read it (#1986, items 2 and 3).

Targeted (two-year-old) childcare tests earned income "for the purposes of
Chapter 2 of Part 6 of the Universal Credit Regulations 2013" (SI 2014/2147
reg. 1(3)(a)), and the Kingston upon Thames, Merton, Newham and Westminster
Council Tax Reduction schemes take the Secretary of State's calculation of the
claimant's income (Default Scheme para. 37). Neither subtracts the work
allowance, which is a step in the award (UC Regs 2013 reg. 22(1)(b)).

Invariants, for single people and couples with a child aged 2, earnings,
self-employment and pension contributions, in 2025, 2026 and 2027:

1. Differential against the award: uc_earned_income equals
   max(0, uc_earned_income_before_work_allowance - uc_work_allowance), so the
   award's earned income is unchanged by this PR.
2. Differential against the formula this replaced: the childcare criterion
   now implies the criterion main used (earned income after the work
   allowance at or below the limit), because earned income before the work
   allowance is never lower.
3. Monotone: more employment income for one adult never turns the childcare
   criterion on.
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
YEARS = [2025, 2026, 2027]
TENURES = ["RENT_FROM_COUNCIL", "RENT_FROM_HA", "RENT_PRIVATELY"]
VARIABLES = [
    "uc_earned_income",
    "uc_earned_income_before_work_allowance",
    "uc_work_allowance",
    "universal_credit",
    "meets_universal_credit_criteria_for_targeted_childcare_entitlement",
]


@st.composite
def adult(draw):
    return dict(
        age=draw(st.integers(18, 60)),
        employment_income=draw(
            st.one_of(st.just(0.0), st.floats(0, 40_000), st.floats(14_000, 19_000))
        ),
        self_employment_income=draw(st.one_of(st.just(0.0), st.floats(0, 10_000))),
        pension_contributions=draw(st.one_of(st.just(0.0), st.floats(0, 2_000))),
    )


@st.composite
def families(draw):
    return dict(
        adults=[draw(adult()) for _ in range(draw(st.sampled_from([1, 2])))],
        tenure=draw(st.sampled_from(TENURES)),
        rent=draw(st.floats(4_000, 20_000)),
    )


units = st.lists(families(), min_size=1, max_size=6)


def situation(units, year, bump=None):
    """One simulation holding every family. ``bump`` is (family, adult,
    amount) of extra employment income."""
    people, benunits, households = {}, {}, {}
    for i, unit in enumerate(units):
        names = []
        for j, a in enumerate(unit["adults"]):
            person = {k: {year: v} for k, v in a.items()}
            # Roles are given, not inferred; neither adult is under the
            # minimum income floor (a start-up period), so the floor does
            # not move earned income here.
            person["is_claimant_or_partner"] = {year: True}
            person["uc_is_in_startup_period"] = {year: True}
            if bump is not None and bump[:2] == (i, j):
                person["employment_income"] = {year: a["employment_income"] + bump[2]}
            people[f"p{i}_{j}"] = person
            names.append(f"p{i}_{j}")
        people[f"c{i}"] = {"age": {year: 2}, "is_claimant_or_partner": {year: False}}
        names.append(f"c{i}")
        benunits[f"b{i}"] = {"members": names, "would_claim_uc": {year: True}}
        households[f"h{i}"] = {
            "members": names,
            "tenure_type": {year: unit["tenure"]},
            "rent": {year: unit["rent"]},
            "region": {year: "NORTH_EAST"},
        }
    return {"people": people, "benunits": benunits, "households": households}


def calculate(units, year, **kwargs):
    sim = Simulation(situation=situation(units, year, **kwargs))
    values = {v: np.asarray(sim.calculate(v, year)) for v in VARIABLES}
    values["limit"] = float(
        sim.tax_benefit_system.parameters(
            f"{year}-01-01"
        ).gov.dfe.targeted_childcare_entitlement.income_limit.universal_credit
    )
    return values


@PROPERTY_SETTINGS
@given(units=units, year=st.sampled_from(YEARS))
def test_award_earned_income_is_before_work_allowance_less_the_allowance(units, year):
    v = calculate(units, year)
    expected = np.maximum(
        0, v["uc_earned_income_before_work_allowance"] - v["uc_work_allowance"]
    )
    np.testing.assert_allclose(v["uc_earned_income"], expected, atol=0.01)
    assert (
        v["uc_earned_income_before_work_allowance"] >= v["uc_earned_income"] - 0.01
    ).all()


@PROPERTY_SETTINGS
@given(units=units, year=st.sampled_from(YEARS))
def test_childcare_criterion_implies_the_old_after_allowance_test(units, year):
    v = calculate(units, year)
    old = (v["universal_credit"] > 0) & (v["uc_earned_income"] <= v["limit"])
    new = v["meets_universal_credit_criteria_for_targeted_childcare_entitlement"]
    assert not (new & ~old).any(), units
    # And the new test is exactly the regulation's: UC in payment and earned
    # income before the work allowance at or below the limit.
    expected = (v["universal_credit"] > 0) & (
        v["uc_earned_income_before_work_allowance"] <= v["limit"]
    )
    assert (new == expected).all(), units


@PROPERTY_SETTINGS
@given(
    units=units,
    year=st.sampled_from(YEARS),
    data=st.data(),
)
def test_more_pay_never_turns_the_childcare_criterion_on(units, year, data):
    i = data.draw(st.integers(0, len(units) - 1))
    j = data.draw(st.integers(0, len(units[i]["adults"]) - 1))
    amount = data.draw(st.floats(100, 5_000))
    before = calculate(units, year)
    after = calculate(units, year, bump=(i, j, amount))
    criterion = "meets_universal_credit_criteria_for_targeted_childcare_entitlement"
    assert not (after[criterion] & ~before[criterion]).any(), (units, i, j, amount)


def test_crossing_the_limit_by_one_pound_of_pay():
    """A fixed crossing, so the monotone property is not vacuous: a single
    parent aged 30 earning £16,500 (£15,399.60 after tax and NI) meets the
    2026-27 criterion, and £16,501 (£15,400.32) does not."""
    family = dict(
        adults=[
            dict(
                age=30,
                employment_income=16_500.0,
                self_employment_income=0.0,
                pension_contributions=0.0,
            )
        ],
        tenure="RENT_FROM_COUNCIL",
        rent=9_600.0,
    )
    criterion = "meets_universal_credit_criteria_for_targeted_childcare_entitlement"
    under = calculate([family], 2026)
    over = calculate([family], 2026, bump=(0, 0, 1.0))
    assert under["universal_credit"][0] > 0 and over["universal_credit"][0] > 0
    assert abs(under["uc_earned_income_before_work_allowance"][0] - 15_399.60) < 0.01
    assert under[criterion][0] and not over[criterion][0]
