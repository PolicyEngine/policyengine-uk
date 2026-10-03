"""Property-based tests for the Housing Benefit earnings disregard for
specified or temporary accommodation.

SI 2006/213 Sch 4 para 18 (NI: SR 2006/405 Sch 5 para 18), in force from 5
October 2026 (SI 2026/753 reg 2(4) as substituted by SI 2026/978 reg 2(2); NI
SR 2026/157 reg 2(4)), disregards a weekly amount from the net earnings of a
claimant who lives in specified or temporary accommodation where the claimant
or partner is an employed or self-employed earner: £61.41 for a single
claimant or lone parent under 25, £77.73 at 25 or over; for a couple £97.33
where both are under 18, £61.53 where one is 18 or over but both are under
25, and £119.70 where one is 25 or over. A couple has one amount. It is added
to the £5/£10/£25 disregards (paras 10, 7 and 4), and para 17(3)(a) counts it
in the £17.10 additional disregard's earnings test. The pension-age
Regulations (SI 2006/214; NI SR 2006/406) have no such disregard.

Invariants, for 2027 (the first fiscal year the model reads with para 18 in
force), over generated populations of families not on Income Support,
income-based JSA or income-related ESA:

1. Bounds: 0 <= para 18 amount <= £119.70 x 52, and it is one of the five
   statutory amounts or zero; 0 <= total disregard <= min(net earnings,
   (£25 + £119.70 + £17.10) x 52).
2. Zero when the input is false: no para 18 amount, and the total disregard
   is what it was before para 18 (checked by setting the para 18 amount to
   zero on the same population).
3. Metamorphic: with the input true, the total disregard is non-decreasing
   in employment income.
4. Metamorphic: turning the input on never lowers the total disregard and
   never raises applicable income. This holds because every para 18 amount
   exceeds the £17.10 it can take away through para 17(3)(a); it is a
   property of the amounts, not a rule of law.
5. Differential: the model agrees with a reference written from the
   statutory text. The reference is independent for the para 18 bands and
   gates (amounts hard-coded from the instrument, ages, family type, earner
   and pension-age status from the generated inputs) and for how paras 4, 7,
   10, 17 and 18 combine. It takes net earnings, deductible childcare and
   the para 17(2) work condition from the model, which other tests cover.
   Explicit examples pin the age boundaries (couples aged 17/17, 17/18 and
   24/25; single claimants and lone parents aged 24 and 25).
6. Scope: families whose claimant and partner are all over State Pension
   age, and families in the accommodation with no earner (para 18(1)(b)),
   get no para 18 amount; a working-age family in the accommodation with an
   earner gets exactly the statutory amount.
7. Para 12: on Income Support, every family has all its net earnings
   disregarded, with or without the input.
8. Dates: no para 18 amount in any year to 2026 (the model reads 2026-27 at
   30 April 2026, before 5 October), the same amounts in every year from
   2027 to 2035 (nothing uprates them), and the parameter files start on 5
   October 2026.
"""

from pathlib import Path

import numpy as np
import yaml
from hypothesis import HealthCheck, example, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation
from policyengine_uk.system import system

YEAR = 2027
WEEKS = 52
PROPERTY_SETTINGS = settings(
    max_examples=10,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)
# Para 18(2), weekly, from the instrument (SI 2026/978 reg 2(2)).
SINGLE_UNDER_25, SINGLE_25_PLUS = 61.41, 77.73
COUPLE_BOTH_UNDER_18, COUPLE_UNDER_25, COUPLE_25_PLUS = 97.33, 61.53, 119.70
STATUTORY_WEEKLY = {
    SINGLE_UNDER_25,
    SINGLE_25_PLUS,
    COUPLE_BOTH_UNDER_18,
    COUPLE_UNDER_25,
    COUPLE_25_PLUS,
}
# Paras 4, 7 and 10, and para 17.
BASE_WEEKLY = {"single": 5, "lone_parent": 25, "couple": 10, "couple_with_children": 10}
ADDITIONAL_WEEKLY = 17.10
MAX_ANNUAL = (25 + COUPLE_25_PLUS + ADDITIONAL_WEEKLY) * WEEKS

