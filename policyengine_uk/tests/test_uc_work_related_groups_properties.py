"""Property-based tests for the scope of the Universal Credit minimum income floor.

UC Regs 2013 reg. 62(1)(b) applies the floor only to a claimant who "would,
apart from this regulation or regulation 90, fall within section 22 of the
Act (claimants subject to all work-related requirements)". Welfare Reform Act
2012 ss. 19 to 21 take out claimants with limited capability for work or
work-related activity, carers, the responsible carer of a child under 3,
claimants over State Pension Credit qualifying age and the prescribed
descriptions of regs. 89 and 91. Regulation 88(2) lowers the expected hours of
the responsible carer of a child under 13, reg. 90(2)(a) gives a claimant who
would otherwise be in section 20 or 21 a 16-hour threshold, and only one member
of a couple is the responsible carer (reg. 86(2)).

Invariants, for any generated population of single people, couples and
mixed-age couples, with children of any age, disability, caring, the
prescribed circumstances, employment, self-employment, pension contributions
and start-up periods, in England, Wales and Scotland:

1. Scope: the floor applies only to a claimant in the all work-related
   requirements group, in gainful self-employment, outside a start-up period.
   Everyone else keeps their actual earned income, and nobody's earned income
   is lowered.
2. Thresholds: a person's gross threshold is the minimum wage for their age
   times 52 times their expected hours (section 22), 16 (sections 20 and 21)
   or nothing (section 19 and anyone who is not a claimant). Expected hours
   are 35, or the lesser number for the responsible carer of a child under
   13, and never more than 35.
3. Nomination: a benefit unit has one responsible carer if it has a child
   under 16 and none otherwise, and the responsible carer is always a
   claimant. Differential against the default rule written from its
   description: the claimant with the fewest hours of paid work, then the
   elder, then the first listed.
4. Whichever member of a couple is nominated, invariants 1 and 2 hold, and
   the nomination changes nothing in a benefit unit with no child under 13
   or no claimant the floor could apply to.
5. Differential against the floor without the scope rules: the same people
   with everyone forced into the all work-related requirements group at 35
   hours (the rule before this change). The scope rules never raise anyone's
   earned income, so they never lower Universal Credit before the benefit
   cap, under the default nomination or the other one.
6. Monotone: more earnings never lower a benefit unit's earned income or
   raise its Universal Credit before the benefit cap. The default
   nomination does not depend on earnings. The intended exception is a loss
   raised to exactly zero, which the model reads as no self-employment.
7. A partner who cannot be a joint claimant (reg. 3(3)) never has the floor,
   and adds the same amount to the couple threshold whatever their age.
8. Qualifying age (reg. 89(1)(a)): a claimant past the qualifying age for
   State Pension Credit is in section 19 whatever else applies, so never has
   the floor. For births every fifth day from 1948 to 1956, both sexes, in
   2015-16 to 2019-20, the group follows the statute's day for a woman born
   on the same day (Pensions Act 1995 Sch. 4 para. 1, read by
   test_state_pension_age). Differential against the State Pension age
   route it replaced: only claimants past the qualifying age and under State
   Pension age change group, all into section 19, all men born before 6
   December 1953, and only before 2019-20.

Marriage Allowance is switched off throughout: a transfer can lower one
partner's earned income when the other's earnings rise.
"""

from datetime import date, timedelta
from functools import lru_cache

import numpy as np
import pytest
from hypothesis import HealthCheck, assume, example, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation
from policyengine_uk.tests.test_state_pension_age import (
    grid_months,
    reference_attainment_day,
)

PROPERTY_SETTINGS = settings(
    max_examples=10,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)
