"""Child Tax Credit qualifying young persons who have left education.

Child Tax Credit Regulations 2002:

- Reg. 5(3)(a), (ab), (3A): the first condition is full-time non-advanced
  education or approved training, begun before 19.
- Reg. 4(1)-(2): from the 16th birthday until the 31 August that next
  follows, the first condition is not required. Reg. 4(1A): a 16th birthday
  on 31 August gets no such period.
- Reg. 5(3)(b): under 18, the 20 weeks after leaving while registered for
  work or training satisfy the first condition.
- Reg. 5(4), the second condition, always applies: a person who has left
  education or training must not be in remunerative work (24 hours a week or
  more, reg. 2(1)), and no one may be receiving a benefit in their own right.

Invariants:

1. Reg. 4, against calendar arithmetic that shares no code with the model:
   a person outside education, not working, is a qualifying young person for
   a year exactly when they are 16 to 19 on 6 October and some of the year,
   from 6 April, falls on or before the last day they are a child or in the
   reg. 4 period. For a 16th birthday on 31 August that day is 30 August.
2. Over every combination of age, education, training, apprenticeship,
   own-right benefits, the age the course began, the two leaver facts and
   hours: the status is the education condition, or a leaver fact for a
   person who has left and is not in remunerative work, within ages 16 to 19
   and without own-right benefits. So remunerative work ends both leaver
   routes and neither a student's status, the 20 weeks end at 18, a leaver
   fact never reaches a student whose course began at 19, and with the
   leaver facts off the status is the education condition's alone, as
   before.
3. Switching a leaver fact on never removes the status.
4. The benefit unit's child or qualifying young person is a child or
   qualifying young person who is not its claimant or partner.
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

YEAR = 2024
_PROPERTY_SYSTEM = system.clone()
EDUCATIONS = tuple(item.name for item in EducationType)
ROUTE = "is_before_first_september_following_16th_birthday"
EXTENSION = "is_in_child_tax_credit_extension_period"
QYP = "is_qualifying_young_person_for_child_tax_credit"
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


def last_day_as_child_or_in_regulation_4_period(born):
    # Reg. 4(1): "until 31st August which next follows" the 16th birthday.
    # Reg. 4(1A): a 16th birthday on 31 August starts no such period, so the
    # last day covered is the day before it, the last day under 16.
    # https://www.legislation.gov.uk/uksi/2002/2007/regulation/4
    if (born.month, born.day) == (8, 31):
        return date(born.year + 16, 8, 30)
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
    expected = [
        16 <= age_on_6_october(born, year) < 20
        and date(year, 4, 6) <= last_day_as_child_or_in_regulation_4_period(born)
        for born in births
    ]
    actual = simulate(units, year).calculate(QYP, year)[1::2]
    np.testing.assert_array_equal(actual, expected)
    return expected


def test_regulation_4_for_every_date_of_birth():
    # Every date of birth from 2004 to 2009: ages 14 to 20 on 6 October 2024.
    start, end = date(2004, 1, 1), date(2010, 1, 1)
    births = [start + timedelta(days=d) for d in range((end - start).days)]
    expected = assert_regulation_4_matches_calendar(births, YEAR)
    by_birth = dict(zip(births, expected))
    assert by_birth[date(2008, 6, 1)] and not by_birth[date(2007, 6, 1)]
    # 16 on 31 August 2023: reg. 4(1A) gives no period to 31 August 2024.
    assert not by_birth[date(2007, 8, 31)]
    # 16 on 31 August 2024: a child until 30 August 2024, in the year.
    assert by_birth[date(2008, 8, 31)]
    # 16 on 1 September 2023: the period runs to 31 August 2024.
    assert by_birth[date(2007, 9, 1)]
    # 16 on 6 October 2024 is 16 for the year; 16 on 7 October is still 15.
    assert by_birth[date(2008, 10, 6)] and not by_birth[date(2008, 10, 7)]


@SETTINGS
@given(
    st.lists(st.dates(date(1990, 1, 1), date(2031, 12, 31)), min_size=1, max_size=30),
    st.integers(2013, 2031),
)
def test_regulation_4_matches_calendar_arithmetic_in_any_year(births, year):
    births = [born for born in births if age_on_6_october(born, year) >= 0]
    assume(births)
    assert_regulation_4_matches_calendar(births, year)


def receiving_education_or_training(p):
    # Education status stands in for full-time non-advanced education that is
    # not by virtue of employment (reg. 5(3)(a)), or approved training ((ab)).
    return (
        p["current_education"] not in {"NOT_IN_EDUCATION", "TERTIARY"}
        and not p["is_apprentice"]
    ) or p["is_in_approved_training"]


def first_condition_through_education(p):
    # Reg. 5(3A): begun before 19.
    begun_before_19 = (
        p["age"] < 19 or p["age_started_or_accepted_current_education_or_training"] < 19
    )
    return receiving_education_or_training(p) and begun_before_19


def qualifying_young_person(p):
    # https://www.legislation.gov.uk/uksi/2002/2007/regulation/5
    if not 16 <= p["age"] < 20 or p["receives_benefits_in_own_right"]:
        return False
    if first_condition_through_education(p):
        return True
    left = not receiving_education_or_training(p)
    leaver_fact = p[ROUTE] or (p["age"] < 18 and p[EXTENSION])
    # Reg. 2(1): remunerative work is 24 hours a week or more.
    return left and leaver_fact and p["weekly_hours"] < 24


GRID = [
    person(
        age,
        current_education=education,
        is_in_approved_training=training,
        is_apprentice=apprentice,
        receives_benefits_in_own_right=own_right,
        weekly_hours=hours,
        age_started_or_accepted_current_education_or_training=entry_age,
        **{ROUTE: route, EXTENSION: extension},
    )
    for age, education, training, apprentice, own_right, hours, entry_age in product(
        range(14, 22),
        EDUCATIONS,
        (False, True),
        (False, True),
        (False, True),
        (0, 23, 24),
        # A course begun at 19 fails reg. 5(3A). Such a student has not left
        # education, so neither leaver fact reaches them.
        (17, 1000),
    )
    for route, extension in product((False, True), repeat=2)
]


def test_status_is_the_first_condition_or_a_leaver_fact_under_the_second():
    units = [
        [person(45, is_claimant_or_partner=True, **{ROUTE: False}), p] for p in GRID
    ]
    sim = simulate(units)
    status = sim.calculate(QYP, YEAR)[1::2]
    # Invariant 2.
    np.testing.assert_array_equal(status, [qualifying_young_person(p) for p in GRID])
    age = np.array([p["age"] for p in GRID])
    hours = np.array([p["weekly_hours"] for p in GRID])
    student = np.array([receiving_education_or_training(p) for p in GRID])
    own_right = np.array([p["receives_benefits_in_own_right"] for p in GRID])
    assert not status[(age < 16) | (age >= 20)].any()
    assert not status[own_right].any()
    # A student whose course began at 19 does not qualify, whatever the
    # leaver facts say.
    late_student = np.array(
        [
            receiving_education_or_training(p)
            and p["age"] >= 19
            and p["age_started_or_accepted_current_education_or_training"] >= 19
            for p in GRID
        ]
    )
    assert late_student.any() and not status[late_student].any()
    # Remunerative work ends a leaver's status and not a student's.
    assert not status[~student & (hours >= 24)].any()
    assert status[student & (hours >= 24)].any()
    # The 20 weeks alone do not reach an 18-year-old.
    alone = np.array([p[EXTENSION] and not p[ROUTE] for p in GRID])
    assert not status[alone & ~student & (age >= 18)].any()
    assert status[alone & ~student & (age == 17)].any()
    # With the leaver facts off, the education condition alone, as before.
    off = np.array([not (p[ROUTE] or p[EXTENSION]) for p in GRID])
    np.testing.assert_array_equal(
        status[off],
        [
            16 <= p["age"] < 20
            and not p["receives_benefits_in_own_right"]
            and first_condition_through_education(p)
            for p, o in zip(GRID, off)
            if o
        ],
    )
    # Invariant 3: rows are ordered (route, extension) within blocks of 4.
    blocks = status.reshape(-1, 4)
    for less, more in ((0, 1), (0, 2), (1, 3), (2, 3)):
        assert (blocks[:, more] >= blocks[:, less]).all(), (less, more)
    # Invariant 4, for members who are not the claimant.
    family = sim.calculate(
        "is_child_or_qualifying_young_person_for_child_tax_credit", YEAR
    )
    np.testing.assert_array_equal(family[1::2], (age < 16) | status)
    assert not family[0::2].any()


member = st.builds(
    person,
    st.integers(0, 21),
    current_education=st.sampled_from(EDUCATIONS),
    is_in_approved_training=st.booleans(),
    receives_benefits_in_own_right=st.booleans(),
    is_looked_after_by_local_authority=st.booleans(),
    weekly_hours=st.sampled_from([0, 10, 23, 24, 40]),
    **{ROUTE: st.booleans(), EXTENSION: st.booleans()},
)


@st.composite
def benefit_units(draw):
    claimants = draw(st.lists(member, min_size=1, max_size=2))
    others = draw(st.lists(member, max_size=4))
    return [dict(p, is_claimant_or_partner=True) for p in claimants] + others


@SETTINGS
@given(st.lists(benefit_units(), min_size=1, max_size=6), st.sampled_from([2020, 2024]))
def test_family_members_in_any_benefit_unit(units, year):
    # Invariants 2 and 4 on benefit units of any shape, where a claimant or
    # partner can be a qualifying young person by status.
    sim = simulate(units, year)
    people = [p for unit in units for p in unit]
    status = sim.calculate(QYP, year)
    np.testing.assert_array_equal(status, [qualifying_young_person(p) for p in people])
    family = sim.calculate(
        "is_child_or_qualifying_young_person_for_child_tax_credit", year
    )
    expected = [
        (p["age"] < 16 or qualifying_young_person(p))
        and not p["is_claimant_or_partner"]
        and not p["is_looked_after_by_local_authority"]
        for p in people
    ]
    np.testing.assert_array_equal(family, expected)