SHAPES = {
    "single": (1, 0),
    "couple": (2, 0),
    "lone_parent": (1, 2),
    "couple_with_children": (2, 1),
}
# Working age includes the para 18(2) age boundaries; pension age is over
# State Pension age in 2027. Families are wholly one or the other.
WORKING_AGE = st.one_of(st.integers(16, 60), st.sampled_from([17, 18, 24, 25]))
PENSION_AGE = st.integers(67, 90)
HOURS = st.one_of(
    st.sampled_from([0.0, 15.0, 16.0, 29.0, 30.0]), st.floats(0, 50, allow_nan=False)
)
EARNINGS = st.one_of(
    st.just(0.0),
    st.floats(0, 3_000, allow_nan=False),
    st.floats(0, 12_000, allow_nan=False),
    st.floats(0, 60_000, allow_nan=False),
)
SELF_EMPLOYMENT = st.one_of(st.just(0.0), st.floats(0, 12_000, allow_nan=False))


@st.composite
def adults(draw, age, earns=True):
    return dict(
        age=draw(age),
        employment_income=draw(EARNINGS) if earns else 0.0,
        self_employment_income=draw(SELF_EMPLOYMENT) if earns else 0.0,
        weekly_hours=draw(HOURS),
        disabled=draw(st.booleans()),
    )


@st.composite
def families(draw, pension_age=None, accommodation=None, earners=None):
    shape = draw(st.sampled_from(sorted(SHAPES)))
    n_adults, n_children = SHAPES[shape]
    if pension_age is None:
        pension_age = draw(st.booleans())
    age = PENSION_AGE if pension_age else WORKING_AGE
    # Families without any earnings are drawn often, so that para 18(1)(b)
    # is exercised on both sides.
    if earners is None:
        earners = draw(st.booleans())
    return dict(
        shape=shape,
        pension_age=pension_age,
        accommodation=(draw(st.booleans()) if accommodation is None else accommodation),
        adults=[draw(adults(age, earners)) for _ in range(n_adults)],
        children=[draw(st.integers(0, 15)) for _ in range(n_children)],
        childcare=(
            draw(st.one_of(st.just(0.0), st.floats(0, 10_000))) if n_children else 0.0
        ),
    )


def situation(units, earnings_bump=0.0, income_support=0.0, accommodation=None):
    people, benunits, households = {}, {}, {}
    for i, unit in enumerate(units):
        names = []
        for j, adult in enumerate(unit["adults"]):
            name = f"a{i}_{j}"
            people[name] = {
                "age": {YEAR: adult["age"]},
                # Roles supplied: the model would otherwise treat a 16- or
                # 17-year-old non-head as a dependant, and a partner 20 or
                # more years younger as the claimant's child.
                "is_claimant_or_partner": {YEAR: True},
                "employment_income": {
                    YEAR: adult["employment_income"] + (earnings_bump if j == 0 else 0)
                },
                "self_employment_income": {YEAR: adult["self_employment_income"]},
                "weekly_hours": {YEAR: adult["weekly_hours"]},
                "is_disabled_for_benefits": {YEAR: adult["disabled"]},
                "childcare_expenses": {YEAR: unit["childcare"] if j == 0 else 0.0},
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
            "income_support": {YEAR: income_support},
            "jsa_income": {YEAR: 0.0},
            "esa_income": {YEAR: 0.0},
            "in_specified_or_temporary_accommodation": {
                YEAR: unit["accommodation"] if accommodation is None else accommodation
            },
        }
        households[f"h{i}"] = {"members": names}
    return {"people": people, "benunits": benunits, "households": households}


VARIABLES = [
    "housing_benefit_applicable_income_disregard",
    "housing_benefit_specified_or_temporary_accommodation_disregard",
    "housing_benefit_net_earnings",
    "housing_benefit_applicable_income",
    "housing_benefit_applicable_income_childcare_element",
    "meets_housing_benefit_additional_earnings_disregard_conditions",
    "housing_benefit_pension_age_regulations_apply",
]


def calculate(units, **kwargs):
    sim = Simulation(situation=situation(units, **kwargs))
    return {v: np.asarray(sim.calculate(v, YEAR), dtype=float) for v in VARIABLES}


def has_earner(unit):
    # Para 18(1)(b): an employed or self-employed earner.
    return any(
        adult["employment_income"] > 0 or adult["self_employment_income"] != 0
        for adult in unit["adults"]
    )


