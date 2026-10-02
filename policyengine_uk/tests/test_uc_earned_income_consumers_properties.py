"""Property-based tests for rules that read Universal Credit earned income.

Three rules outside the UC award test a UC claimant's earned income:

- the benefit cap earnings exception (UC Regs 2013 reg. 82(1)(a)): earned
  income, without the minimum income floor (reg. 82(4)), against 16 hours a
  week at the national living wage, in whole pounds a month (reg. 6(1A)(za));
- the targeted childcare route for UC families (SI 2014/2147 reg. 1(3)):
  earned income as in UC Regs Part 6 Chapter 2, before the work allowance,
  against 15,400 a year;
- the Kingston upon Thames, Merton, Newham and Westminster council tax
  reduction schemes (Default Scheme para. 37): the Secretary of State's
  calculation of income, before the work allowance, plus the award.

Invariants, for any generated population of single people and couples with
earnings, self-employment, pension contributions, voluntary Class 3 and
taxable unearned income:

1. The benefit cap exception never depends on income tax or NI that is not
   on earnings: adding Class 3 or any unearned income to any adult leaves
   benefit_cap_earned_income and the income test unchanged, and the
   exception too wherever there is a UC award before and after.
2. Differential against the UC means test: benefit cap earned income equals
   the UC earned income before the work allowance when no one's minimum
   income floor applies, and never exceeds it; and switching every floor off
   never changes it (reg. 82(4)). The exception is the income test plus a
   UC award (reg. 82(1)), so it never applies to Housing Benefit alone.
3. The threshold is 12 x floor(12.71 x 16 x 52 / 12) in 2026-27 and the same
   formula on the national living wage parameter in every year, for every
   family.
4. Monotone in earnings: the benefit cap income test is non-decreasing, and
   the childcare criterion non-increasing, in any adult's employment income.
   A fixed example crosses the childcare limit with a UC award throughout.
5. Differential against the formulas #1986 replaced: the childcare criterion
   now implies the old criterion (earned income before the work allowance is
   never below earned income after it), and local CTR is never higher.
6. Differential against a reference: for a UC award in the four boroughs,
   council_tax_reduction equals the scheme formula recomputed from the
   model's own UC maximum amount, award and earned income.

Invariant 1 holds only while unearned income leaves the person's allowances
alone, as in test_uc_earnings_deductions_properties.py: adjusted net income
stays below the personal allowance taper, no one is old enough for the
married couple's allowance, and no one claims Marriage Allowance.
Self-employment profits are never negative, because a trading loss is netted
against employment income in uc_individual_earned_income but not in the
benefit cap measure.
"""

import numpy as np
from hypothesis import HealthCheck, example, given, settings
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
YEARS = [2020, 2024, 2025, 2026]
TENURES = ["RENT_FROM_COUNCIL", "RENT_FROM_HA", "RENT_PRIVATELY", "OWNED_OUTRIGHT"]
LOCAL_AUTHORITIES = ["MERTON", "KINGSTON_UPON_THAMES", "NEWHAM", "WESTMINSTER"]
UNEARNED = [
    "private_pension_income",
    "property_income",
    "savings_interest_income",
    "dividend_income",
]
earnings = st.one_of(st.just(0.0), st.floats(0, 30_000))
self_employment = st.one_of(st.just(0.0), st.floats(0, 20_000))
pension = st.one_of(st.just(0.0), st.floats(0, 2_000))
unearned = st.one_of(st.just(0.0), st.floats(0, 7_000))
bumps = st.floats(1, 9_000)


@st.composite
def families(draw):
    adults = []
    for _ in range(draw(st.integers(1, 2))):
        adult = dict(
            age=draw(st.integers(18, 60)),
            employment_income=draw(earnings),
            self_employment_income=draw(self_employment),
            employee_pension_contributions=draw(pension),
            ni_class_3=draw(st.one_of(st.just(0.0), st.floats(0, 950))),
            uc_is_in_startup_period=draw(st.booleans()),
        )
        for variable in UNEARNED:
            adult[variable] = draw(unearned)
        adults.append(adult)
    return dict(
        adults=adults,
        children=[draw(st.integers(0, 15)) for _ in range(draw(st.integers(0, 3)))],
        tenure=draw(st.sampled_from(TENURES)),
        rent=draw(st.floats(0, 15_000)),
        local_authority=draw(st.sampled_from(LOCAL_AUTHORITIES)),
        council_tax=draw(st.floats(500, 3_000)),
    )


