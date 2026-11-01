"""Housing Benefit accommodation segments under a reform's defined_for masks.

A reform can give a Housing Benefit amount a ``defined_for`` condition and
keep the model's formula. Core then masks the annual output: the amount
where the condition holds, nil where it fails. In 2026-27 the award is
calculated separately before and after 5 October, when SI 2026/753 reg 1(1)
brings the Sch 4 para 18 accommodation disregard into force, from amounts
the segment helpers rebuild. Each helper applies the condition to its own
amount (issue #2777).

For every generated population, with or without tax credits, and any
condition on the accommodation, earnings and WTC disregards, the childcare
deduction, its limit and applicable income:

M1. Each annual disregard equals the day-weighted sum of its segment amounts.
M2. Where a condition fails, its amount is nil in the annual output and in
    every segment, unless the population supplies the amount as an input,
    which applies as supplied, as core applies it.
M3. A benefit unit whose conditions all hold has the model's outputs, award
    included.
M4. The award equals an independent calculation that applies the
    regulations within each segment, with each failed condition's amount
    nil, and combines the segments' awards by days.
M5. Each year but 2026-27 has one segment, and the award built from it
    equals the award the model builds from annual income.

The annual childcare deduction and its limit keep their single annual
calculation. Populations use core situations, as in
test_housing_benefit_wtc_disregard.py; they never load a survey dataset.
"""

from functools import cache

import numpy as np
import pytest
from hypothesis import example, given
from hypothesis import strategies as st
from policyengine_core.periods import period as period_
from policyengine_core.reforms import Reform

from policyengine_uk.model_api import BenUnit, Person, Variable, YEAR
from policyengine_uk.system import system
from policyengine_uk.tests.test_housing_benefit_wtc_disregard import (
    ACCOMMODATION,
    CHILDCARE,
    LIMIT,
    PROPERTY_SETTINGS,
    RENT,
    TOLERANCE,
    WTC_DISREGARD,
    case,
    legal_components,
    results,
    simulation,
    tax_credits_kept,
)
from policyengine_uk.tests.test_housing_benefit_wtc_disregard_segments import (
    FULL_ACCOMMODATION,
    SEGMENT_DAYS,
    SEGMENT_EDGE_CASES,
    SUPPLIED_LIMIT_SEGMENT_EDGE_CASES,
    SUPPLIED_SEGMENT_EDGE_CASES,
    WITHDRAWAL_RATE,
    segment_populations,
    specified_claimant,
)
from policyengine_uk.variables.gov.dwp.housing_benefit.applicable_income.housing_benefit_applicable_income import (
    hb_income_before_deductions,
)
from policyengine_uk.variables.gov.dwp.housing_benefit.applicable_income.housing_benefit_applicable_income_disregard import (
    hb_segment_deductions,
)
from policyengine_uk.variables.gov.dwp.housing_benefit.applicable_income.housing_benefit_specified_or_temporary_accommodation_disregard import (
    hb_accommodation_segments,
)


YEAR_WITH_SEGMENTS = 2026
EARNINGS = "housing_benefit_applicable_income_disregard"
INCOME = "housing_benefit_applicable_income"
AWARD = "housing_benefit_entitlement"
MASKED = (ACCOMMODATION, EARNINGS, WTC_DISREGARD, CHILDCARE, LIMIT, INCOME)
# The issue's claimant: a single claimant aged 40 outside specified or
# temporary accommodation, with £500 of earnings, a £260 ordinary disregard
# and £2,000 of WTC.
ISSUE_CLAIMANT = specified_claimant(specified=False)
# The same claimant paying £1,000 a year for one child's care.
CHILDCARE_CLAIMANT = specified_claimant(specified=False, children=1, childcare=1_000)


@pytest.fixture(scope="module", autouse=True)
def release_caches():
    yield
    conditioned.cache_clear()
    tax_credits_kept.cache_clear()


def baseline(active):
    """The model, with tax credits kept in 2026-27 where ``active``."""
    return tax_credits_kept() if active else system


def condition_of(name):
    return f"{name}_condition"


