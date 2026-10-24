"""Child Benefit qualifying young persons who have left education.

Child Benefit (General) Regulations 2006: a person aged 16 to 19 is a
qualifying young person while any of regs 3 to 7 applies (reg. 2(2)) and
they are not receiving a benefit in their own right (reg. 8).

- Reg. 3: non-advanced education or approved training, begun before 19.
- Reg. 4: under 17 and left education, until the 31 August next following
  the 16th birthday (the 1 September for a 16th birthday on 31 August).
- Reg. 5: under 18, in an extension period, not in remunerative work.
- Reg. 7: until the terminal date after leaving; reg. 7(3) pays no Child
  Benefit "by virtue of this regulation" in a week of remunerative work (24
  hours or more, reg. 1(3)).

Invariants:

1. Reg. 4, against calendar arithmetic that shares no code with the model:
   a person outside education is a qualifying young person for a year
   exactly when they are 16 to 19 on 6 October and the year starts (6 April)
   on or before the reg. 4 end date, for every date of birth.
2. Over every combination of age, education, training, own-right benefits,
   the three leaver facts and hours: the status equals the union of the four
   conditions within ages 16 to 19 and without own-right benefits. So each
   condition ends at its age limit, own-right benefits exclude every
   condition, and with the three leaver facts off the status is reg. 3's
   alone, as before.
3. Switching a leaver fact on never removes the status.
4. Child Benefit is payable for the benefit unit's child or qualifying young
   person unless they qualify through reg. 7 alone and are in remunerative
   work. They stay a qualifying young person, and a legacy young person.
5. Child Benefit entitlement is the eldest payable member at the eldest
   rate and each other at the additional rate, for 52 weeks.
"""

from datetime import date, timedelta
from itertools import product
from unittest.mock import patch

import numpy as np
from hypothesis import HealthCheck, assume, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation
from policyengine_uk.tax_benefit_system import system
from policyengine_uk.variables.household.demographic.highest_education import (
    EducationType,
)

YEAR = 2026
_PROPERTY_SYSTEM = system.clone()
EDUCATIONS = tuple(item.name for item in EducationType)
ROUTE = "is_before_first_september_following_16th_birthday"
EXTENSION = "is_in_child_benefit_extension_period"
TERMINAL = "is_before_child_benefit_terminal_date"
QYP = "is_qualifying_young_person_for_child_benefit"
SETTINGS = settings(
    max_examples=25,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)


def person(age, **inputs):
    return {
        "age": age,
        "current_education": "NOT_IN_EDUCATION",
        "is_in_approved_training": False,
        "is_apprentice": False,
        "receives_benefits_in_own_right": False,
        "is_looked_after_by_local_authority": False,
        "age_started_or_accepted_current_education_or_training": 17,
        "weekly_hours": 0,
        EXTENSION: False,
        TERMINAL: False,
        "is_claimant_or_partner": False,
        **inputs,
    }


def simulate(units, year=YEAR):
    situation = {"people": {}, "benunits": {}, "households": {}}
    people = []
    for i, unit in enumerate(units):
        names = []
        for j, inputs in enumerate(unit):
            name = f"p{i}_{j}"
            situation["people"][name] = {}
            people.append(inputs)
            names.append(name)
        situation["benunits"][f"b{i}"] = {"members": names}
        situation["households"][f"h{i}"] = {"members": names}
    with patch(
        "policyengine_uk.simulation.CountryTaxBenefitSystem",
        side_effect=_PROPERTY_SYSTEM.clone,
    ):
        sim = Simulation(situation=situation)
    variables = people[0].keys()
    assert all(p.keys() == variables for p in people)
    for variable in variables:
        sim.set_input(variable, year, [p[variable] for p in people])
    sim.input_variables = list(variables)
    sim.reset_calculations()
    return sim


def regulation_4_end_date(born):
    # Reg. 4(2): "the 31st August next following the person's 16th birthday";
    # reg. 4(3): for a 16th birthday on 31 August, "the 1st September
    # immediately following". A 29 February birthday is before 31 August
    # whichever day it is kept on in other years.
    # https://www.legislation.gov.uk/uksi/2006/223/regulation/4
    if (born.month, born.day) == (8, 31):
        return date(born.year + 16, 9, 1)
    return date(born.year + 16 + ((born.month, born.day) > (8, 31)), 8, 31)


