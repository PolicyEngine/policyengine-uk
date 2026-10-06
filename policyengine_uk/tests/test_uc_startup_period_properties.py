"""Property-based tests for the Universal Credit start-up period that begins
when a self-employed responsible carer enters the all work-related
requirements group.

UC Regs 2013 reg. 63(1): a start-up period "is a period of 12 months and
applies from the beginning of the assessment period in which the Secretary of
State determines that a claimant is in gainful self-employment", where (a) the
minimum income floor has not applied to them before for the trade (from 23
September 2020; before then, where the trade began in the previous 12
months). Reg. 63(2) bars a second start-up period. Reg. 62(5): no floor in a
start-up period. DWP finds no claimant in the lower work-related groups
gainfully self-employed, and decides after the move into the all
work-related requirements group, as when the youngest child reaches 3 (Welfare
Reform Act 2012 s. 21(1)(aa); 5 before 3 April 2017).

Invariants, for any generated population of single people, couples and
mixed-age couples, with children of any age (often around the entry age),
disability, caring, the prescribed circumstances, employment,
self-employment, start-up periods from the data and a history that bars a
new one, in England, Wales and Scotland:

1. The test: a person is in this start-up period exactly when they are in
   the all work-related requirements group, the responsible carer, their
   youngest child has the entry age, they are in gainful self-employment,
   their history does not bar it, and the year is after reg. 63(1)(a)
   changed (differential against the rule written from its description).
   So it never applies outside the all work-related requirements group, to
   anyone but a claimant, or to more than one person in a benefit unit.
2. The floor: it applies exactly to a claimant in the all work-related
   requirements group, in gainful self-employment, in neither start-up
   period.
3. Never adds the floor: against the same people with this start-up period
   switched off (the rule before this change), the floor applies to no one
   new, the person in the start-up period has their actual earned income,
   everyone else's earned income is unchanged, and Universal Credit before
   and after the benefit cap never falls.
4. Monotone in the inputs that end a start-up period or start one: a
   history that bars it never removes the floor from anyone, and a start-up
   period from the data never adds it.
5. Monotone in earnings: more earnings never lower a benefit unit's earned
   income or raise its Universal Credit before the benefit cap. The
   intended exception is a loss raised to exactly zero, which the model
   reads as no self-employment.

Marriage Allowance is switched off throughout: a transfer can lower one
partner's earned income when the other's earnings rise.
"""

import numpy as np
from hypothesis import HealthCheck, assume, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation

PROPERTY_SETTINGS = settings(
    max_examples=10,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)
# 2016: entry at 5, and only a new trade had a start-up period. 2020: entry
# at 3, still only a new trade (parameters are read at 30 April). 2021 and
# 2026: an established trade has one.
YEARS = [2016, 2020, 2021, 2026]
REGIONS = ["LONDON", "NORTH_EAST", "WALES", "SCOTLAND"]
WORKING_AGE = st.integers(18, 64)
PENSION_AGE = st.integers(68, 80)
SHAPES = {
    "single": [WORKING_AGE],
    "couple": [WORKING_AGE, WORKING_AGE],
    "mixed_age": [PENSION_AGE, WORKING_AGE],
}
self_employment = st.one_of(
    st.just(0.0), st.floats(-10_000, 40_000), st.floats(1, 12_000)
)
employment = st.one_of(st.just(0.0), st.floats(0, 40_000))
child_ages = st.one_of(st.sampled_from([2, 3, 3, 4, 5]), st.integers(0, 15))
bumps = st.floats(1, 10_000)
rarely = st.integers(0, 5).map(lambda n: n == 0)
CIRCUMSTANCES = [
    "uc_limited_capability_for_WRA",
    "uc_has_limited_capability_for_work",
    "uc_is_in_pregnancy_or_post_confinement_period",
    "uc_is_foster_parent_or_new_friend_or_family_carer",
]
ROUTE = "uc_is_in_startup_period_on_entering_all_requirements_group"
BARRED = "uc_startup_period_barred_by_earlier_floor_or_startup"
GROUP = "uc_work_related_group_apart_from_earnings"
PERSON_VARIABLES = [
    "age",
    "is_uc_claimant",
    "uc_is_responsible_carer",
    "uc_is_in_gainful_self_employment",
    "uc_is_in_startup_period",
    BARRED,
    ROUTE,
    "uc_mif_applies",
    "uc_individual_earned_income_before_mif",
    "uc_individual_earned_income",
]
BOOLEAN_VARIABLES = [
    "is_uc_claimant",
    "uc_is_responsible_carer",
    "uc_is_in_gainful_self_employment",
    "uc_is_in_startup_period",
    BARRED,
    ROUTE,
    "uc_mif_applies",
]
BENUNIT_VARIABLES = [
    "uc_earned_income",
    "universal_credit_pre_benefit_cap",
    "universal_credit",
]