def masking_reform(conditions, entity=BenUnit):
    """A reform that adds each condition as an input of ``entity``, true
    unless set, and makes it the defined_for of each variable it maps to,
    keeping the model's formula."""

    class mask(Reform):
        def apply(self):
            for condition, names in conditions.items():

                class condition_variable(Variable):
                    value_type = bool
                    default_value = True
                    definition_period = YEAR
                    label = "Reform condition for Housing Benefit amounts"

                condition_variable.entity = entity
                condition_variable.__name__ = condition
                self.add_variable(condition_variable)
                for name in names:

                    class masked(Variable):
                        defined_for = condition

                    masked.__name__ = name
                    self.update_variable(masked)

    return mask


@cache
def conditioned(active):
    """The model under a reform that gives each variable in ``MASKED`` its own
    benefit-unit condition."""
    reform = masking_reform({condition_of(name): [name] for name in MASKED})
    return reform(baseline(active))


def masked_simulation(units, year, active, **options):
    """``units`` under ``conditioned``, each with the conditions it lists."""
    sim = simulation(
        units,
        year,
        tax_benefit_system=conditioned(active),
        dated_accommodation=True,
        **options,
    )
    for name in MASKED:
        sim.set_input(
            condition_of(name),
            year,
            np.array([unit["conditions"][name] for unit in units]),
        )
    return sim


def holding(unit, *failing):
    """``unit`` with every condition holding but those named."""
    return {**unit, "conditions": {name: name not in failing for name in MASKED}}


def outputs(sim, year):
    return {
        **results(sim, year),
        "accommodation": np.asarray(sim.calculate(ACCOMMODATION, year), dtype=float),
        "award": np.asarray(sim.calculate(AWARD, year), dtype=float),
    }


def segments(sim, year):
    """Each segment's share of the year and the amounts its helpers give."""
    benunit = sim.populations["benunit"]
    period = period_(year)
    parameters = sim.tax_benefit_system.parameters
    result = []
    for accommodation, share in hb_accommodation_segments(benunit, period, parameters):
        disregard, reserve, childcare = hb_segment_deductions(
            benunit, period, parameters, accommodation
        )
        result.append(
            dict(
                share=share,
                accommodation=np.asarray(accommodation, dtype=float),
                earnings_disregard=np.asarray(disregard, dtype=float),
                reserve=np.asarray(reserve, dtype=float),
                childcare=np.asarray(childcare, dtype=float),
            )
        )
    return result


def day_weighted(segment_list, key):
    return sum(segment["share"] * segment[key] for segment in segment_list)


def assert_close(actual, expected, message=""):
    np.testing.assert_allclose(
        actual, expected, rtol=0, atol=TOLERANCE, err_msg=message
    )


def legal_masked_award(unit, active):
    """Apply the regulations within each segment of 2026-27 to scalar
    assessed inputs, as test_housing_benefit_wtc_disregard_segments.py does,
    with each failed condition's amount nil, then combine the awards by days.
    A failed condition on the accommodation disregard, the childcare
    deduction or its limit removes that amount before the earnings tests;
    one on the earnings or WTC disregard, or on applicable income, removes it
    from income. A supplied deduction or limit applies as supplied."""
    holds = unit["conditions"]
    awards = []
    for in_force in (False, True):
        applies = (
            in_force
            and unit["specified"]
            and unit["net"] > 0
            and not unit["pension_age"]
            and holds[ACCOMMODATION]
        )
        segment = {**unit, "accommodation": FULL_ACCOMMODATION if applies else 0}
        if unit["supplied"] is None and not holds[CHILDCARE]:
            segment["supplied"] = 0
        elif (
            unit["supplied"] is None
            and unit["supplied_limit"] is None
            and not holds[LIMIT]
        ):
            segment["supplied_limit"] = 0
        components = legal_components(segment, YEAR_WITH_SEGMENTS, active)
        income = max(
            0,
            unit["net"]
            + unit["wtc"]
            + unit["ctc"]
            + unit["other"]
            - (components["earnings_disregard"] if holds[EARNINGS] else 0)
            - (components["reserve"] if holds[WTC_DISREGARD] else 0)
            - components["childcare"],
        )
        if not holds[INCOME]:
            income = 0
        awards.append(
            max(0, RENT - WITHDRAWAL_RATE * max(0, income - unit["applicable_amount"]))
        )
    return sum(days * award for days, award in zip(SEGMENT_DAYS, awards)) / 365