def age_on_6_october(born, year):
    return year - born.year - ((10, 6) < (born.month, born.day))


def assert_regulation_4_matches_calendar(births, year):
    units = [
        [
            person(40, is_claimant_or_partner=True, date_of_birth=0),
            person(age_on_6_october(born, year), date_of_birth=int(f"{born:%Y%m%d}")),
        ]
        for born in births
    ]
    # "Has not passed": the year, from 6 April, reaches the period if it
    # starts on or before the end date.
    expected = [
        16 <= age_on_6_october(born, year) < 20
        and date(year, 4, 6) <= regulation_4_end_date(born)
        for born in births
    ]
    actual = simulate(units, year).calculate(QYP, year)[1::2]
    np.testing.assert_array_equal(actual, expected)
    return expected


def test_regulation_4_for_every_date_of_birth():
    # Every date of birth from 2006 to 2011: ages 14 to 20 on 6 October 2026,
    # with the 31 August and 1 September edges in each year.
    start, end = date(2006, 1, 1), date(2012, 1, 1)
    births = [start + timedelta(days=d) for d in range((end - start).days)]
    expected = assert_regulation_4_matches_calendar(births, YEAR)
    # Not vacuous, and the edges fall where the regulation puts them.
    by_birth = dict(zip(births, expected))
    assert by_birth[date(2010, 6, 1)] and not by_birth[date(2009, 6, 1)]
    # 16 on 31 August 2025: the period ended on 1 September 2025.
    assert not by_birth[date(2009, 8, 31)]
    # 16 on 1 September 2025: the period runs to 31 August 2026.
    assert by_birth[date(2009, 9, 1)]
    # 16 on 6 October 2026 is 16 for the year; 16 on 7 October is still 15.
    assert by_birth[date(2010, 10, 6)] and not by_birth[date(2010, 10, 7)]


@SETTINGS
@given(
    st.lists(st.dates(date(1990, 1, 1), date(2031, 12, 31)), min_size=1, max_size=30),
    st.integers(2013, 2031),
)
def test_regulation_4_matches_calendar_arithmetic_in_any_year(births, year):
    births = [born for born in births if age_on_6_october(born, year) >= 0]
    assume(births)
    assert_regulation_4_matches_calendar(births, year)


def regulation_3(p):
    # Education status stands in for full-time non-advanced education.
    # https://www.legislation.gov.uk/uksi/2006/223/regulation/3
    studying = (
        p["current_education"] not in {"NOT_IN_EDUCATION", "TERTIARY"}
        and not p["is_apprentice"]
    ) or p["is_in_approved_training"]
    begun_before_19 = (
        p["age"] < 19 or p["age_started_or_accepted_current_education_or_training"] < 19
    )
    return studying and begun_before_19


def remunerative_work(p):
    # https://www.legislation.gov.uk/uksi/2006/223/regulation/1
    return p["weekly_hours"] >= 24


def regulation_5(p):
    # https://www.legislation.gov.uk/uksi/2006/223/regulation/5
    return p["age"] < 18 and p[EXTENSION] and not remunerative_work(p)


def qualifying_young_person(p):
    if not 16 <= p["age"] < 20 or p["receives_benefits_in_own_right"]:
        return False
    return regulation_3(p) or p[ROUTE] or regulation_5(p) or p[TERMINAL]


def payable(p):
    # Reg. 7(3) bars Child Benefit payable through reg. 7 only.
    if p["is_claimant_or_partner"]:
        return False
    if p["age"] < 16:
        return True
    if not qualifying_young_person(p):
        return False
    through_another = regulation_3(p) or p[ROUTE] or regulation_5(p)
    return through_another or not remunerative_work(p)


GRID = [
    person(
        age,
        current_education=education,
        is_in_approved_training=training,
        receives_benefits_in_own_right=own_right,
        weekly_hours=hours,
        **{ROUTE: route, EXTENSION: extension, TERMINAL: terminal},
    )
    for age, education, training, own_right, hours in product(
        range(14, 22), EDUCATIONS, (False, True), (False, True), (0, 23, 24)
    )
    for route, extension, terminal in product((False, True), repeat=3)
]


