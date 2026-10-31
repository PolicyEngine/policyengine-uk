"""Properties of fiscal-year Housing Benefit accommodation date integration.

D1. No change, no segments: when none of the seven monetary parameters
    changes, one full-year segment gives the direct unsegmented award.
D2. Convex combination: the annual award is between the segment awards and
    equals their independently calculated elapsed-day-weighted mean.
D3. Bounds: with nonnegative eligible rent and non-dependant deductions,
    entitlement is between zero and eligible rent.
D4. Monotonicity: without the additional disregard, raising accommodation
    never lowers the annual award. With it, the award can fall, as the law
    intends: the additional disregard applies only where net earnings reach
    the standard, accommodation, childcare and additional amounts together
    (HB Regs 2006 Sch. 4 para. 17(1) and (3), as SI 2026/978 reg. 2 amends
    them; NI Sch. 5 para. 17 and SR 2026/157 reg. 2). At net earnings of
    1,149.20, standard 260 and no childcare, raising later accommodation from
    zero to one penny removes the 889.20 additional disregard, and the annual
    award falls from 10,400 to 10,110.22. A regression pins that case.
D5. Day count: 2026-27 has 182 days before 5 October and 183 from that
    date, totalling 365; inspect production segments, not just a calendar.

Fixture-scale populations hold annual incomes, rent and circumstances
constant. The direct oracle implements the earnings cap, residual childcare
limit, additional earnings test, income floor, threshold and award floor
independently of the production helpers. It uses calendar dates independently
of the production weights. All seven rates, family shapes, negative net
earnings, permitted work, childcare and tax credits are exercised.
"""

from datetime import date

import numpy as np
import pytest
from hypothesis import HealthCheck, example, given, settings
from hypothesis import strategies as st

from policyengine_core.periods import period as make_period
from policyengine_core.reforms import Reform
from policyengine_core.simulations import Simulation
from policyengine_uk.system import system
from policyengine_uk.variables.gov.dwp.housing_benefit.applicable_income.housing_benefit_specified_or_temporary_accommodation_disregard import (
    hb_accommodation_segments,
)


PREFIX = (
    "gov.dwp.housing_benefit.means_test.income_disregard."
    "specified_or_temporary_accommodation"
)
RATES = {
    ("single", "younger"): 61.41,
    ("single", "older"): 77.73,
    ("lone_parent", "younger"): 61.41,
    ("lone_parent", "older"): 77.73,
    ("couple", "minors"): 97.33,
    ("couple", "younger"): 61.53,
    ("couple", "older"): 119.70,
}
AGES = {"minors": 17, "younger": 23, "older": 30}
TOLERANCE = 0.01
PROPERTY_SETTINGS = settings(
    max_examples=5,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)


def case(**overrides):
    result = dict(
        family="single",
        age="older",
        net=1_000,
        other=0,
        special=False,
        permitted=0,
        childcare=0,
        credits=0,
        worker=False,
        rent=10_400,
        applicable=500,
        non_dep=0,
    )
    result.update(overrides)
    return result


@st.composite
def families(draw):
    family, age = draw(st.sampled_from(list(RATES)))
    return case(
        family=family,
        age=age,
        net=draw(st.integers(-1_000, 30_000)),
        other=draw(st.integers(0, 20_000)),
        special=draw(st.booleans()),
        permitted=draw(st.sampled_from([0, 520, 1_040, 1_300, 9_542])),
        childcare=draw(st.integers(0, 20_000)) if family == "lone_parent" else 0,
        credits=draw(st.integers(0, 5_000)),
        worker=draw(st.booleans()),
        rent=draw(st.integers(0, 30_000)),
        applicable=draw(st.integers(0, 15_000)),
        non_dep=draw(st.integers(0, 5_000)),
    )


EDGE_CASES = [case(family=family, age=age) for family, age in RATES]
EDGE_CASES += [
    case(net=-100, rent=0),
    case(net=30_000, rent=100),
    case(family="lone_parent", net=10_000, childcare=20_000, credits=500),
    case(net=1_149.20, worker=True),
    case(net=1_149.21, worker=True, permitted=520),
]
POPULATIONS = st.lists(families(), min_size=1, max_size=24)