@st.composite
def masked_populations(draw):
    """A population from the segment tests, each benefit unit with its own
    draw of the six conditions."""
    return [
        {
            **unit,
            "conditions": draw(
                st.fixed_dictionaries({name: st.booleans() for name in MASKED})
            ),
        }
        for unit in draw(segment_populations())
    ]


def rotating(units):
    """Each unit with one condition failing, in turn, and the others holding."""
    return [
        holding(unit, MASKED[index % len(MASKED)]) for index, unit in enumerate(units)
    ]


def failing(units):
    """Each unit with every condition but income's failing."""
    return [holding(unit, *MASKED[:-1]) for unit in units]


MASKED_EDGE_CASES = rotating(SEGMENT_EDGE_CASES)
FAILING_EDGE_CASES = failing(SEGMENT_EDGE_CASES)
SUPPLIED_MASKED_EDGE_CASES = rotating(SUPPLIED_SEGMENT_EDGE_CASES)
SUPPLIED_LIMIT_MASKED_EDGE_CASES = rotating(SUPPLIED_LIMIT_SEGMENT_EDGE_CASES)


class issue_reform(Reform):
    """The issue's reform: the earnings and WTC disregards apply only in
    specified or temporary accommodation."""

    def apply(self):
        for name in (EARNINGS, WTC_DISREGARD):

            class eligibility_only(Variable):
                defined_for = "in_specified_or_temporary_accommodation"

            eligibility_only.__name__ = name
            self.update_variable(eligibility_only)


@pytest.mark.parametrize(
    "specified,earnings,wtc,award",
    [
        # The condition fails. The annual disregards are nil, and so is
        # each segment's: before the fix, £260 and £889.20. Income is the
        # £500 of earnings and the £2,000 of WTC, so the award is 10,400 -
        # 0.65 * 2,500 = 8,775 in both segments, the annual route's award.
        (False, [0, 0], [0, 0], 8_775),
        # The condition holds, so the model's figures apply: £260 before 5
        # October; then also the £240 of accommodation disregard that the
        # earnings left; and £889.20 of WTC disregard in both segments.
        (True, [260, 500], [889.20, 889.20], 9_600.19),
    ],
)
def test_issue_2777_reform_masks_each_segment(specified, earnings, wtc, award):
    reformed = issue_reform(tax_credits_kept())
    unit = specified_claimant(specified=specified)
    sim = simulation(
        [unit],
        YEAR_WITH_SEGMENTS,
        tax_benefit_system=reformed,
        dated_accommodation=True,
    )
    before, after = segments(sim, YEAR_WITH_SEGMENTS)
    assert_close(
        [before["earnings_disregard"][0], after["earnings_disregard"][0]], earnings
    )
    assert_close([before["reserve"][0], after["reserve"][0]], wtc)
    for key, name in (("earnings_disregard", EARNINGS), ("reserve", WTC_DISREGARD)):
        assert_close(
            sim.calculate(name, YEAR_WITH_SEGMENTS),
            day_weighted([before, after], key),
            name,
        )
    assert sim.calculate(AWARD, YEAR_WITH_SEGMENTS)[0] == pytest.approx(
        award, abs=TOLERANCE
    )