# 2016: a child aged 1 or 2 puts the responsible carer in section 20 and a
# child aged 3 or 4 in section 21. 2020: sections 20 and 21 take children
# aged 1 and 2, expected hours 16 and 25. 2026: expected hours 30.
YEARS = [2016, 2020, 2026]
REGIONS = ["LONDON", "NORTH_EAST", "WALES", "SCOTLAND"]
WORKING_AGE = st.integers(18, 64)
PENSION_AGE = st.integers(68, 80)
SHAPES = {
    "single": [WORKING_AGE],
    "couple": [WORKING_AGE, WORKING_AGE],
    "mixed_age": [PENSION_AGE, WORKING_AGE],
}
self_employment = st.one_of(st.just(0.0), st.floats(-10_000, 40_000))
employment = st.one_of(st.just(0.0), st.floats(0, 40_000))
pension = st.one_of(st.just(0.0), st.floats(0, 4_000))
bumps = st.floats(1, 10_000)
rarely = st.integers(0, 5).map(lambda n: n == 0)
CIRCUMSTANCES = [
    "uc_limited_capability_for_WRA",
    "uc_limited_capability_for_work",
    "uc_is_in_pregnancy_or_post_confinement_period",
    "uc_is_adopter_in_first_year",
    "uc_is_student_with_no_work_related_requirements",
    "uc_is_responsible_foster_parent_of_child_under_one",
    "uc_is_foster_parent_or_new_friend_or_family_carer",
]
PERSON_VARIABLES = [
    "age",
    "is_uc_claimant",
    "uc_is_ineligible_partner",
    "uc_is_responsible_carer",
    "uc_is_in_gainful_self_employment",
    "uc_is_in_startup_period",
    "uc_expected_hours",
    "uc_mif_applies",
    "uc_individual_earned_income_before_mif",
    "uc_individual_earned_income",
    "uc_minimum_income_floor",
    "uc_minimum_income_floor_gross",
]
BENUNIT_VARIABLES = [
    "uc_youngest_child_age",
    "uc_earned_income",
    "universal_credit_pre_benefit_cap",
]
GROUP = "uc_work_related_group_apart_from_earnings"


@st.composite
def families(draw, ineligible_partners=False):
    shape = draw(st.sampled_from(list(SHAPES)))
    adults = []
    for age in SHAPES[shape]:
        adult = dict(
            age=draw(age),
            self_employment_income=draw(self_employment),
            employment_income=draw(employment),
            pension_contributions=draw(pension),
            uc_is_in_startup_period=draw(rarely),
            care_hours=draw(st.sampled_from([0, 0, 0, 20, 35])),
            hours_worked=draw(st.sampled_from([0, 0, 832, 1_820, 2_080])),
        )
        for circumstance in CIRCUMSTANCES:
            adult[circumstance] = draw(rarely)
        adults.append(adult)
    if ineligible_partners and shape == "couple":
        adults[1]["uc_is_ineligible_partner"] = draw(st.booleans())
    return dict(
        adults=adults,
        children=[draw(st.integers(0, 15)) for _ in range(draw(st.integers(0, 2)))],
        rent=draw(st.floats(0, 15_000)),
        region=draw(st.sampled_from(REGIONS)),
    )


populations = st.lists(families(), min_size=1, max_size=8)


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
            # The generated adults are the claimant and partner; say so, so the
            # claimant-or-partner presumption (a member under 20 and much
            # younger is the head's child) does not apply. Children get False.
            person["is_claimant_or_partner"] = {year: True}
            if bump is not None and bump[:2] == (i, j):
                variable, amount = bump[2], bump[3]
                person[variable] = {year: adult[variable] + amount}
            person["would_claim_marriage_allowance"] = {year: False}
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
    values["group"] = np.asarray(sim.calculate(GROUP, year)).astype(str)
    for v in BENUNIT_VARIABLES:
        values[v] = np.asarray(sim.calculate(v, year))
        values[f"person_{v}"] = np.asarray(sim.calculate(v, year, map_to="person"))
    values["names"] = list(inputs["people"])
    parameters = sim.tax_benefit_system.parameters(f"{year}-01-01")
    wage = parameters.gov.hmrc.minimum_wage.non_apprentice
    values["wage"] = np.asarray(wage.calc(values["age"]))
    values["national_living_wage"] = float(wage.calc(np.array([200.0]))[0])
    values["parameters"] = parameters.gov.dwp.universal_credit.work_requirements

    def per_unit(person_values):
        return np.asarray(
            sim.map_result(
                sim.map_result(person_values, "person", "benunit"),
                "benunit",
                "person",
            )
        )

    values["responsible_carers_in_unit"] = per_unit(
        values["uc_is_responsible_carer"].astype(float)
    )
    values["claimants_in_unit"] = per_unit(values["is_uc_claimant"].astype(float))
    values["self_employed_claimants_in_unit"] = per_unit(
        (
            values["uc_is_in_gainful_self_employment"].astype(bool)
            & values["is_uc_claimant"].astype(bool)
            & ~values["uc_is_in_startup_period"].astype(bool)
        ).astype(float)
    )
    return values