def calculate(units, year=2026, rates=None):
    people, benunits, households = {}, {}, {}
    for i, unit in enumerate(units):
        adults = 2 if unit["family"] == "couple" else 1
        children = int(unit["family"] == "lone_parent")
        members = []
        for j in range(adults + children):
            name = f"p{i}_{j}"
            gross = max(1, unit["net"]) if j == 0 else 0
            people[name] = {
                "age": {year: AGES[unit["age"]] if j < adults else 8},
                "is_claimant_or_partner": {year: j < adults},
                "employment_income": {year: gross},
                "income_tax_before_winter_fuel_payment_charge": {
                    year: gross - unit["net"] if j == 0 else 0
                },
                "national_insurance": {year: 0},
                "pension_contributions": {year: 0},
                "private_pension_income": {year: unit["other"] if j == 0 else 0},
                "childcare_expenses": {year: unit["childcare"] if j == 0 else 0},
            }
            members.append(name)
        inputs = {
            "housing_benefit_net_earnings": unit["net"],
            "housing_benefit_special_earnings_disregard_eligible": unit["special"],
            "housing_benefit_permitted_work_disregard": unit["permitted"],
            "meets_housing_benefit_additional_earnings_disregard_conditions": unit[
                "worker"
            ],
            "housing_benefit_applicable_amount": unit["applicable"],
            "benunit_rent": unit["rent"],
            "housing_benefit_non_dep_deductions": unit["non_dep"],
            "housing_benefit_meals_deduction": 0,
            "housing_benefit_tariff_income": 0,
            "LHA_eligible": False,
            "in_specified_or_temporary_accommodation": True,
            "housing_benefit_on_passporting_benefit": False,
            "housing_benefit_pension_age_regulations_apply": False,
            "working_tax_credit": unit["credits"],
            "child_tax_credit": 0,
            "tax_credits": unit["credits"],
            "income_support": 0,
            "jsa_income": 0,
            "esa_income": 0,
        }
        benunits[f"b{i}"] = {
            "members": members,
            **{name: {year: value} for name, value in inputs.items()},
        }
        households[f"h{i}"] = {"members": members}
    situation = {"people": people, "benunits": benunits, "households": households}
    if rates is None:
        sim = Simulation(tax_benefit_system=system, situation=situation)
    else:
        reform = Reform.from_dict(
            {
                f"{PREFIX}.{family}.{age}": {"2026-10-05.2027-04-05": value}
                for (family, age), value in rates.items()
            }
        )
        sim = Simulation(tax_benefit_system=reform(system), situation=situation)
    return sim, np.asarray(
        sim.calculate("housing_benefit_entitlement", year), dtype=float
    )


def direct_award(unit, weekly, year=2026):
    """Independent complete award for a full, unweighted weekly rate."""
    p = system.parameters(year).gov.dwp.housing_benefit.means_test
    standard_rates = p.income_disregard
    net = max(0, unit["net"])
    lone_parent = unit["family"] == "lone_parent"
    selected = min(
        net,
        52
        * (
            standard_rates.lone_parent
            if lone_parent
            else standard_rates.special
            if unit["special"]
            else standard_rates.couple
            if unit["family"] == "couple"
            else standard_rates.single
        ),
    )
    standard = (
        min(net, max(unit["permitted"], selected if lone_parent else 0))
        if unit["permitted"] > 0
        else selected
    )
    accommodation = min(max(0, weekly * 52), max(0, net - standard))
    cap = system.parameters(
        year
    ).gov.dwp.tax_credits.working_tax_credit.elements.childcare_1
    charges = min(unit["childcare"], cap * 52) if lone_parent else 0
    childcare = min(charges, max(0, net - standard - accommodation) + unit["credits"])
    additional = standard_rates.worker * 52
    if not unit["worker"] or round(net * 100) < round(
        (standard + accommodation + childcare + additional) * 100
    ):
        additional = 0
    income = max(
        0,
        unit["net"]
        + unit["other"]
        + unit["credits"]
        - standard
        - accommodation
        - childcare
        - additional,
    )
    return max(
        0,
        unit["rent"]
        - unit["non_dep"]
        - p.withdrawal_rate * max(0, income - unit["applicable"]),
    )


def segments(sim, year):
    return list(
        hb_accommodation_segments(
            sim.benunit, make_period(year), sim.tax_benefit_system.parameters
        )
    )