@st.composite
def families(draw):
    shape = draw(st.sampled_from(list(SHAPES)))
    adults = []
    for age in SHAPES[shape]:
        adult = dict(
            age=draw(age),
            self_employment_income=draw(self_employment),
            employment_income=draw(employment),
            uc_is_in_startup_period=draw(rarely),
            care_hours=draw(st.sampled_from([0, 0, 0, 0, 35])),
            hours_worked=draw(st.sampled_from([0, 0, 832, 1_820, 2_080])),
        )
        adult[BARRED] = draw(rarely)
        for circumstance in CIRCUMSTANCES:
            adult[circumstance] = draw(rarely)
        adults.append(adult)
    return dict(
        adults=adults,
        children=[draw(child_ages) for _ in range(draw(st.integers(0, 3)))],
        rent=draw(st.floats(0, 15_000)),
        region=draw(st.sampled_from(REGIONS)),
    )


populations = st.lists(families(), min_size=1, max_size=6)


def situation(units, year, bump=None, overrides=None):
    """One simulation holding every family.

    ``bump`` is (family index, adult index, variable, amount) to add.
    ``overrides`` maps a person's name to extra inputs.
    """
    people, benunits, households = {}, {}, {}
    for i, unit in enumerate(units):
        names = []
        for j, adult in enumerate(unit["adults"]):
            name = f"p{i}_{j}"
            person = {k: {year: v} for k, v in adult.items()}
            if bump is not None and bump[:2] == (i, j):
                variable, amount = bump[2], bump[3]
                person[variable] = {year: adult[variable] + amount}
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
            "tenure_type": {year: "RENT_FROM_COUNCIL"},
            "region": {year: unit["region"]},
        }
    for name, inputs in (overrides or {}).items():
        people[name].update({k: {year: v} for k, v in inputs.items()})
    return {"people": people, "benunits": benunits, "households": households}


def calculate(units, year, **kwargs):
    inputs = situation(units, year, **kwargs)
    sim = Simulation(situation=inputs)
    values = {v: np.asarray(sim.calculate(v, year)) for v in PERSON_VARIABLES}
    for v in BOOLEAN_VARIABLES:
        values[v] = values[v].astype(bool)
    values["group"] = np.asarray(sim.calculate(GROUP, year)).astype(str)
    for v in BENUNIT_VARIABLES:
        values[v] = np.asarray(sim.calculate(v, year))
    values["youngest"] = np.asarray(
        sim.calculate("uc_youngest_child_age", year, map_to="person")
    )
    values["names"] = list(inputs["people"])
    parameters = sim.tax_benefit_system.parameters(f"{year}-01-01")
    p = parameters.gov.dwp.universal_credit
    values["child_age"] = p.work_requirements.responsible_carer.child_age
    values["new_trade_only"] = bool(
        p.means_test.minimum_income_floor.start_up_period.requires_new_trade
    )
    values["route_in_unit"] = np.asarray(
        sim.map_result(
            sim.map_result(values[ROUTE].astype(float), "person", "benunit"),
            "benunit",
            "person",
        )
    )
    return values


def everyone(v, variable, value):
    """Overrides setting ``variable`` to ``value`` for every person."""
    return {name: {variable: value} for name in v["names"]}


@PROPERTY_SETTINGS
@given(units=populations, year=st.sampled_from(YEARS))
def test_start_up_period_is_the_legal_test(units, year):
    v = calculate(units, year)
    route = v[ROUTE]
    all_requirements = v["group"] == "ALL_REQUIREMENTS"
    child_age = v["child_age"]
    entry_age = child_age.work_preparation
    # The entry age is the highest child-age limit: below it the responsible
    # carer is in a lower group.
    assert entry_age >= child_age.interview_only >= child_age.no_requirements
    expected = (
        all_requirements
        & v["uc_is_responsible_carer"]
        & (v["youngest"] == entry_age)
        & v["uc_is_in_gainful_self_employment"]
        & ~v[BARRED]
        & (not v["new_trade_only"])
    )
    np.testing.assert_array_equal(route, expected, err_msg=str(units))
    assert np.all(all_requirements[route]), units
    assert np.all(v["is_uc_claimant"][route]), units
    assert np.all(v["route_in_unit"] <= 1), units
    # The floor: all work-related requirements, gainful self-employment, in
    # neither start-up period.
    np.testing.assert_array_equal(
        v["uc_mif_applies"],
        all_requirements
        & v["uc_is_in_gainful_self_employment"]
        & ~v["uc_is_in_startup_period"]
        & ~route,
        err_msg=str(units),
    )