# Each variable, for the issue's claimant or one who needs it, with its
# condition failing and holding: the segments' amounts, the annual amount and
# the award. Where the condition holds the figures are the model's.
SINGLE_MASKS = [
    # Without the earnings disregard income is 2,500 - 889.20 = 1,610.80, and
    # the award 10,400 - 0.65 * 1,610.80 = 9,352.98 in both segments. With
    # it, 1,350.80 and 9,521.98.
    pytest.param(
        EARNINGS,
        ISSUE_CLAIMANT,
        "earnings_disregard",
        ([0, 0], 9_352.98),
        ([260, 260], 9_521.98),
        id="earnings disregard",
    ),
    # Without the WTC disregard income is 2,500 - 260 = 2,240, and the award
    # 10,400 - 0.65 * 2,240 = 8,944.
    pytest.param(
        WTC_DISREGARD,
        ISSUE_CLAIMANT,
        "reserve",
        ([0, 0], 8_944),
        ([889.20, 889.20], 9_521.98),
        id="WTC disregard",
    ),
    # In specified accommodation: without the accommodation disregard the
    # claimant is as the issue's, with an award of 9,521.98. With it, £77.73 a
    # week from 5 October.
    pytest.param(
        ACCOMMODATION,
        specified_claimant(),
        "accommodation",
        ([0, 0], 9_521.98),
        ([0, FULL_ACCOMMODATION], 9_600.19),
        id="accommodation disregard",
    ),
    # The limit is the 240 of earnings the standard disregard leaves and the
    # 2,000 - 889.20 of WTC left after the para 56 disregard, 1,350.80, so
    # the deduction is the whole 1,000 charge. Income is 2,500 - 260 - 889.20
    # - 1,000 = 350.80 and the award 10,400 - 0.65 * 350.80 = 10,171.98.
    # Without the deduction, the award is the issue's claimant's.
    pytest.param(
        CHILDCARE,
        CHILDCARE_CLAIMANT,
        "childcare",
        ([0, 0], 9_521.98),
        ([1_000, 1_000], 10_171.98),
        id="childcare deduction",
    ),
    # A nil limit leaves nil to deduct.
    pytest.param(
        LIMIT,
        CHILDCARE_CLAIMANT,
        "childcare",
        ([0, 0], 9_521.98),
        ([1_000, 1_000], 10_171.98),
        id="childcare limit",
    ),
]


@pytest.mark.parametrize("holds", [False, True])
@pytest.mark.parametrize("name,unit,key,fails,held", SINGLE_MASKS)
def test_a_condition_reaches_each_segment(name, unit, key, fails, held, holds):
    amounts, award = held if holds else fails
    reformed = holding(unit) if holds else holding(unit, name)
    sim = masked_simulation([reformed], YEAR_WITH_SEGMENTS, active=True)
    segment_list = segments(sim, YEAR_WITH_SEGMENTS)
    assert_close([segment[key][0] for segment in segment_list], amounts)
    if name in (ACCOMMODATION, EARNINGS, WTC_DISREGARD):
        assert_close(
            sim.calculate(name, YEAR_WITH_SEGMENTS), day_weighted(segment_list, key)
        )
    elif holds:
        # The annual deduction and its limit keep their single calculation.
        assert sim.calculate(CHILDCARE, YEAR_WITH_SEGMENTS)[0] == pytest.approx(
            1_000, abs=TOLERANCE
        )
        assert sim.calculate(LIMIT, YEAR_WITH_SEGMENTS)[0] == pytest.approx(
            1_350.80, abs=TOLERANCE
        )
    else:
        assert sim.calculate(CHILDCARE, YEAR_WITH_SEGMENTS)[0] == 0
        if name == LIMIT:
            assert sim.calculate(LIMIT, YEAR_WITH_SEGMENTS)[0] == 0
    assert sim.calculate(AWARD, YEAR_WITH_SEGMENTS)[0] == pytest.approx(
        award, abs=TOLERANCE
    )


@pytest.mark.parametrize(
    "holds,income,award",
    [
        # Nil income leaves the whole rent of 10,400.
        (False, 0, 10_400),
        (True, 1_350.80, 9_521.98),
    ],
)
def test_a_condition_on_applicable_income_reaches_each_segment(holds, income, award):
    unit = holding(ISSUE_CLAIMANT) if holds else holding(ISSUE_CLAIMANT, INCOME)
    sim = masked_simulation([unit], YEAR_WITH_SEGMENTS, active=True)
    assert sim.calculate(INCOME, YEAR_WITH_SEGMENTS)[0] == pytest.approx(
        income, abs=TOLERANCE
    )
    assert sim.calculate(AWARD, YEAR_WITH_SEGMENTS)[0] == pytest.approx(
        award, abs=TOLERANCE
    )