def situation(units, year, bump=None, earnings_only=False, no_floor=False):
    """One simulation holding every family.

    ``bump`` is (family index, adult index, variable, amount) to add, or a
    list of them.
    ``earnings_only`` drops Class 3 and every kind of unearned income.
    ``no_floor`` puts every adult in a start-up period, so no minimum income
    floor applies.
    """
    bumps = [] if bump is None else [bump] if isinstance(bump, tuple) else bump
    people, benunits, households = {}, {}, {}
    for i, unit in enumerate(units):
        names = []
        for j, adult in enumerate(unit["adults"]):
            name = f"p{i}_{j}"
            person = {"would_claim_marriage_allowance": {year: False}}
            for variable, value in adult.items():
                if earnings_only and (variable in UNEARNED or variable == "ni_class_3"):
                    continue
                person[variable] = {year: value}
            if no_floor:
                person["uc_is_in_startup_period"] = {year: True}
            for b in bumps:
                if b[:2] == (i, j):
                    variable, amount = b[2], b[3]
                    person[variable] = {year: adult.get(variable, 0.0) + amount}
            people[name] = person
            names.append(name)
        for k, age in enumerate(unit["children"]):
            name = f"c{i}_{k}"
            people[name] = {"age": {year: age}}
            names.append(name)
        benunits[f"b{i}"] = {
            "members": names,
            "would_claim_uc": {year: True},
            "claims_all_entitled_benefits": {year: True},
        }
        households[f"h{i}"] = {
            "members": names,
            "rent": {year: unit["rent"]},
            "tenure_type": {year: unit["tenure"]},
            "country": {year: "ENGLAND"},
            "region": {year: "LONDON"},
            "local_authority": {year: unit["local_authority"]},
            "council_tax": {year: unit["council_tax"]},
            "savings": {year: 0.0},
        }
    return {"people": people, "benunits": benunits, "households": households}


BENUNIT_VARIABLES = [
    "benefit_cap_earned_income",
    "benefit_cap_earnings_threshold",
    "is_benefit_cap_exempt_earnings",
    "uc_benefit_cap_earnings_threshold_met",
    "universal_credit_pre_benefit_cap",
    "uc_earned_income_before_work_allowance",
    "uc_earned_income",
    "uc_unearned_income",
    "uc_maximum_amount",
    "universal_credit",
    "meets_universal_credit_criteria_for_targeted_childcare_entitlement",
]
# Each family is one benefit unit in its own household, so household values
# line up with benefit unit values.
HOUSEHOLD_VARIABLES = ["council_tax_reduction", "council_tax"]


def calculate(units, year, scenario=None, **kwargs):
    sim = Simulation(situation=situation(units, year, **kwargs), scenario=scenario)
    values = {}
    for v in BENUNIT_VARIABLES + HOUSEHOLD_VARIABLES:
        values[v] = np.asarray(sim.calculate(v, year))
    values["floor_applies"] = np.asarray(
        sim.map_result(
            sim.calculate("uc_mif_applies", year), "person", "benunit", "any"
        )
    )
    return values


@st.composite
def bumped(draw, variables):
    units = draw(st.lists(families(), min_size=1, max_size=8))
    i = draw(st.integers(0, len(units) - 1))
    j = draw(st.integers(0, len(units[i]["adults"]) - 1))
    return units, (i, j, draw(st.sampled_from(variables)), draw(bumps))


# Annual benefit cap earnings thresholds (12 x the monthly amount).
THRESHOLDS = {2020: 7_248, 2024: 9_516, 2025: 10_152, 2026: 10_572}


@st.composite
def near_threshold_families(draw, year):
    """A family whose one earner is just either side of the threshold, so
    that any deduction wrongly taken from earned income moves the
    exception."""
    earner = dict(
        age=draw(st.integers(18, 60)),
        employment_income=THRESHOLDS[year] + draw(st.floats(-300, 900)),
    )
    adults = [earner]
    if draw(st.booleans()):
        adults.append(dict(age=draw(st.integers(18, 60))))
    return dict(
        adults=adults,
        children=[draw(st.integers(0, 15)) for _ in range(draw(st.integers(0, 4)))],
        tenure=draw(st.sampled_from(TENURES)),
        rent=draw(st.floats(0, 15_000)),
        local_authority=draw(st.sampled_from(LOCAL_AUTHORITIES)),
        council_tax=draw(st.floats(500, 3_000)),
    )