@PROPERTY_SETTINGS
@given(units=populations, year=st.sampled_from(YEARS))
def test_floor_applies_only_to_the_all_requirements_group(units, year):
    v = calculate(units, year)
    # Sections 19 to 21, dependants, start-up periods: actual earned income.
    check_scope(v, units)
    claimant = v["is_uc_claimant"].astype(bool)
    assert np.all(v["group"][~claimant] == "NOT_A_CLAIMANT"), units
    assert np.all(v["group"][claimant] != "NOT_A_CLAIMANT"), units


@PROPERTY_SETTINGS
@given(units=populations, year=st.sampled_from(YEARS))
def test_thresholds_follow_the_group_and_expected_hours(units, year):
    v = calculate(units, year)
    p = v["parameters"]
    hours = v["uc_expected_hours"]
    default = p.default_expected_hours
    assert np.all(hours <= default), units
    youngest = v["person_uc_youngest_child_age"]
    limit = p.responsible_carer.expected_hours.child_age_limit
    lesser = v["uc_is_responsible_carer"].astype(bool) & (youngest < limit)
    assert np.all(hours[~lesser] == default), units
    group = v["group"]
    threshold_hours = np.select(
        [
            group == "ALL_REQUIREMENTS",
            (group == "INTERVIEW_ONLY") | (group == "WORK_PREPARATION"),
        ],
        [hours, p.interview_or_preparation_threshold_hours],
        default=0,
    )
    np.testing.assert_allclose(
        v["uc_minimum_income_floor_gross"],
        v["wage"] * threshold_hours * 52,
        atol=0.01,
        err_msg=str(units),
    )
    net = v["uc_minimum_income_floor"]
    assert np.all(net <= v["uc_minimum_income_floor_gross"] + 0.01), units
    assert np.all(net >= 0), units


@PROPERTY_SETTINGS
@given(units=populations, year=st.sampled_from(YEARS))
def test_one_responsible_carer_where_there_is_a_child(units, year):
    v = calculate(units, year)
    carer = v["uc_is_responsible_carer"].astype(bool)
    assert np.all(v["is_uc_claimant"].astype(bool)[carer]), units
    has_child = v["person_uc_youngest_child_age"] < np.inf
    np.testing.assert_array_equal(
        v["responsible_carers_in_unit"],
        has_child.astype(float),
        err_msg=str(units),
    )
    # The default rule, from its description: fewest hours of paid work,
    # then the elder, then the first listed.
    for i, unit in enumerate(units):
        adults = unit["adults"]
        expected = min(
            range(len(adults)),
            key=lambda j: (adults[j]["hours_worked"], -adults[j]["age"], j),
        )
        for j in range(len(adults)):
            nominated = bool(carer[v["names"].index(f"p{i}_{j}")])
            assert nominated == (bool(unit["children"]) and j == expected), units


