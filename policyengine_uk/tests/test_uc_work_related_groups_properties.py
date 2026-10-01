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
   under 16 and none otherwise; the responsible carer is always a claimant.
4. The default nomination is the one that gives the couple the higher award:
   nominating the other member never lowers the couple's combined earned
   income or raises their Universal Credit. This runs the whole model both
   ways, so it also checks the functions the default nomination evaluates
   against the variables that apply them.
5. Differential against the floor without the scope rules: the same people
   with everyone forced into the all work-related requirements group at 35
   hours (the rule before this change). The scope rules never raise anyone's
   earned income, so they never lower Universal Credit before the benefit
   cap.
6. Monotone: more earnings never lower a benefit unit's earned income or
   raise its Universal Credit before the benefit cap, whichever member the
   default nomination picks. The intended exception is a loss raised to
   exactly zero, which the model reads as no self-employment.
7. A partner who cannot be a joint claimant (reg. 3(3)) never has the floor,
   and adds the same amount to the couple threshold whatever their age.

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
    "uc_has_limited_capability_for_work",
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
    return values


@PROPERTY_SETTINGS
@given(units=populations, year=st.sampled_from(YEARS))
def test_floor_applies_only_to_the_all_requirements_group(units, year):
    v = calculate(units, year)
    applies = v["uc_mif_applies"].astype(bool)
    in_scope = (
        (v["group"] == "ALL_REQUIREMENTS")
        & v["uc_is_in_gainful_self_employment"].astype(bool)
        & ~v["uc_is_in_startup_period"].astype(bool)
    )
    np.testing.assert_array_equal(applies, in_scope, err_msg=str(units))
    # Sections 19 to 21, dependants, start-up periods: actual earned income.
    before = v["uc_individual_earned_income_before_mif"]
    after = v["uc_individual_earned_income"]
    np.testing.assert_allclose(
        after[~applies], before[~applies], atol=0.01, err_msg=str(units)
    )
    assert np.all(after >= before - 0.01), units
    # The group follows the Act for the circumstances the test sets.
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
    for i, unit in enumerate(units):
        assert has_child[v["names"].index(f"p{i}_0")] == bool(unit["children"])


def other_nomination(units, v):
    """Inputs that nominate the other member of every couple with a child."""
    overrides = {}
    for i, unit in enumerate(units):
        names = [f"p{i}_{j}" for j in range(len(unit["adults"]))]
        nominated = [
            bool(v["uc_is_responsible_carer"][v["names"].index(name)]) for name in names
        ]
        if len(names) == 2 and any(nominated):
            for name, is_nominated in zip(names, nominated):
                overrides[name] = {"uc_is_responsible_carer": not is_nominated}
    return overrides


@PROPERTY_SETTINGS
@given(units=populations, year=st.sampled_from(YEARS))
def test_default_nomination_gives_the_couple_the_higher_award(units, year):
    default = calculate(units, year)
    overrides = other_nomination(units, default)
    assume(overrides)
    other = calculate(units, year, overrides=overrides)
    assert np.all(other["uc_earned_income"] >= default["uc_earned_income"] - 0.01), (
        units
    )
    assert np.all(
        other["universal_credit_pre_benefit_cap"]
        <= default["universal_credit_pre_benefit_cap"] + 0.01
    ), units


@PROPERTY_SETTINGS
@given(units=populations, year=st.sampled_from(YEARS))
def test_scope_rules_never_raise_earned_income(units, year):
    v = calculate(units, year)
    # The floor without the scope rules: every claimant in the all
    # work-related requirements group with 35 expected hours.
    overrides = {
        name: {
            GROUP: "ALL_REQUIREMENTS" if claimant else "NOT_A_CLAIMANT",
            "uc_expected_hours": 35,
        }
        for name, claimant in zip(v["names"], v["is_uc_claimant"])
    }
    unrestricted = calculate(units, year, overrides=overrides)
    assert np.all(
        v["uc_individual_earned_income"]
        <= unrestricted["uc_individual_earned_income"] + 0.01
    ), units
    assert np.all(
        v["universal_credit_pre_benefit_cap"]
        >= unrestricted["universal_credit_pre_benefit_cap"] - 0.01
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
    # partner's age.
    np.testing.assert_allclose(
        v["uc_minimum_income_floor_gross"][ineligible],
        v["parameters"].default_expected_hours * 52 * v["national_living_wage"],
        atol=0.01,
        err_msg=str(units),
    )
