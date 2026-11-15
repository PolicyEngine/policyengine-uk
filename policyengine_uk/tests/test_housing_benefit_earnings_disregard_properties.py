"""Property-based tests for the Housing Benefit earnings disregards.

SI 2006/213 Sch 4 (working age) and SI 2006/214 Sch 4 (pension age) disregard
£25 a week of a lone parent's net earnings, £10 of a couple's and £5 of anyone
else's, or £20 in place of the £5 or £10 for a family that qualifies for the
special disregard (housing_benefit_special_earnings_disregard_eligible), plus the £17.10 additional earnings disregard where a work condition
is met and net earnings at least equal the other disregards, the deductible
childcare charges and £17.10. A claimant who, or whose partner, is on
Universal Credit, Income Support, income-based JSA or income-related ESA has
all earnings disregarded (SI 2006/213 Sch 4 para 12), at any age: SI 2006/213
then applies whatever the claimant's age (reg 5(1)(b)).

Invariants, for any generated population of families not on those benefits
(none claims Universal Credit):

1. Bounds: 0 <= disregard <= min(net earnings, (£25 + £17.10) x 52), and
   net earnings never exceed the claimant's and partner's gross earnings.
2. No earnings, no disregard.
3. Metamorphic: the disregard is non-decreasing in employment income.
4. The weekly amounts are the same in every year from 2015 to 2030, except
   the additional disregard in 2020-21, which SI 2020/371 reg 5 raised to
   £37.10 (an intended difference).
5. The disregard reduces applicable income by no more than the claimant's
   and partner's gross earnings, and never raises it.
6. Metamorphic: with special eligibility fixed identically false or true,
   moving every adult between working age (25 to 60) and pension age (67 to
   90) leaves every family's disregard unchanged. Earnings stay below the
   tax and National Insurance thresholds and every adult stays over 25.
   Natural eligibility is checked independently: the disability flag qualifies
   at working age, but the draws supply no pension-age qualifying receipt,
   blindness or carer premium (SI 2006/214 Sch 4 paras 4 and 5), and YEAR
   falls after tax credits end in the model (6 April 2025, tax_credits.active),
   so the disability-element route of working tax credit cannot apply. A YEAR
   before 2025-26 would need that route excluded from the draws. Lone parents
   naturally keep the same £25 even when these eligibility flags differ.
7. Differential against the old flat formula (£5/£10/£25 by family type, plus
   £37.10 for summed hours over 30, or 16 for lone parents), read without
   CPI uprating. They agree for families whose net earnings cover the flat
   amount and to whom neither formula gives the additional disregard or the
   special disregard; a couple or single person who qualifies for the special
   disregard, and whose net earnings cover £20, gets £20 instead. They
   must differ where net earnings fall below the flat amount (the new
   disregard is the net earnings) and for families without earnings (the new
   disregard is zero).
8. The selected standard is min(net earnings, 52 times the statutory weekly
   choice), with £25 lone-parent precedence, then £20 special, then £10
   couple, then £5 single. These amounts never stack and the selected
   standard stays between zero and net earnings. It is the amount before
   permitted work, whatever the permitted-work input. With a pre-assessed
   permitted-work amount above zero, the standard actually deducted is
   min(net earnings, the permitted-work amount), or for a lone parent
   min(net earnings, the larger of that amount and £25 x 52): the
   permitted-work amount replaces the £20, £10 and £5 (SI 2006/213 Sch 4
   para 10A(2), SI 2006/214 Sch 4 para 5A(2)) and is never added to them.

Para 12 is tested on its own: with Income Support, every family has all its
net earnings disregarded, at working or pension age. Leaving Income Support can
therefore lower the disregard as earnings rise; that is the law, so invariant
3 holds those benefits at zero.

The additional sum's history is tested at each up-rating: £14.50 as made,
£14.90 from April 2006 (SI 2006/645), £15.45, £16.05, £16.85, then £17.10
from April 2010, with SI 2020/371's £37.10 for 2020-21.
"""

import numpy as np
from hypothesis import HealthCheck, example, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation
from policyengine_uk.system import system

YEAR = 2026
WEEKS = 52
PROPERTY_SETTINGS = settings(
    max_examples=5,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)