def other_nomination(units, v):
    """Inputs that nominate the other member of every couple with a child.

    An input set for some people sets it for everyone (the rest take the
    default, False), so every person gets one: their default nomination, or
    its opposite in a couple with a child.
    """
    nominated = v["uc_is_responsible_carer"].astype(bool)
    overrides = {
        name: {"uc_is_responsible_carer": bool(value)}
        for name, value in zip(v["names"], nominated)
    }
    flipped = False
    for i, unit in enumerate(units):
        names = [f"p{i}_{j}" for j in range(len(unit["adults"]))]
        if len(names) == 2 and unit["children"]:
            for name in names:
                overrides[name]["uc_is_responsible_carer"] ^= True
            flipped = True
    return overrides if flipped else {}


def check_scope(v, units):
    applies = v["uc_mif_applies"].astype(bool)
    in_scope = (
        (v["group"] == "ALL_REQUIREMENTS")
        & v["uc_is_in_gainful_self_employment"].astype(bool)
        & ~v["uc_is_in_startup_period"].astype(bool)
    )
    np.testing.assert_array_equal(applies, in_scope, err_msg=str(units))
    before = v["uc_individual_earned_income_before_mif"]
    after = v["uc_individual_earned_income"]
    np.testing.assert_allclose(
        after[~applies], before[~applies], atol=0.01, err_msg=str(units)
    )
    assert np.all(after >= before - 0.01), units


@PROPERTY_SETTINGS
@given(units=populations, year=st.sampled_from(YEARS))
def test_scope_holds_whichever_member_is_nominated(units, year):
    default = calculate(units, year)
    overrides = other_nomination(units, default)
    assume(overrides)
    other = calculate(units, year, overrides=overrides)
    check_scope(other, units)
    np.testing.assert_array_equal(
        other["responsible_carers_in_unit"], default["responsible_carers_in_unit"]
    )
    # The nomination matters only through a child under 13 and a claimant
    # the floor could apply to.
    limit = default["parameters"].responsible_carer.expected_hours.child_age_limit
    matters = (default["person_uc_youngest_child_age"] < limit) & (
        default["self_employed_claimants_in_unit"] > 0
    )
    np.testing.assert_allclose(
        other["uc_individual_earned_income"][~matters],
        default["uc_individual_earned_income"][~matters],
        atol=0.01,
        err_msg=str(units),
    )


def unrestricted(units, year, v):
    """The floor without the scope rules, as before this change."""
    forced = {
        name: {
            GROUP: "ALL_REQUIREMENTS" if claimant else "NOT_A_CLAIMANT",
            "uc_expected_hours": 35,
        }
        for name, claimant in zip(v["names"], v["is_uc_claimant"])
    }
    return calculate(units, year, overrides=forced)


@PROPERTY_SETTINGS
@given(units=populations, year=st.sampled_from(YEARS), other=st.booleans())
def test_scope_rules_never_raise_earned_income(units, year, other):
    v = calculate(units, year)
    before_change = unrestricted(units, year, v)
    if other:
        v = calculate(units, year, overrides=other_nomination(units, v))
    assert np.all(
        v["uc_individual_earned_income"]
        <= before_change["uc_individual_earned_income"] + 0.01
    ), units
    assert np.all(
        v["universal_credit_pre_benefit_cap"]
        >= before_change["universal_credit_pre_benefit_cap"] - 0.01
    ), units


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
    # The exception again: profits of zero raised above zero start
    # self-employment and can bring the floor; that raises earned income.
    assert np.all(high["uc_earned_income"] >= low["uc_earned_income"] - 0.01), (
        bump,
        units,
    )
    assert np.all(
        high["universal_credit_pre_benefit_cap"]
        <= low["universal_credit_pre_benefit_cap"] + 0.01
    ), (bump, units)