def test_a_supplied_deduction_applies_whatever_its_condition():
    """Core returns an input without applying the variable's condition, and
    each segment deducts the supplied annual amount too. The lone parent of
    test_supplied_annual_deduction_applies_in_every_segment, supplying the
    £4,160 the model calculates, keeps its award of 7,394.22."""
    unit = holding(case(specified=True, net=8_000, wtc=2_000, other=3_000), CHILDCARE)
    sim = masked_simulation([unit], YEAR_WITH_SEGMENTS, active=True)
    sim.set_input(CHILDCARE, YEAR_WITH_SEGMENTS, [4_160])
    assert sim.calculate(CHILDCARE, YEAR_WITH_SEGMENTS)[0] == 4_160
    for segment in segments(sim, YEAR_WITH_SEGMENTS):
        assert segment["childcare"][0] == pytest.approx(4_160, abs=TOLERANCE)
    assert sim.calculate(AWARD, YEAR_WITH_SEGMENTS)[0] == pytest.approx(
        7_394.22, abs=TOLERANCE
    )


@pytest.mark.parametrize("entity", [BenUnit, Person])
def test_a_condition_holding_for_one_of_two_benefit_units_in_a_household(entity):
    """Two of the issue's claimants in specified accommodation share a
    household. One condition masks the accommodation, earnings and WTC
    disregards, the childcare deduction and its limit, and holds only for
    the first benefit unit, or for its adult. Core maps a person's condition
    to the benefit unit as it does for the annual amounts."""
    names = (ACCOMMODATION, EARNINGS, WTC_DISREGARD, CHILDCARE, LIMIT)
    condition = "housing_benefit_reform_condition"
    reformed = masking_reform({condition: names}, entity)(tax_credits_kept())
    units = [specified_claimant(), specified_claimant()]
    sim = simulation(
        units,
        YEAR_WITH_SEGMENTS,
        tax_benefit_system=reformed,
        dated_accommodation=True,
        one_household=True,
    )
    assert len(sim.calculate("household_id", YEAR_WITH_SEGMENTS)) == 1
    # One adult in each benefit unit, so the people's and the benefit
    # units' conditions both read [True, False].
    sim.set_input(condition, YEAR_WITH_SEGMENTS, [True, False])
    before, after = segments(sim, YEAR_WITH_SEGMENTS)
    # The first keeps the model's amounts; the second has none, so its
    # income is 2,500 and its award 10,400 - 0.65 * 2,500 = 8,775.
    assert_close(after["accommodation"], [FULL_ACCOMMODATION, 0])
    assert_close(before["earnings_disregard"], [260, 0])
    assert_close(after["earnings_disregard"], [500, 0])
    assert_close(before["reserve"], [889.20, 0])
    assert_close(after["reserve"], [889.20, 0])
    for key, name in (
        ("accommodation", ACCOMMODATION),
        ("earnings_disregard", EARNINGS),
        ("reserve", WTC_DISREGARD),
    ):
        assert_close(
            sim.calculate(name, YEAR_WITH_SEGMENTS),
            day_weighted([before, after], key),
            name,
        )
    assert_close(sim.calculate(AWARD, YEAR_WITH_SEGMENTS), [9_600.19, 8_775])


@PROPERTY_SETTINGS
@given(units=masked_populations(), active=st.booleans())
@example(units=MASKED_EDGE_CASES, active=True)
@example(units=MASKED_EDGE_CASES, active=False)
@example(units=FAILING_EDGE_CASES, active=True)
@example(units=SUPPLIED_MASKED_EDGE_CASES, active=True)
@example(units=SUPPLIED_LIMIT_MASKED_EDGE_CASES, active=True)
def test_masked_segments_add_up_and_match_the_regulations(units, active):
    """M1, M2 and M4 in 2026-27."""
    sim = masked_simulation(units, YEAR_WITH_SEGMENTS, active)
    actual = outputs(sim, YEAR_WITH_SEGMENTS)
    segment_list = segments(sim, YEAR_WITH_SEGMENTS)
    assert len(segment_list) == 2
    # M1.
    for key in ("accommodation", "earnings_disregard", "reserve"):
        assert_close(actual[key], day_weighted(segment_list, key), key)
    # M2.
    holds = {
        name: np.array([unit["conditions"][name] for unit in units]) for name in MASKED
    }
    deduction_supplied = units[0]["supplied"] is not None
    limit_supplied = units[0]["supplied_limit"] is not None
    fails = {
        "accommodation": ~holds[ACCOMMODATION],
        "earnings_disregard": ~holds[EARNINGS],
        "reserve": ~holds[WTC_DISREGARD],
    }
    if not deduction_supplied:
        fails["childcare"] = ~holds[CHILDCARE] | (
            ~holds[LIMIT] if not limit_supplied else False
        )
    if not deduction_supplied and not limit_supplied:
        fails["limit"] = ~holds[LIMIT]
    for key, failed in fails.items():
        assert np.all(actual[key][failed] == 0), key
        for segment in segment_list:
            if key in segment:
                assert np.all(segment[key][failed] == 0), key
    assert np.all(actual["income"][~holds[INCOME]] == 0)
    # Nil income leaves the whole rent.
    assert_close(actual["award"][~holds[INCOME]], RENT)
    # M4.
    assert_close(actual["award"], [legal_masked_award(unit, active) for unit in units])