# State Pension age is 66 until 2026-27 finishes phasing up; 67 and over is
# unambiguously pension age and 60 and under unambiguously working age.
ADULT_AGE = st.one_of(st.integers(18, 90), st.sampled_from([24, 25]))
SHAPES = {
    "single": (1, 0),
    "couple": (2, 0),
    "lone_parent": (1, 2),
    "couple_with_children": (2, 1),
}
HOURS = st.one_of(
    st.sampled_from([0.0, 15.0, 16.0, 29.0, 30.0]), st.floats(0, 50, allow_nan=False)
)
EARNINGS = st.one_of(
    st.just(0.0),
    st.floats(0, 3_000, allow_nan=False),
    st.floats(0, 60_000, allow_nan=False),
)
LOW_EARNINGS = st.one_of(st.just(0.0), st.floats(0, 12_000, allow_nan=False))
# A pre-assessed annual permitted-work disregard: none; 52 weeks at the £20
# exempt-work limit or at 2024-25's £183.50 limit; amounts either side of 52
# weeks of the lone parent's £25; or any amount in pence up to £20,000.
PERMITTED_WORK = st.one_of(
    st.just(0.0),
    st.sampled_from([1040.0, 1299.99, 1300.0, 1300.01, 9542.0]),
    st.integers(0, 2_000_000).map(lambda pennies: pennies / 100),
)
DISREGARD = system.parameters(YEAR).gov.dwp.housing_benefit.means_test.income_disregard
MAX_WEEKLY = max(DISREGARD.single, DISREGARD.couple, DISREGARD.lone_parent)
MAX_ANNUAL = (MAX_WEEKLY + DISREGARD.worker) * WEEKS
# The flat amounts the old formula applied before CPI uprating.
OLD_FLAT = {"single": 5, "couple": 10, "lone_parent": 25, "couple_with_children": 10}
OLD_WORKER_HOURS = {
    "single": 30,
    "couple": 30,
    "lone_parent": 16,
    "couple_with_children": 30,
}


@st.composite
def adults(draw, earnings, age):
    return dict(
        age=draw(age),
        employment_income=draw(earnings),
        weekly_hours=draw(HOURS),
        disabled=draw(st.booleans()),
        pension_contributions=draw(st.one_of(st.just(0.0), st.floats(0, 2_000))),
    )


@st.composite
def families(draw, earnings=EARNINGS, age=ADULT_AGE):
    shape = draw(st.sampled_from(sorted(SHAPES)))
    n_adults, n_children = SHAPES[shape]
    return dict(
        shape=shape,
        adults=[draw(adults(earnings, age)) for _ in range(n_adults)],
        children=[draw(st.integers(0, 15)) for _ in range(n_children)],
        childcare=(
            draw(st.one_of(st.just(0.0), st.floats(0, 10_000))) if n_children else 0.0
        ),
    )


def situation(units, earnings_bump=0.0, income_support=0.0, age_map=None):
    people, benunits, households = {}, {}, {}
    for i, unit in enumerate(units):
        names = []
        for j, adult in enumerate(unit["adults"]):
            name = f"a{i}_{j}"
            age = adult["age"] if age_map is None else age_map(adult["age"])
            people[name] = {
                "age": {YEAR: age},
                "employment_income": {
                    YEAR: adult["employment_income"] + (earnings_bump if j == 0 else 0)
                },
                "weekly_hours": {YEAR: adult["weekly_hours"]},
                "is_disabled_for_benefits": {YEAR: adult["disabled"]},
                "personal_pension_contributions": {
                    YEAR: adult["pension_contributions"]
                },
                "childcare_expenses": {YEAR: unit["childcare"] if j == 0 else 0.0},
                # The generated adults are the claimant and partner whatever
                # their age gap (or mapped ages), so the roles are supplied
                # rather than left to the age presumption.
                "is_claimant_or_partner": {YEAR: True},
            }
            names.append(name)
        for k, child_age in enumerate(unit["children"]):
            name = f"c{i}_{k}"
            people[name] = {
                "age": {YEAR: child_age},
                "is_claimant_or_partner": {YEAR: False},
            }
            names.append(name)
        benunits[f"b{i}"] = {
            "members": names,
            "would_claim_uc": {YEAR: False},
            "income_support": {YEAR: income_support},
            "jsa_income": {YEAR: 0.0},
            "esa_income": {YEAR: 0.0},
        }
        households[f"h{i}"] = {"members": names}
    return {"people": people, "benunits": benunits, "households": households}