@PROPERTY_SETTINGS
@given(units=POPULATIONS)
@example(units=EDGE_CASES)
def test_d1_no_change_no_segments(units):
    sim, awards = calculate(units, year=2027)
    schedule = sim.tax_benefit_system.parameters.gov.dwp.housing_benefit.means_test.income_disregard.specified_or_temporary_accommodation
    for family, age in RATES:
        leaf = schedule.children[family].children[age]
        assert not any(
            "2027-04-06" < v.instant_str < "2028-04-06" for v in leaf.values_list
        )
    actual_segments = segments(sim, 2027)
    assert len(actual_segments) == 1
    assert actual_segments[0][1] == 1
    expected = [direct_award(u, RATES[u["family"], u["age"]], 2027) for u in units]
    np.testing.assert_allclose(awards, expected, atol=TOLERANCE, rtol=0)


@PROPERTY_SETTINGS
@given(units=POPULATIONS)
@example(units=EDGE_CASES)
def test_d2_convex_combination(units):
    _, awards = calculate(units)
    before_days = (date(2026, 10, 5) - date(2026, 4, 6)).days
    after_days = (date(2027, 4, 6) - date(2026, 10, 5)).days
    before = np.array([direct_award(u, 0) for u in units])
    after = np.array([direct_award(u, RATES[u["family"], u["age"]]) for u in units])
    expected = (before * before_days + after * after_days) / (before_days + after_days)
    np.testing.assert_allclose(awards, expected, atol=TOLERANCE, rtol=0)
    assert np.all(awards >= np.minimum(before, after) - TOLERANCE)
    assert np.all(awards <= np.maximum(before, after) + TOLERANCE)


@PROPERTY_SETTINGS
@given(units=POPULATIONS)
@example(units=EDGE_CASES)
def test_d3_bounds(units):
    _, awards = calculate(units)
    assert np.all(awards >= 0)
    assert np.all(awards <= np.array([u["rent"] for u in units]) + TOLERANCE)


@PROPERTY_SETTINGS
@given(units=POPULATIONS, bump=st.integers(1, 100_000))
@example(units=EDGE_CASES, bump=100)
def test_d4_monotonicity_without_additional_disregard(units, bump):
    units = [{**u, "worker": False} for u in units]
    _, before = calculate(units)
    _, after = calculate(
        units, rates={key: value + bump / 100 for key, value in RATES.items()}
    )
    assert np.all(after >= before - TOLERANCE)


def test_d4_a_penny_of_accommodation_can_switch_off_the_additional_disregard():
    # Net earnings of 1,149.20 equal the 260 standard plus the 889.20
    # additional disregard, so the additional disregard applies with no
    # accommodation amount and stops applying with a penny of it. The later
    # rate is reformed to a penny a year so that only the threshold moves.
    unit = case(net=1_149.20, worker=True, applicable=0)
    _, before = calculate([unit], rates={key: 0 for key in RATES})
    _, after = calculate([unit], rates={key: 0.01 / 52 for key in RATES})
    assert before[0] == pytest.approx(10_400, abs=TOLERANCE)
    assert after[0] == pytest.approx(10_110.22, abs=TOLERANCE)
    # The later segment loses the whole additional disregard: its award is
    # 10,400 less the 65% taper on 1,149.20 - 260 - 0.01 = 889.19 of income.
    later = direct_award(unit, 0.01 / 52)
    assert later == pytest.approx(10_400 - 0.65 * 889.19, abs=TOLERANCE)
    before_days = (date(2026, 10, 5) - date(2026, 4, 6)).days
    after_days = (date(2027, 4, 6) - date(2026, 10, 5)).days
    expected = (direct_award(unit, 0) * before_days + later * after_days) / (
        before_days + after_days
    )
    assert after[0] == pytest.approx(expected, abs=TOLERANCE)


@PROPERTY_SETTINGS
@given(units=POPULATIONS)
@example(units=EDGE_CASES)
def test_d5_day_count(units):
    sim, _ = calculate(units)
    actual_segments = segments(sim, 2026)
    assert len(actual_segments) == 2
    days = [share * 365 for _, share in actual_segments]
    assert days == pytest.approx([182, 183], abs=1e-10)
    assert sum(days) == pytest.approx(365, abs=1e-10)
    np.testing.assert_array_equal(actual_segments[0][0], np.zeros(len(units)))
    np.testing.assert_allclose(
        actual_segments[1][0],
        [52 * RATES[u["family"], u["age"]] for u in units],
        atol=TOLERANCE,
        rtol=0,
    )