@PROPERTY_SETTINGS
@given(year=st.sampled_from(YEARS), data=st.data())
def test_benefit_cap_exception_ignores_tax_not_on_earnings(year, data):
    units = data.draw(
        st.lists(
            st.one_of(families(), near_threshold_families(year)),
            min_size=1,
            max_size=8,
        )
    )
    # One adult in every family gets more Class 3 (up to a year's worth) or
    # unearned income large enough to be taxed, so a wrongly deducted charge
    # would move an earner near the threshold across it.
    bump = []
    for i, unit in enumerate(units):
        j = data.draw(st.integers(0, len(unit["adults"]) - 1))
        variable = data.draw(st.sampled_from(UNEARNED + ["ni_class_3"]))
        if variable == "ni_class_3":
            amount = data.draw(st.floats(500, 950))
        else:
            amount = data.draw(st.floats(2_000, 9_000))
        bump.append((i, j, variable, amount))
    low = calculate(units, year)
    high = calculate(units, year, bump=bump)
    np.testing.assert_allclose(
        high["benefit_cap_earned_income"],
        low["benefit_cap_earned_income"],
        atol=0.01,
        err_msg=f"{bump} {units}",
    )
    np.testing.assert_array_equal(
        high["uc_benefit_cap_earnings_threshold_met"],
        low["uc_benefit_cap_earnings_threshold_met"],
        err_msg=f"{bump} {units}",
    )
    # Unearned income can end the UC award, and with it the exception; where
    # there is an award either way, the exception does not move.
    on_uc = (low["universal_credit_pre_benefit_cap"] > 0) & (
        high["universal_credit_pre_benefit_cap"] > 0
    )
    np.testing.assert_array_equal(
        high["is_benefit_cap_exempt_earnings"][on_uc],
        low["is_benefit_cap_exempt_earnings"][on_uc],
        err_msg=f"{bump} {units}",
    )


@PROPERTY_SETTINGS
@given(
    units=st.lists(families(), min_size=1, max_size=8),
    year=st.sampled_from(YEARS),
)
def test_benefit_cap_earned_income_matches_uc_without_the_floor(units, year):
    v = calculate(units, year)
    cap = v["benefit_cap_earned_income"]
    uc = v["uc_earned_income_before_work_allowance"]
    no_floor = ~v["floor_applies"]
    np.testing.assert_allclose(cap[no_floor], uc[no_floor], atol=0.01, err_msg=units)
    # The exception is the income test plus an award of UC (reg. 82(1)).
    np.testing.assert_array_equal(
        v["is_benefit_cap_exempt_earnings"],
        v["uc_benefit_cap_earnings_threshold_met"]
        & (v["universal_credit_pre_benefit_cap"] > 0),
        err_msg=str(units),
    )
    assert np.all(cap <= uc + 0.01), units


@PROPERTY_SETTINGS
@given(
    units=st.lists(families(), min_size=1, max_size=8),
    year=st.sampled_from(YEARS),
)
def test_minimum_income_floor_never_counts_for_the_benefit_cap(units, year):
    with_floor = calculate(units, year)
    without_floor = calculate(units, year, no_floor=True)
    np.testing.assert_allclose(
        with_floor["benefit_cap_earned_income"],
        without_floor["benefit_cap_earned_income"],
        atol=0.01,
        err_msg=str(units),
    )


@PROPERTY_SETTINGS
@given(
    units=st.lists(families(), min_size=1, max_size=8),
    year=st.sampled_from(YEARS),
)
def test_benefit_cap_threshold_is_16_hours_at_the_living_wage(units, year):
    v = calculate(units, year)
    nlw = Simulation(situation={"people": {"p": {"age": {year: 30}}}}).calculate(
        "minimum_wage", year
    )[0]
    expected = 12 * np.floor(nlw * 16 * 52 / 12)
    np.testing.assert_allclose(v["benefit_cap_earnings_threshold"], expected)
    if year == 2026:
        np.testing.assert_allclose(v["benefit_cap_earnings_threshold"], 10_572)


CHILDCARE_LIMIT_CROSSING = (
    [
        dict(
            adults=[dict(age=30, employment_income=16_500.0)],
            children=[2],
            tenure="RENT_FROM_COUNCIL",
            rent=9_600.0,
            local_authority="MERTON",
            council_tax=1_800.0,
        )
    ],
    (0, 0, "employment_income", 1.0),
)


@PROPERTY_SETTINGS
@given(case=bumped(["employment_income"]), year=st.sampled_from(YEARS))
# Earned income goes from 15,399.60 to 15,400.32, across the 15,400 limit,
# with a UC award throughout.
@example(case=CHILDCARE_LIMIT_CROSSING, year=2026)
def test_monotone_in_earnings(case, year):
    units, bump = case
    low = calculate(units, year)
    high = calculate(units, year, bump=bump)
    # More earnings never take away the benefit cap income test...
    assert np.all(
        high["uc_benefit_cap_earnings_threshold_met"]
        >= low["uc_benefit_cap_earnings_threshold_met"]
    ), (bump, units)
    # ...and never bring a family within the childcare earnings limit. Where
    # the minimum income floor applies, the floor stands in for gross
    # earnings while the person's actual tax and NI are still deducted, so
    # more employment income can lower earned income; #1973 nets the floor
    # instead. Those families are left out here.
    criterion = "meets_universal_credit_criteria_for_targeted_childcare_entitlement"
    no_floor = ~low["floor_applies"] & ~high["floor_applies"]
    assert np.all(high[criterion][no_floor] <= low[criterion][no_floor]), (
        bump,
        units,
    )