VARIABLES = [
    "housing_benefit_applicable_income_disregard",
    "housing_benefit_net_earnings",
    "housing_benefit_applicable_income",
    "housing_benefit_applicable_income_childcare_element",
    "meets_housing_benefit_additional_earnings_disregard_conditions",
    "housing_benefit_special_earnings_disregard_eligible",
]


def calculate(units, special_eligible=None, **kwargs):
    sim = Simulation(situation=situation(units, **kwargs))
    if special_eligible is not None:
        sim.set_input(
            "housing_benefit_special_earnings_disregard_eligible",
            YEAR,
            np.full(len(units), special_eligible),
        )
    return {v: np.asarray(sim.calculate(v, YEAR), dtype=float) for v in VARIABLES}


def gross_earnings(unit):
    return sum(max(adult["employment_income"], 0) for adult in unit["adults"])


def old_flat_formula(unit):
    """The formula this PR replaces, with its parameters left at their
    2015 values instead of CPI-uprated: a flat amount by family type plus
    £37.10 where the family's summed hours exceed 30 (16 for lone parents)."""
    hours = sum(adult["weekly_hours"] for adult in unit["adults"])
    worker = hours > OLD_WORKER_HOURS[unit["shape"]]
    return (OLD_FLAT[unit["shape"]] + 37.1 * worker) * WEEKS


@PROPERTY_SETTINGS
@given(st.lists(families(), min_size=1, max_size=30))
def test_disregard_is_bounded_by_net_earnings_and_the_statutory_maximum(units):
    values = calculate(units)
    disregard = values["housing_benefit_applicable_income_disregard"]
    net = values["housing_benefit_net_earnings"]
    for i, unit in enumerate(units):
        assert disregard[i] >= 0, unit
        assert disregard[i] <= min(net[i], MAX_ANNUAL) + 0.01, unit
        assert net[i] <= gross_earnings(unit) + 0.01, unit
        if gross_earnings(unit) == 0:
            assert disregard[i] == 0, unit


@PROPERTY_SETTINGS
@given(
    st.lists(families(), min_size=1, max_size=30),
    st.floats(1, 5_000, allow_nan=False, allow_infinity=False),
)
def test_disregard_is_non_decreasing_in_earnings(units, bump):
    before = calculate(units)["housing_benefit_applicable_income_disregard"]
    after = calculate(units, earnings_bump=bump)[
        "housing_benefit_applicable_income_disregard"
    ]
    for i, unit in enumerate(units):
        assert after[i] >= before[i] - 0.01, (unit, bump)


def test_weekly_amounts_are_frozen_from_2015_to_2030():
    for year in range(2015, 2031):
        p = system.parameters(year).gov.dwp.housing_benefit.means_test.income_disregard
        assert (p.single, p.couple, p.lone_parent) == (5, 10, 25), year
        assert p.special == 20, year
        # SI 2020/371 reg 5: £37.10 from 6 April 2020 to 4 April 2021, which
        # the model's fiscal-year convention reads as 2020.
        expected_worker = 37.1 if year == 2020 else 17.1
        assert p.worker == expected_worker, year


@PROPERTY_SETTINGS
@given(st.lists(families(), min_size=1, max_size=30))
def test_disregard_lowers_applicable_income_by_no_more_than_earnings(units):
    values = calculate(units)
    sim = Simulation(situation=situation(units))
    sim.set_input(
        "housing_benefit_applicable_income_disregard", YEAR, np.zeros(len(units))
    )
    without = np.asarray(sim.calculate("housing_benefit_applicable_income", YEAR))
    with_disregard = values["housing_benefit_applicable_income"]
    for i, unit in enumerate(units):
        assert with_disregard[i] <= without[i] + 0.01, unit
        assert without[i] - with_disregard[i] <= gross_earnings(unit) + 0.01, unit