@PROPERTY_SETTINGS
@given(units=masked_populations(), active=st.booleans())
@example(units=MASKED_EDGE_CASES, active=True)
@example(units=SUPPLIED_MASKED_EDGE_CASES, active=True)
def test_benefit_units_whose_conditions_hold_keep_the_models_outputs(units, active):
    """M3, against the model without the reform. Benefit units are assessed
    separately, so a failed condition in one does not reach another."""
    sim = masked_simulation(units, YEAR_WITH_SEGMENTS, active)
    model = simulation(
        units,
        YEAR_WITH_SEGMENTS,
        tax_benefit_system=baseline(active),
        dated_accommodation=True,
    )
    held = np.array([all(unit["conditions"].values()) for unit in units])
    expected = outputs(model, YEAR_WITH_SEGMENTS)
    for key, values in outputs(sim, YEAR_WITH_SEGMENTS).items():
        assert_close(values[held], expected[key][held], key)


def segment_route_award(sim, units, year):
    """The award built from each segment's income, as entitlement builds it
    in 2026-27, applying the income condition from the units directly."""
    benunit = sim.populations["benunit"]
    period = period_(year)
    parameters = sim.tax_benefit_system.parameters
    before = np.asarray(hb_income_before_deductions(benunit, period, parameters))
    retain = np.asarray(
        sim.calculate("housing_benefit_pension_age_regulations_apply", year)
    ) | np.asarray(sim.calculate("housing_benefit_on_passporting_benefit", year))
    income = np.asarray(sim.calculate(INCOME, year), dtype=float)
    income_holds = np.array([unit["conditions"][INCOME] for unit in units])
    applicable_amount = np.array([unit["applicable_amount"] for unit in units])
    award = 0
    for segment in segments(sim, year):
        segment_income = np.where(
            income_holds,
            np.maximum(
                0,
                before
                - segment["earnings_disregard"]
                - segment["reserve"]
                - segment["childcare"],
            ),
            0,
        )
        segment_income = np.where(retain, income, segment_income)
        award = award + segment["share"] * np.maximum(
            0,
            RENT - WITHDRAWAL_RATE * np.maximum(0, segment_income - applicable_amount),
        )
    return award


@PROPERTY_SETTINGS
@given(
    units=masked_populations(),
    year=st.sampled_from([2024, 2025, 2027]),
    active=st.booleans(),
)
@example(units=MASKED_EDGE_CASES, year=2027, active=True)
@example(units=MASKED_EDGE_CASES, year=2024, active=True)
@example(units=FAILING_EDGE_CASES, year=2027, active=True)
@example(units=SUPPLIED_MASKED_EDGE_CASES, year=2027, active=True)
@example(units=SUPPLIED_LIMIT_MASKED_EDGE_CASES, year=2024, active=False)
def test_one_segment_gives_the_annual_routes_award(units, year, active):
    """M5: outside 2026-27 the accommodation amounts do not change within
    the year. The single segment's amounts are the annual outputs, and the
    award built from them is the model's, which reads annual income."""
    sim = masked_simulation(units, year, active)
    actual = outputs(sim, year)
    (segment,) = segments(sim, year)
    assert segment["share"] == 1
    for key in ("accommodation", "earnings_disregard", "reserve", "childcare"):
        assert_close(segment[key], actual[key], key)
    assert_close(segment_route_award(sim, units, year), actual["award"])
