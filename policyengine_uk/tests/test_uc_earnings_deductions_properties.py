"""Property-based tests for the Universal Credit deductions from earnings.

UC Regs 2013 reg. 55(5) and reg. 57(2) deduct from a person's earnings their
own relievable pension contributions, the income tax and National Insurance
they pay in respect of their employment or trade, and payroll giving (reg.
55(5)(c), which the model does not have). The model takes
earnings as the lowest slice of the person's non-savings income, after their
allowances, with other income above it (ITA 2007 s. 16 for savings and
dividends).

Invariants, for any generated population of single people and couples with
earnings, self-employment and every kind of taxable unearned income:

1. Unearned income never changes earned income: giving any adult more State
   Pension, private pension, property, savings or dividend income leaves
   every person's uc_individual_earned_income, and so uc_earned_income,
   unchanged.
2. Monotone: the UC award, before and after the benefit cap, is
   non-increasing in each kind of unearned income for each adult.
3. Differential against the tax engine: the income tax deducted equals the
   income tax the same person pays when their earnings are their only
   income, and the NI deducted equals their NI.
4. Differential against the formula this replaced: earned income is never
   lower, and UC never higher, than when the whole benefit unit's tax was
   deducted, because only deductions were removed.

Invariants 1-3 hold only while unearned income leaves the person's
allowances alone, so the generated incomes keep adjusted net income below
the personal allowance taper (100,000) and no one claims Marriage Allowance
(see test_uc_state_pension_properties.py for the Marriage Allowance
deviation). Tax reductions are covered: adults born before 6 April 1935 can
have a married couple's allowance, which comes off the tax on earnings
first. Invariant 4 runs with Marriage Allowance claimed.
"""

import numpy as np
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation
from policyengine_uk.model_api import *
from policyengine_uk.utils.scenario import Scenario

PROPERTY_SETTINGS = settings(
    max_examples=10,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)
# 2020 has the temporary UC uplift; 2026 current rates; 2027 the new property
# and savings rates (Finance Act 2026).
YEARS = [2020, 2026, 2027]
TENURES = [
    "RENT_FROM_COUNCIL",
    "RENT_FROM_HA",
    "RENT_PRIVATELY",
    "OWNED_OUTRIGHT",
]
REGIONS = ["LONDON", "NORTH_EAST", "WALES", "SCOTLAND"]
UNEARNED = [
    "state_pension",
    "private_pension_income",
    "property_income",
    "savings_interest_income",
    "dividend_income",
]
# The married couple's allowance needs a birth before 6 April 1935.
MCA_BIRTH_YEAR = 1934
PENSION_AGE = st.integers(67, 96)
WORKING_AGE = st.integers(18, 60)
SHAPES = {
    "single": [WORKING_AGE],
    "couple": [WORKING_AGE, WORKING_AGE],
    "mixed_age": [PENSION_AGE, WORKING_AGE],
}
# Per adult: earnings up to 50,000 and unearned income up to 5 x 7,000,
# plus a bump up to 9,000, keeps adjusted net income under 100,000.
earnings = st.one_of(st.just(0.0), st.floats(0, 30_000))
self_employment = st.one_of(st.just(0.0), st.floats(0, 20_000))
unearned = st.one_of(st.just(0.0), st.floats(0, 7_000))
bumps = st.floats(1, 9_000)
UC_VARIABLES = [
    "universal_credit",
    "universal_credit_pre_benefit_cap",
    "uc_earned_income",
]
PERSON_VARIABLES = [
    "uc_individual_earned_income",
    "uc_income_tax_on_earnings",
    "uc_national_insurance_on_earnings",
    "income_tax",
    "national_insurance",
]


@st.composite
def families(draw):
    shape = draw(st.sampled_from(list(SHAPES)))
    adults = []
    for age in [draw(age) for age in SHAPES[shape]]:
        adult = dict(
            age=age,
            employment_income=draw(earnings),
            self_employment_income=draw(self_employment),
            # Some self-employed are in a start-up period, so the minimum
            # income floor does not apply.
            uc_is_in_startup_period=draw(st.booleans()),
        )
        for variable in UNEARNED:
            if variable == "state_pension" and age < 67:
                continue
            adult[variable] = draw(unearned)
        # Used only where the adult is old enough in the simulated year.
        adult["married_couples_allowance"] = draw(
            st.one_of(st.just(0.0), st.floats(0, 12_000))
        )
        adults.append(adult)
    return dict(
        adults=adults,
        children=[draw(st.integers(0, 15)) for _ in range(draw(st.integers(0, 2)))],
        tenure=draw(st.sampled_from(TENURES)),
        rent=draw(st.floats(0, 15_000)),
        region=draw(st.sampled_from(REGIONS)),
    )