@PROPERTY_SETTINGS
@given(
    st.lists(
        families(earnings=LOW_EARNINGS, age=st.integers(25, 60)),
        max_size=30,
        min_size=1,
    )
)
@example(
    units=[
        dict(
            shape=shape,
            adults=[
                dict(
                    age=40,
                    employment_income=2_000.0,
                    weekly_hours=0.0,
                    disabled=True,
                    pension_contributions=0.0,
                )
                for _ in range(n_adults)
            ],
            children=[5] * n_children,
            childcare=0.0,
        )
        for shape, (n_adults, n_children) in SHAPES.items()
    ]
)
def test_pension_age_and_working_age_schedules_agree(units):
    working_age = calculate(units)

    # Map 25-60 onto 67-90, keeping everyone at or over 25.
    def pension_age_map(age):
        return 67 + (age - 25) * 23 // 35

    pension_age = calculate(units, age_map=pension_age_map)
    key = "housing_benefit_applicable_income_disregard"
    special = "housing_benefit_special_earnings_disregard_eligible"
    for i, unit in enumerate(units):
        assert working_age[special][i] == any(
            adult["disabled"] for adult in unit["adults"]
        ), unit
        assert not pension_age[special][i], unit
        if unit["shape"] == "lone_parent":
            assert abs(working_age[key][i] - pension_age[key][i]) < 0.01, unit

    for eligible in (False, True):
        working_age_fixed = calculate(units, special_eligible=eligible)
        pension_age_fixed = calculate(
            units, special_eligible=eligible, age_map=pension_age_map
        )
        for i, unit in enumerate(units):
            assert working_age_fixed[special][i] == eligible, unit
            assert pension_age_fixed[special][i] == eligible, unit
            assert abs(working_age_fixed[key][i] - pension_age_fixed[key][i]) < 0.01, (
                unit,
                eligible,
            )


@PROPERTY_SETTINGS
@given(
    st.lists(
        st.tuples(
            st.sampled_from(sorted(SHAPES)),
            st.integers(0, 100_000_000).map(lambda pennies: pennies / 100),
            st.booleans(),
            PERMITTED_WORK,
        ),
        min_size=1,
        max_size=30,
    )
)
@example(
    cases=[
        (shape, net, eligible, permitted)
        for shape in SHAPES
        for net in (0, 259.99, 260, 500, 520, 1039.99, 1040, 1300, 2000, 9542)
        for eligible in (False, True)
        for permitted in (0, 500, 1040, 1299.99, 1300, 1300.01, 9542)
    ]
)
def test_selected_standard_has_statutory_precedence_and_is_capped_at_net_earnings(
    cases,
):
    units = []
    for shape, _, _, _ in cases:
        n_adults, n_children = SHAPES[shape]
        units.append(
            dict(
                shape=shape,
                adults=[
                    dict(
                        age=40,
                        employment_income=0.0,
                        weekly_hours=0.0,
                        disabled=False,
                        pension_contributions=0.0,
                    )
                    for _ in range(n_adults)
                ],
                children=[5] * n_children,
                childcare=0.0,
            )
        )
    sim = Simulation(situation=situation(units))
    # Supply net earnings independently of taxes, pensions and gross income:
    # this property tests the selected standard before downstream composition.
    sim.set_input("housing_benefit_net_earnings", YEAR, [case[1] for case in cases])
    sim.set_input(
        "housing_benefit_special_earnings_disregard_eligible",
        YEAR,
        [case[2] for case in cases],
    )
    sim.set_input(
        "housing_benefit_permitted_work_disregard", YEAR, [case[3] for case in cases]
    )
    # Hold every other term at nil, so the applied disregard is the standard
    # amount after the permitted-work replacement and nothing else.
    for variable, value in (
        ("housing_benefit_specified_or_temporary_accommodation_disregard", 0.0),
        ("housing_benefit_applicable_income_childcare_element", 0.0),
        ("meets_housing_benefit_additional_earnings_disregard_conditions", False),
        ("housing_benefit_on_passporting_benefit", False),
    ):
        sim.set_input(variable, YEAR, np.full(len(cases), value))
    selected = sim.calculate("housing_benefit_special_earnings_disregard", YEAR)
    applied = sim.calculate("housing_benefit_applicable_income_disregard", YEAR)
    net_earnings = sim.calculate("housing_benefit_net_earnings", YEAR)
    permitted_work = sim.calculate("housing_benefit_permitted_work_disregard", YEAR)
    for actual, after, net, permitted, (shape, _, eligible, _) in zip(
        selected, applied, net_earnings, permitted_work, cases
    ):
        case = (shape, net, eligible, permitted)
        if shape == "lone_parent":
            weekly = 25
        elif eligible:
            weekly = 20
        elif SHAPES[shape][0] == 2:
            weekly = 10
        else:
            weekly = 5
        # The selected standard is the amount before permitted work, whatever
        # the permitted-work input.
        assert actual == min(net, WEEKS * weekly), case
        assert 0 <= actual <= net, case
        if permitted > 0:
            # Working-age para 10A(2), pension-age para 5A(2): the specified
            # amount replaces paras 3 to 10 (pension age: 1 to 5 and 7), the
            # £20 included; a lone parent keeps £25 where that is higher.
            floor = WEEKS * 25 if shape == "lone_parent" else 0
            expected = min(net, max(permitted, floor))
        else:
            expected = min(net, WEEKS * weekly)
        assert abs(after - expected) < 0.01, case
        assert -0.01 < after <= net + 0.01, case
        # Never stacked: at most the larger of the two amounts, never both.
        assert after <= max(permitted, WEEKS * weekly) + 0.01, case