def test_status_is_the_union_of_the_four_conditions():
    # 8 ages * every education value * 2 * 2 * 3 hours, each with the 8
    # combinations of the three leaver facts (adjacent rows).
    units = [
        [person(45, is_claimant_or_partner=True, **{ROUTE: False}), p] for p in GRID
    ]
    sim = simulate(units)
    status = sim.calculate(QYP, YEAR)[1::2]
    # Invariant 2.
    np.testing.assert_array_equal(status, [qualifying_young_person(p) for p in GRID])
    age = np.array([p["age"] for p in GRID])
    assert not status[(age < 16) | (age >= 20)].any()
    assert not status[
        np.array([p["receives_benefits_in_own_right"] for p in GRID])
    ].any()
    assert status.any()
    # With the leaver facts off, reg. 3 alone, as before.
    off = np.array([not (p[ROUTE] or p[EXTENSION] or p[TERMINAL]) for p in GRID])
    np.testing.assert_array_equal(
        status[off],
        [
            16 <= p["age"] < 20
            and not p["receives_benefits_in_own_right"]
            and regulation_3(p)
            for p, o in zip(GRID, off)
            if o
        ],
    )
    # Invariant 3: within each block of 8, a row with more facts on never
    # loses the status. Rows are ordered (route, extension, terminal).
    blocks = status.reshape(-1, 8)
    for less, more in (
        (0, 1),
        (0, 2),
        (0, 4),
        (1, 3),
        (1, 5),
        (2, 3),
        (2, 6),
        (4, 5),
        (4, 6),
        (3, 7),
        (5, 7),
        (6, 7),
    ):
        assert (blocks[:, more] >= blocks[:, less]).all(), (less, more)
    # Invariant 4.
    np.testing.assert_array_equal(
        sim.calculate("is_child_benefit_payable_for_person", YEAR)[1::2],
        [payable(p) for p in GRID],
    )
    family = sim.calculate(
        "is_child_or_qualifying_young_person_for_child_benefit", YEAR
    )[1::2]
    legacy = sim.calculate("is_child_or_young_person_for_legacy_benefits", YEAR)[1::2]
    np.testing.assert_array_equal(family, (age < 16) | status)
    np.testing.assert_array_equal(legacy, family)
    barred = family & ~np.array([payable(p) for p in GRID])
    # Not vacuous: some young persons are barred, all of them 16 or over,
    # before the terminal date and working 24 hours.
    assert barred.any()
    assert all(
        p[TERMINAL] and p["weekly_hours"] == 24 and p["age"] >= 16
        for p, b in zip(GRID, barred)
        if b
    )


member = st.builds(
    person,
    st.integers(0, 21),
    current_education=st.sampled_from(EDUCATIONS),
    is_in_approved_training=st.booleans(),
    receives_benefits_in_own_right=st.booleans(),
    weekly_hours=st.sampled_from([0, 10, 23, 24, 40]),
    **{ROUTE: st.booleans(), EXTENSION: st.booleans(), TERMINAL: st.booleans()},
)


@st.composite
def benefit_units(draw):
    claimants = draw(st.lists(member, min_size=1, max_size=2))
    others = draw(st.lists(member, max_size=4))
    return [dict(p, is_claimant_or_partner=True) for p in claimants] + others


@SETTINGS
@given(st.lists(benefit_units(), min_size=1, max_size=6), st.sampled_from([2024, 2026]))
def test_child_benefit_entitlement_counts_payable_members(units, year):
    # Invariant 5, from the inputs and the weekly rates alone.
    sim = simulate(units, year)
    rates = sim.tax_benefit_system.parameters(f"{year}-06-01").gov.hmrc.child_benefit
    entitlement = sim.calculate("child_benefit_entitlement", year)
    for unit, actual in zip(units, entitlement):
        number = sum(payable(p) for p in unit)
        weekly = (
            0
            if number == 0
            else rates.amount.eldest + (number - 1) * rates.amount.additional
        )
        np.testing.assert_allclose(actual, weekly * 52, rtol=1e-6)