def _use_formulas_before_1986(simulation):
    class meets_universal_credit_criteria_for_targeted_childcare_entitlement(Variable):
        value_type = bool
        entity = BenUnit
        label = "UC childcare criterion as computed before #1986"
        definition_period = YEAR

        def formula(benunit, period, parameters):
            p = parameters(period).gov.dfe.targeted_childcare_entitlement
            uc = benunit("universal_credit", period)
            earned_income = benunit("uc_earned_income", period)
            return (uc > 0) & (earned_income <= p.income_limit.universal_credit)

    class uc_earned_income_before_work_allowance(Variable):
        # Only the local CTR schemes read this variable apart from
        # uc_earned_income and the childcare criterion, so swapping it for the
        # after-work-allowance amount reproduces their old income figure.
        value_type = float
        entity = BenUnit
        label = "UC earned income as local CTR read it before #1986"
        definition_period = YEAR
        unit = GBP

        def formula(benunit, period, parameters):
            earned_income = add(benunit, period, ["uc_individual_earned_income"])
            work_allowance = benunit("uc_work_allowance", period)
            return max_(0, earned_income - work_allowance)

    class uc_earned_income(Variable):
        value_type = float
        entity = BenUnit
        label = "UC earned income (after deductions and work allowance)"
        definition_period = YEAR
        unit = GBP

        def formula(benunit, period, parameters):
            earned_income = add(benunit, period, ["uc_individual_earned_income"])
            work_allowance = benunit("uc_work_allowance", period)
            return max_(0, earned_income - work_allowance)

    system = simulation.tax_benefit_system
    system.update_variable(
        meets_universal_credit_criteria_for_targeted_childcare_entitlement
    )
    system.update_variable(uc_earned_income)
    system.update_variable(uc_earned_income_before_work_allowance)


BEFORE_1986 = Scenario(simulation_modifier=_use_formulas_before_1986)


@PROPERTY_SETTINGS
@given(
    units=st.lists(families(), min_size=1, max_size=8),
    year=st.sampled_from([2025, 2026]),
)
def test_fix_only_tightens_childcare_and_ctr(units, year):
    after = calculate(units, year)
    before = calculate(units, year, scenario=BEFORE_1986)
    # The UC award itself is unchanged.
    np.testing.assert_allclose(
        after["universal_credit"], before["universal_credit"], atol=0.01
    )
    assert np.all(
        after["uc_earned_income_before_work_allowance"]
        >= after["uc_earned_income"] - 0.01
    ), units
    criterion = "meets_universal_credit_criteria_for_targeted_childcare_entitlement"
    assert np.all(after[criterion] <= before[criterion]), units
    assert np.all(
        after["council_tax_reduction"] <= before["council_tax_reduction"] + 0.01
    ), units


# Scheme parameters: maximum support rate and taper (withdrawal rate).
SCHEMES = {
    "MERTON": "merton",
    "KINGSTON_UPON_THAMES": "kingston_upon_thames",
    "NEWHAM": "newham",
    "WESTMINSTER": "westminster",
}


@PROPERTY_SETTINGS
@given(
    units=st.lists(families(), min_size=1, max_size=8),
    year=st.sampled_from([2025, 2026]),
)
def test_local_ctr_matches_the_scheme_formula(units, year):
    # Single-adult, no non-dependant households: no non-dependant
    # deductions, so CTR for a UC award is
    # max(0, liability x maximum support rate
    #        - taper x max(0, earned income before the work allowance
    #                         + unearned income + UC - UC maximum amount)).
    v = calculate(units, year)
    system = Simulation(situation={"people": {"p": {"age": {year: 30}}}})
    parameters = system.tax_benefit_system.parameters(year).gov.local_authorities
    for k, unit in enumerate(units):
        if v["universal_credit"][k] <= 0:
            continue
        ctr = getattr(
            parameters, SCHEMES[unit["local_authority"]]
        ).council_tax_reduction
        income = (
            v["uc_earned_income_before_work_allowance"][k]
            + v["uc_unearned_income"][k]
            + v["universal_credit"][k]
        )
        excess = max(0.0, income - v["uc_maximum_amount"][k])
        expected = max(
            0.0,
            v["council_tax"][k] * ctr.maximum_support_rate
            - excess * ctr.means_test.withdrawal_rate,
        )
        np.testing.assert_allclose(
            v["council_tax_reduction"][k], expected, atol=0.01, err_msg=str(unit)
        )