def reference_para_18_weekly(unit):
    """Para 18(1)-(2) from the statutory text, ignoring Income Support."""
    if not unit["accommodation"] or not has_earner(unit) or unit["pension_age"]:
        return 0.0
    eldest = max(adult["age"] for adult in unit["adults"])
    if unit["shape"] in ("couple", "couple_with_children"):
        if eldest >= 25:
            return COUPLE_25_PLUS
        if eldest >= 18:
            return COUPLE_UNDER_25
        return COUPLE_BOTH_UNDER_18
    return SINGLE_25_PLUS if eldest >= 25 else SINGLE_UNDER_25


def reference_disregard(unit, net, childcare, work_condition):
    """Paras 4, 7, 10, 17 and 18 combined, from net earnings, the deductible
    childcare charges and whether a para 17(2) work condition is met."""
    standard = min(BASE_WEEKLY[unit["shape"]] * WEEKS, net)
    accommodation = min(reference_para_18_weekly(unit) * WEEKS, net - standard)
    additional = ADDITIONAL_WEEKLY * WEEKS
    covers = round(net, 2) >= round(
        standard + accommodation + childcare + additional, 2
    )
    return standard + accommodation + (additional if work_condition and covers else 0)


@PROPERTY_SETTINGS
@given(st.lists(families(), min_size=1, max_size=40))
def test_bounds(units):
    values = calculate(units)
    total = values["housing_benefit_applicable_income_disregard"]
    para_18 = values["housing_benefit_specified_or_temporary_accommodation_disregard"]
    net = values["housing_benefit_net_earnings"]
    for i, unit in enumerate(units):
        assert 0 <= para_18[i] <= COUPLE_25_PLUS * WEEKS + 0.01, unit
        weekly = round(para_18[i] / WEEKS, 2)
        assert weekly == 0 or weekly in STATUTORY_WEEKLY, (unit, weekly)
        assert total[i] >= 0, unit
        assert total[i] <= min(net[i], MAX_ANNUAL) + 0.01, unit


@PROPERTY_SETTINGS
@given(st.lists(families(accommodation=False), min_size=1, max_size=40))
def test_no_para_18_amount_without_the_input(units):
    values = calculate(units)
    para_18 = values["housing_benefit_specified_or_temporary_accommodation_disregard"]
    assert (para_18 == 0).all()
    # The total is what the pre-para 18 formula gives: zeroing the amount
    # changes nothing.
    sim = Simulation(situation=situation(units))
    sim.set_input(
        "housing_benefit_specified_or_temporary_accommodation_disregard",
        YEAR,
        np.zeros(len(units)),
    )
    zeroed = np.asarray(
        sim.calculate("housing_benefit_applicable_income_disregard", YEAR)
    )
    total = values["housing_benefit_applicable_income_disregard"]
    np.testing.assert_allclose(total, zeroed, atol=0.01)


@PROPERTY_SETTINGS
@given(
    st.lists(families(accommodation=True), min_size=1, max_size=40),
    st.floats(1, 5_000, allow_nan=False, allow_infinity=False),
)
def test_disregard_is_non_decreasing_in_earnings(units, bump):
    key = "housing_benefit_applicable_income_disregard"
    before = calculate(units)[key]
    after = calculate(units, earnings_bump=bump)[key]
    for i, unit in enumerate(units):
        assert after[i] >= before[i] - 0.01, (unit, bump)


@PROPERTY_SETTINGS
@given(st.lists(families(), min_size=1, max_size=40))
def test_the_input_never_lowers_the_disregard(units):
    off = calculate(units, accommodation=False)
    on = calculate(units, accommodation=True)
    for i, unit in enumerate(units):
        key = "housing_benefit_applicable_income_disregard"
        assert on[key][i] >= off[key][i] - 0.01, unit
        income = "housing_benefit_applicable_income"
        assert on[income][i] <= off[income][i] + 0.01, unit


def boundary_family(shape, ages, children=()):
    return dict(
        shape=shape,
        pension_age=False,
        accommodation=True,
        adults=[
            dict(
                age=age,
                employment_income=10_400.0 if j == 0 else 0.0,
                self_employment_income=0.0,
                weekly_hours=30.0,
                disabled=False,
            )
            for j, age in enumerate(ages)
        ],
        children=list(children),
        childcare=0.0,
    )


BOUNDARY_FAMILIES = [
    boundary_family("couple", (17, 17)),
    boundary_family("couple", (17, 18)),
    boundary_family("couple", (24, 25)),
    boundary_family("couple_with_children", (17, 17), (1,)),
    boundary_family("single", (24,)),
    boundary_family("single", (25,)),
    boundary_family("lone_parent", (24,), (3, 5)),
    boundary_family("lone_parent", (25,), (3, 5)),
]