@PROPERTY_SETTINGS
@given(units=populations, year=st.sampled_from(YEARS))
def test_start_up_period_never_adds_the_floor(units, year):
    v = calculate(units, year)
    # The rule before this change: no start-up period on the move.
    before = calculate(units, year, overrides=everyone(v, ROUTE, False))
    route = v[ROUTE]
    assert not np.any(v["uc_mif_applies"] & ~before["uc_mif_applies"]), units
    np.testing.assert_array_equal(
        v["uc_mif_applies"], before["uc_mif_applies"] & ~route, err_msg=str(units)
    )
    earned = v["uc_individual_earned_income"]
    np.testing.assert_allclose(
        earned[route],
        v["uc_individual_earned_income_before_mif"][route],
        atol=0.01,
        err_msg=str(units),
    )
    assert np.all(earned <= before["uc_individual_earned_income"] + 0.01), units
    # A partner's floor reads actual earnings and both thresholds, so
    # nobody else's earned income moves.
    np.testing.assert_allclose(
        earned[~route],
        before["uc_individual_earned_income"][~route],
        atol=0.01,
        err_msg=str(units),
    )
    for variable in ["universal_credit_pre_benefit_cap", "universal_credit"]:
        assert np.all(v[variable] >= before[variable] - 0.01), (variable, units)


@PROPERTY_SETTINGS
@given(units=populations, year=st.sampled_from(YEARS))
def test_monotone_in_the_inputs_that_bar_or_start_a_start_up_period(units, year):
    v = calculate(units, year)
    barred = calculate(units, year, overrides=everyone(v, BARRED, True))
    assert not barred[ROUTE].any(), units
    # A barred history ends this start-up period only: the floor never
    # leaves anyone, and comes back where this start-up period was and no
    # start-up period from the data runs.
    assert np.all(barred["uc_mif_applies"] >= v["uc_mif_applies"]), units
    np.testing.assert_array_equal(
        barred["uc_mif_applies"],
        v["uc_mif_applies"] | (v[ROUTE] & ~v["uc_is_in_startup_period"]),
        err_msg=str(units),
    )
    assert np.all(
        barred["uc_individual_earned_income"] >= v["uc_individual_earned_income"] - 0.01
    ), units
    started = calculate(
        units, year, overrides=everyone(v, "uc_is_in_startup_period", True)
    )
    assert not started["uc_mif_applies"].any(), units
    assert np.all(
        started["uc_individual_earned_income"]
        <= v["uc_individual_earned_income"] + 0.01
    ), units
    np.testing.assert_allclose(
        started["uc_individual_earned_income"],
        started["uc_individual_earned_income_before_mif"],
        atol=0.01,
        err_msg=str(units),
    )


@st.composite
def bumped(draw):
    units = draw(populations)
    i = draw(st.integers(0, len(units) - 1))
    j = draw(st.integers(0, len(units[i]["adults"]) - 1))
    variable = draw(st.sampled_from(["self_employment_income", "employment_income"]))
    amount = draw(bumps)
    # The intended exception to monotonicity: a loss raised to exactly zero.
    assume(units[i]["adults"][j][variable] + amount != 0)
    return units, (i, j, variable, amount)


@PROPERTY_SETTINGS
@given(case=bumped(), year=st.sampled_from(YEARS))
def test_more_earnings_never_lower_earned_income_or_raise_uc(case, year):
    units, bump = case
    low = calculate(units, year)
    high = calculate(units, year, bump=bump)
    assert np.all(high["uc_earned_income"] >= low["uc_earned_income"] - 0.01), (
        bump,
        units,
    )
    assert np.all(
        high["universal_credit_pre_benefit_cap"]
        <= low["universal_credit_pre_benefit_cap"] + 0.01
    ), (bump, units)