@PROPERTY_SETTINGS
@given(
    units=st.lists(families(ineligible_partners=True), min_size=1, max_size=8),
    year=st.sampled_from(YEARS),
)
def test_partner_who_cannot_be_a_joint_claimant(units, year):
    v = calculate(units, year)
    ineligible = v["uc_is_ineligible_partner"].astype(bool)
    assume(ineligible.any())
    assert not v["uc_mif_applies"][ineligible].any(), units
    assert np.all(v["group"][ineligible] == "NOT_A_CLAIMANT"), units
    np.testing.assert_allclose(
        v["uc_individual_earned_income"][ineligible],
        v["uc_individual_earned_income_before_mif"][ineligible],
        atol=0.01,
    )
    # Reg. 90(3)(b)(ii): 35 hours at the national living wage, whatever the
    # partner's age. The 35 is the regulation's own figure, not reg. 88's
    # expected hours.
    np.testing.assert_allclose(
        v["uc_minimum_income_floor_gross"][ineligible],
        35 * 52 * v["national_living_wage"],
        atol=0.01,
        err_msg=str(units),
    )


# Regulation 89(1)(a): "the claimant has reached the qualifying age for state
# pension credit". State Pension Credit Act 2002 s. 1(6), the meaning the
# phrase has in Welfare Reform Act 2012 s. 4(4) and so, by Interpretation Act
# 1978 s. 11, in the regulations: a woman's pensionable age, and for a man the
# pensionable age of a woman born on the same day. For a man born before 6
# December 1953 that day comes before his own State Pension age of 65 (on it,
# for a birth on 6 November 1953), so in 2015-16 to 2018-19 some claimants are
# over the one and under the other.
QUALIFYING_AGE_YEARS = [2015, 2016, 2017, 2018, 2019]
LAST_YEAR_THE_AGES_DIFFER = 2018
MALE_RULE_BORN_BEFORE = date(1953, 12, 6)
# Births every fifth day from 6 April 1948 to April 1956, and both sides of
# the 6 December 1953 boundary of Pensions Act 1995 Sch. 4 para. 1 rule (1).
QUALIFYING_AGE_BIRTHS = sorted(
    {date(1948, 4, 6) + timedelta(days=d) for d in range(0, 8 * 366, 5)}
    | {date(1953, 12, 5), date(1953, 12, 6)}
)