def situation(units, year, bump=None, earnings_only=False, marriage_allowance=False):
    """One simulation holding every family.

    ``bump`` is (family index, adult index, variable, amount) to add.
    ``earnings_only`` drops every kind of unearned income.
    """
    people, benunits, households = {}, {}, {}
    for i, unit in enumerate(units):
        names = []
        for j, adult in enumerate(unit["adults"]):
            name = f"p{i}_{j}"
            person = {"state_pension": {year: 0.0}}
            for variable, value in adult.items():
                if earnings_only and variable in UNEARNED:
                    continue
                if variable == "married_couples_allowance" and (
                    year - adult["age"] > MCA_BIRTH_YEAR
                ):
                    continue
                person[variable] = {year: value}
            if bump is not None and bump[:2] == (i, j) and not earnings_only:
                variable, amount = bump[2], bump[3]
                person[variable] = {year: adult.get(variable, 0.0) + amount}
            if not marriage_allowance:
                person["would_claim_marriage_allowance"] = {year: False}
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
            "region": {year: unit["region"]},
        }
    return {"people": people, "benunits": benunits, "households": households}


def calculate(units, year, scenario=None, **kwargs):
    sim = Simulation(situation=situation(units, year, **kwargs), scenario=scenario)
    values = {v: np.asarray(sim.calculate(v, year)) for v in UC_VARIABLES}
    for v in PERSON_VARIABLES:
        values[v] = np.asarray(sim.calculate(v, year))
    values["is_adult_person"] = np.asarray(sim.calculate("age", year)) >= 18
    return values


@st.composite
def bumped(draw):
    units = draw(st.lists(families(), min_size=1, max_size=10))
    i = draw(st.integers(0, len(units) - 1))
    j = draw(st.integers(0, len(units[i]["adults"]) - 1))
    variables = UNEARNED if units[i]["adults"][j]["age"] >= 67 else UNEARNED[1:]
    return units, (i, j, draw(st.sampled_from(variables)), draw(bumps))


@PROPERTY_SETTINGS
@given(case=bumped(), year=st.sampled_from(YEARS))
def test_unearned_income_never_changes_earned_income(case, year):
    units, bump = case
    low = calculate(units, year)
    high = calculate(units, year, bump=bump)
    for variable in ["uc_individual_earned_income", "uc_earned_income"]:
        np.testing.assert_allclose(
            high[variable], low[variable], atol=0.01, err_msg=f"{bump} {units}"
        )


@PROPERTY_SETTINGS
@given(case=bumped(), year=st.sampled_from(YEARS))
def test_uc_is_non_increasing_in_unearned_income(case, year):
    units, bump = case
    low = calculate(units, year)
    high = calculate(units, year, bump=bump)
    for variable in ["universal_credit", "universal_credit_pre_benefit_cap"]:
        assert np.all(high[variable] <= low[variable] + 0.01), (variable, bump, units)


@PROPERTY_SETTINGS
@given(
    units=st.lists(families(), min_size=1, max_size=10),
    year=st.sampled_from(YEARS),
)
def test_deductions_equal_tax_and_ni_on_earnings_alone(units, year):
    full = calculate(units, year)
    alone = calculate(units, year, earnings_only=True)
    adult = full["is_adult_person"]
    np.testing.assert_allclose(
        full["uc_income_tax_on_earnings"][adult],
        alone["income_tax"][adult],
        atol=0.01,
        err_msg=str(units),
    )
    np.testing.assert_allclose(
        full["uc_national_insurance_on_earnings"][adult],
        alone["national_insurance"][adult],
        atol=0.01,
        err_msg=str(units),
    )
    # Never more than the person's own tax and NI.
    assert np.all(full["uc_income_tax_on_earnings"] <= full["income_tax"] + 0.01)
    assert np.all(
        full["uc_national_insurance_on_earnings"] <= full["national_insurance"] + 0.01
    )


def _use_formula_before_1942(simulation):
    class uc_earned_income(Variable):
        value_type = float
        entity = BenUnit
        label = "UC earned income as computed before #1942"
        definition_period = YEAR
        unit = GBP

        def formula(benunit, period, parameters):
            gross = add(benunit, period, ["uc_mif_capped_earned_income"])
            disregards = add(
                benunit,
                period,
                ["uc_work_allowance", "benunit_tax", "pension_contributions"],
            )
            return max_(0, gross - disregards)

    simulation.tax_benefit_system.update_variable(uc_earned_income)


BEFORE_1942 = Scenario(simulation_modifier=_use_formula_before_1942)


@PROPERTY_SETTINGS
@given(
    units=st.lists(families(), min_size=1, max_size=10),
    year=st.sampled_from(YEARS),
)
def test_fix_only_removes_deductions(units, year):
    after = calculate(units, year, marriage_allowance=True)
    before = calculate(units, year, scenario=BEFORE_1942, marriage_allowance=True)
    assert np.all(after["uc_earned_income"] >= before["uc_earned_income"] - 0.01), units
    for variable in ["universal_credit", "universal_credit_pre_benefit_cap"]:
        assert np.all(after[variable] <= before[variable] + 0.01), (variable, units)