@PROPERTY_SETTINGS
@given(st.lists(families(), min_size=1, max_size=30))
def test_differential_against_the_old_flat_formula(units):
    values = calculate(units)
    disregard = values["housing_benefit_applicable_income_disregard"]
    net = values["housing_benefit_net_earnings"]
    additional = values[
        "meets_housing_benefit_additional_earnings_disregard_conditions"
    ].astype(bool)
    special = values["housing_benefit_special_earnings_disregard_eligible"].astype(bool)
    for i, unit in enumerate(units):
        old = old_flat_formula(unit)
        flat = OLD_FLAT[unit["shape"]] * WEEKS
        old_worker = old > flat
        if gross_earnings(unit) == 0:
            # Must differ: the old formula disregarded the flat amount from
            # any income; the new one has no earnings to disregard.
            assert disregard[i] == 0 < old, unit
        elif net[i] < flat:
            # Must differ: the disregard is capped at net earnings.
            assert abs(disregard[i] - net[i]) < 0.01, unit
            assert disregard[i] < old, unit
        elif not old_worker and not additional[i]:
            if special[i] and unit["shape"] != "lone_parent":
                # Must differ: £20 replaces the flat £5 or £10 (lone parents
                # keep £25, which takes precedence).
                assert abs(disregard[i] - min(20 * WEEKS, net[i])) < 0.01, unit
            else:
                # Agree: the flat amount, without CPI uprating.
                assert abs(disregard[i] - old) < 0.01, unit


@PROPERTY_SETTINGS
@given(st.lists(families(), min_size=1, max_size=30))
def test_income_support_disregards_all_earnings_at_any_age(units):
    with_is = calculate(units, income_support=1_000)
    key = "housing_benefit_applicable_income_disregard"
    for i, unit in enumerate(units):
        net = with_is["housing_benefit_net_earnings"][i]
        assert abs(with_is[key][i] - net) < 0.01, unit


def test_additional_disregard_history():
    expected = {
        "2006-03-10": 14.5,
        "2006-06-01": 14.9,
        "2007-06-01": 15.45,
        "2008-06-01": 16.05,
        "2009-06-01": 16.85,
        "2010-06-01": 17.1,
        "2020-06-01": 37.1,
        "2021-06-01": 17.1,
    }
    for instant, amount in expected.items():
        p = system.parameters(instant).gov.dwp.housing_benefit.means_test
        assert p.income_disregard.worker == amount, instant


def test_a_couple_twenty_years_apart_keeps_the_couple_disregard():
    # Supplied as a couple, ages 60 and 40 keep the couple amount; without
    # roles the age presumption would read the 40-year-old as the claimant's
    # child and apply the single amount instead.
    unit = dict(
        shape="couple",
        adults=[
            dict(
                age=age,
                employment_income=income,
                weekly_hours=0,
                disabled=False,
                pension_contributions=0.0,
            )
            for age, income in ((60, 1_000.0), (40, 0.0))
        ],
        children=[],
        childcare=0.0,
    )
    values = calculate([unit])
    disregard = values["housing_benefit_applicable_income_disregard"][0]
    assert abs(disregard - DISREGARD.couple * WEEKS) < 0.01