@lru_cache(maxsize=None)
def qualifying_age_couples():
    """Each birth date, for each sex, as the elder member of a couple whose
    partner is 40 and has no section 19 to 21 circumstance. The elder is
    listed first in each benefit unit."""
    people, benunits, households, keys = {}, {}, {}, []
    for male in (True, False):
        for birth in QUALIFYING_AGE_BIRTHS:
            elder = f"{'m' if male else 'f'}{birth:%Y%m%d}"
            partner = f"{elder}_partner"
            ages, months = {}, {}
            for year in QUALIFYING_AGE_YEARS:
                age_in_months = grid_months(date(year, 10, 6)) - grid_months(birth)
                ages[year] = int(age_in_months // 12)
                months[year] = age_in_months - 12 * ages[year]
            people[elder] = {
                "age": ages,
                "months_since_last_birthday": months,
                "is_male": {year: male for year in QUALIFYING_AGE_YEARS},
            }
            people[partner] = {
                "age": {year: 40 for year in QUALIFYING_AGE_YEARS},
                "is_male": {year: not male for year in QUALIFYING_AGE_YEARS},
            }
            benunits[f"b_{elder}"] = {"members": [elder, partner]}
            households[f"h_{elder}"] = {"members": [elder, partner]}
            keys.append((birth, male))
    situation = {"people": people, "benunits": benunits, "households": households}
    return Simulation(situation=situation), keys


@pytest.mark.parametrize("year", QUALIFYING_AGE_YEARS)
def test_regulation_89_1_a_follows_the_statute_for_every_birth_date(year):
    """The elder member is in section 19 exactly when the statute puts a woman
    born on the same day at pensionable age on or before 6 October, read with
    test_state_pension_age's reference, which shares no code with the model.
    The partner stays in section 22."""
    sim, keys = qualifying_age_couples()
    group = np.asarray(sim.calculate(GROUP, year)).astype(str)
    elder, partner = group[0::2], group[1::2]
    mid_year = date(year, 10, 6)
    mismatches = [
        (birth, male, found)
        for (birth, male), found in zip(keys, elder)
        if found
        != (
            "NO_REQUIREMENTS"
            if reference_attainment_day(birth, male=False) <= mid_year
            else "ALL_REQUIREMENTS"
        )
    ]
    assert not mismatches, mismatches[:10]
    assert np.all(partner == "ALL_REQUIREMENTS")


def test_regulation_89_1_a_differs_from_state_pension_age_only_before_2019():
    """In 2015-16 to 2018-19 some men are in section 19 by reg. 89(1)(a)
    while under their own State Pension age, and all of them were born before
    6 December 1953; from 2019-20 nobody is. Everyone over State Pension age
    is in section 19."""
    sim, keys = qualifying_age_couples()
    for year in QUALIFYING_AGE_YEARS:
        group = np.asarray(sim.calculate(GROUP, year)).astype(str)[0::2]
        sp_age = np.asarray(sim.calculate("is_SP_age", year))[0::2]
        moved = (group == "NO_REQUIREMENTS") & ~sp_age
        assert moved.any() == (year <= LAST_YEAR_THE_AGES_DIFFER), year
        assert all(
            male and birth < MALE_RULE_BORN_BEFORE
            for (birth, male), m in zip(keys, moved)
            if m
        ), year
        assert np.all(group[sp_age] == "NO_REQUIREMENTS"), year


@st.composite
def families_near_the_qualifying_age(draw):
    """A family whose first adult is 60 to 65 on 6 October, either sex."""
    unit = draw(families())
    unit["adults"][0].update(
        age=draw(st.integers(60, 65)),
        months_since_last_birthday=draw(st.integers(0, 11)),
        is_male=draw(st.booleans()),
    )
    return unit


# Born 6 April 1952: the qualifying age on 6 May 2014, State Pension age on 6
# April 2017. A self-employed man of 64 in a couple, so every run of the
# property below includes someone the change moves.
QUALIFYING_AGE_COHORT = [
    dict(
        adults=[
            dict(
                age=64,
                months_since_last_birthday=6,
                is_male=True,
                self_employment_income=5_000.0,
            ),
            dict(age=40, is_male=False),
        ],
        children=[],
        rent=0.0,
        region="LONDON",
    )
]


@PROPERTY_SETTINGS
@example(units=QUALIFYING_AGE_COHORT, year=2016)
@given(
    units=st.lists(families_near_the_qualifying_age(), min_size=1, max_size=8),
    year=st.sampled_from(QUALIFYING_AGE_YEARS[:-1]),
)
def test_qualifying_age_route_moves_only_claimants_past_it(units, year):
    """Whatever else applies, a claimant past the qualifying age is in
    section 19 and has no minimum income floor. Differential against the
    route before this change, which read State Pension age: supplying
    is_SP_age as the qualifying-age status reproduces it. Only claimants past
    the qualifying age and under State Pension age who fall in no other
    section 19 route change group, and all of them move into section 19."""
    inputs = situation(units, year)
    names = list(inputs["people"])
    sim = Simulation(situation=inputs)
    group = np.asarray(sim.calculate(GROUP, year)).astype(str)
    over = np.asarray(
        sim.calculate("has_attained_state_pension_credit_qualifying_age", year)
    )
    sp_age = np.asarray(sim.calculate("is_SP_age", year))
    claimant = group != "NOT_A_CLAIMANT"
    assert np.all(group[claimant & over] == "NO_REQUIREMENTS"), units
    assert not np.asarray(sim.calculate("uc_mif_applies", year))[over].any(), units
    overrides = {
        name: {"has_attained_state_pension_credit_qualifying_age": bool(s)}
        for name, s in zip(names, sp_age)
    }
    before = Simulation(situation=situation(units, year, overrides=overrides))
    old = np.asarray(before.calculate(GROUP, year)).astype(str)
    moved = group != old
    np.testing.assert_array_equal(
        moved,
        claimant & over & ~sp_age & (old != "NO_REQUIREMENTS"),
        err_msg=str(units),
    )
    assert np.all(group[moved] == "NO_REQUIREMENTS"), units