@PROPERTY_SETTINGS
@given(st.lists(families(), min_size=1, max_size=40))
@example(units=BOUNDARY_FAMILIES)
def test_differential_against_the_statutory_reference(units):
    values = calculate(units)
    for i, unit in enumerate(units):
        assert (
            bool(values["housing_benefit_pension_age_regulations_apply"][i])
            == (unit["pension_age"])
        ), unit
        expected_para_18 = reference_para_18_weekly(unit) * WEEKS
        para_18 = values[
            "housing_benefit_specified_or_temporary_accommodation_disregard"
        ]
        assert abs(para_18[i] - expected_para_18) < 0.01, unit
        expected = reference_disregard(
            unit,
            net=float(values["housing_benefit_net_earnings"][i]),
            childcare=float(
                values["housing_benefit_applicable_income_childcare_element"][i]
            ),
            work_condition=bool(
                values[
                    "meets_housing_benefit_additional_earnings_disregard_conditions"
                ][i]
            ),
        )
        total = values["housing_benefit_applicable_income_disregard"][i]
        assert abs(total - expected) < 0.02, (unit, total, expected)


@PROPERTY_SETTINGS
@given(
    st.lists(
        families(pension_age=False, accommodation=True, earners=False),
        min_size=1,
        max_size=40,
    )
)
def test_no_earner_has_no_para_18_amount(units):
    # Para 18(1)(b): neither the claimant nor the partner is an earner.
    values = calculate(units)
    para_18 = values["housing_benefit_specified_or_temporary_accommodation_disregard"]
    assert (para_18 == 0).all()


@PROPERTY_SETTINGS
@given(
    st.lists(
        families(pension_age=False, accommodation=True, earners=True),
        min_size=1,
        max_size=40,
    )
)
def test_working_age_earner_in_the_accommodation_has_the_statutory_amount(units):
    values = calculate(units)
    para_18 = values["housing_benefit_specified_or_temporary_accommodation_disregard"]
    for i, unit in enumerate(units):
        if not has_earner(unit):
            continue  # every drawn income was zero
        assert para_18[i] > 0, unit
        assert abs(para_18[i] - reference_para_18_weekly(unit) * WEEKS) < 0.01, unit


@PROPERTY_SETTINGS
@given(
    st.lists(families(pension_age=True, accommodation=True), min_size=1, max_size=40)
)
def test_pension_age_has_no_para_18_amount(units):
    values = calculate(units)
    para_18 = values["housing_benefit_specified_or_temporary_accommodation_disregard"]
    assert (para_18 == 0).all()


@PROPERTY_SETTINGS
@given(st.lists(families(), min_size=1, max_size=40))
def test_income_support_disregards_all_earnings(units):
    values = calculate(units, income_support=1_000)
    net = values["housing_benefit_net_earnings"]
    total = values["housing_benefit_applicable_income_disregard"]
    np.testing.assert_allclose(total, net, atol=0.01)


def test_amounts_by_year():
    for year in range(2015, 2036):
        p = system.parameters(
            year
        ).gov.dwp.housing_benefit.means_test.income_disregard.specified_or_temporary_accommodation
        amounts = (
            p.single.younger,
            p.single.older,
            p.lone_parent.younger,
            p.lone_parent.older,
            p.couple.minors,
            p.couple.younger,
            p.couple.older,
        )
        if year <= 2026:
            assert amounts == (0,) * 7, year
        else:
            assert amounts == (
                SINGLE_UNDER_25,
                SINGLE_25_PLUS,
                SINGLE_UNDER_25,
                SINGLE_25_PLUS,
                COUPLE_BOTH_UNDER_18,
                COUPLE_UNDER_25,
                COUPLE_25_PLUS,
            ), year
        assert (p.age_threshold.younger, p.age_threshold.older) == (18, 25), year


def test_parameter_files_start_on_5_october_2026():
    folder = (
        Path(__file__).parents[1]
        / "parameters/gov/dwp/housing_benefit/means_test/income_disregard"
        / "specified_or_temporary_accommodation"
    )
    files = sorted(folder.rglob("*.yaml"))
    assert len(files) == 9
    for path in files:
        values = yaml.safe_load(path.read_text())["values"]
        dates = sorted(str(date) for date in values)
        assert "2026-10-05" in dates, path
        for date in dates:
            if date < "2026-10-05":
                assert values[next(d for d in values if str(d) == date)] == 0, path
