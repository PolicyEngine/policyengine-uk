"""The 1 September following the 19th birthday, for Universal Credit and
Pension Credit qualifying young persons.

A young person enrolled on, or accepted for, non-advanced education or
approved training is a qualifying young person "up to, but not including,
the 1st September following their 19th birthday" (UC Regs 2013 reg. 5(1)(b);
SPC Regs 2002 reg. 4A(1)(b)).

Invariants:

1. is_before_first_september_following_19th_birthday is true exactly when
   the year starts (6 April) before that 1 September, for every date of
   birth, against calendar arithmetic that shares no code with the model.
2. Universal Credit's own terminal-date variable follows that fact unless it
   is set, and setting it changes Universal Credit only.
3. Over every combination of age, education, training, apprenticeship,
   own-right benefits, entry age and the two date facts: Universal Credit
   and Pension Credit agree, and both equal the regulation's conditions.
4. With the 19th-birthday fact on, both statuses are the earlier definition
   without a terminal date, so nothing changes below 19 or for a 19-year-old
   before the date; switching the fact on never removes the status; and it
   matters only for a 19-year-old in education or training.
5. The formula gives true for everyone under 20 on 6 October, whether the
   date of birth or only the age is given, and true is each terminal-date
   variable's default. So a situation that sets one of them for some people
   leaves everyone else's status as it would be with nothing set. That holds
   for one variable at a time: a programme variable set for some people gives
   everyone else its default, not their date fact, so a situation that also
   sets the date fact must set the programme variable for every person whose
   status matters (the crossed test).
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
SIXTEEN = "is_before_first_september_following_16th_birthday"
NINETEEN = "is_before_first_september_following_19th_birthday"
UC_TERMINAL = "is_before_universal_credit_qualifying_young_person_terminal_date"
UC = "is_qualifying_young_person_for_universal_credit"
PC = "is_qualifying_young_person_for_pension_credit"
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
        "age_started_or_accepted_current_education_or_training": 17,
        **inputs,
    }


def simulate(people, year=YEAR):
    """Each person alone in a benefit unit: the status tests are personal."""
    situation = {"people": {}, "benunits": {}, "households": {}}
    for i in range(len(people)):
        situation["people"][f"p{i}"] = {}
        situation["benunits"][f"b{i}"] = {"members": [f"p{i}"]}
        situation["households"][f"h{i}"] = {"members": [f"p{i}"]}
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


def first_september_following_19th_birthday(born):
    # A 19th birthday before 1 September is followed by 1 September of the
    # same year, and one on or after it by the next year's. A 29 February
    # birthday is before 1 September whichever day it is kept on.
    # https://www.legislation.gov.uk/uksi/2013/376/regulation/5
    # https://www.legislation.gov.uk/uksi/2002/1792/regulation/4A
    return date(born.year + 19 + ((born.month, born.day) >= (9, 1)), 9, 1)


def age_on_6_october(born, year):
    return year - born.year - ((10, 6) < (born.month, born.day))


def assert_fact_matches_calendar(births, year):
    people = [
        person(age_on_6_october(born, year), date_of_birth=int(f"{born:%Y%m%d}"))
        for born in births
    ]
    expected = [
        date(year, 4, 6) < first_september_following_19th_birthday(born)
        for born in births
    ]
    sim = simulate(people, year)
    # Invariant 1.
    np.testing.assert_array_equal(sim.calculate(NINETEEN, year), expected)
    # Invariant 2: Universal Credit's variable follows it when not set.
    np.testing.assert_array_equal(sim.calculate(UC_TERMINAL, year), expected)
    return expected


def test_fact_for_every_date_of_birth():
    # Every date of birth from 2004 to 2009: ages 16 to 22 on 6 October 2026.
    start, end = date(2004, 1, 1), date(2010, 1, 1)
    births = [start + timedelta(days=d) for d in range((end - start).days)]
    expected = dict(zip(births, assert_fact_matches_calendar(births, YEAR)))
    # 19 on 31 August 2026: the period ends that day, in the year.
    assert expected[date(2007, 8, 31)]
    # 19 on 31 August 2025: it ended before the year.
    assert not expected[date(2006, 8, 31)]
    # 19 on 1 September 2025: it runs to 31 August 2026.
    assert expected[date(2006, 9, 1)]
    # Everyone aged 19 on 6 October 2026 is before the date.
    assert all(
        before
        for born, before in expected.items()
        if age_on_6_october(born, YEAR) == 19
    )


@SETTINGS
@given(
    st.lists(st.dates(date(1990, 1, 1), date(2031, 12, 31)), min_size=1, max_size=30),
    st.integers(2013, 2031),
)
def test_fact_matches_calendar_arithmetic_in_any_year(births, year):
    births = [born for born in births if age_on_6_october(born, year) >= 0]
    assume(births)
    assert_fact_matches_calendar(births, year)


def studying(p):
    # Education status stands in for a non-advanced course of more than 12
    # hours a week; reg. 5(3) and reg. 4A(3) exclude a contract of employment.
    return (
        p["current_education"] not in {"NOT_IN_EDUCATION", "TERTIARY"}
        and not p["is_apprentice"]
    ) or p["is_in_approved_training"]


def qualifying_young_person(p, terminal_date=True):
    # Reg. 5(1), (2), (5); reg. 4A(1), (2), (5).
    if not 16 <= p["age"] < 20 or p["receives_benefits_in_own_right"]:
        return False
    if p[SIXTEEN]:
        return True
    if not studying(p):
        return False
    if (
        p["age"] >= 19
        and p["age_started_or_accepted_current_education_or_training"] >= 19
    ):
        return False
    return p["age"] < 19 or p[NINETEEN] or not terminal_date


GRID = [
    person(
        age,
        current_education=education,
        is_in_approved_training=training,
        is_apprentice=apprentice,
        receives_benefits_in_own_right=own_right,
        age_started_or_accepted_current_education_or_training=entry_age,
        **{SIXTEEN: sixteen, NINETEEN: nineteen},
    )
    for age, education, training, apprentice, own_right, entry_age, sixteen in product(
        range(14, 22),
        EDUCATIONS,
        (False, True),
        (False, True),
        (False, True),
        (17, 19, 1000),
        (False, True),
    )
    for nineteen in (False, True)
]


def test_universal_credit_and_pension_credit_agree_on_every_combination():
    sim = simulate(GRID)
    uc, pc = sim.calculate(UC, YEAR), sim.calculate(PC, YEAR)
    expected = np.array([qualifying_young_person(p) for p in GRID])
    # Invariant 3.
    np.testing.assert_array_equal(uc, expected)
    np.testing.assert_array_equal(pc, expected)
    # Invariant 4. Rows are adjacent pairs: the 19th-birthday fact off, on.
    off, on = expected[0::2], expected[1::2]
    assert (on >= off).all()
    np.testing.assert_array_equal(
        on, [qualifying_young_person(p, terminal_date=False) for p in GRID[1::2]]
    )
    changed = on != off
    assert changed.any()
    assert all(
        p["age"] == 19 and studying(p) and not p[SIXTEEN]
        for p, c in zip(GRID[1::2], changed)
        if c
    )


def test_universal_credit_input_overrides_the_fact_for_universal_credit_only():
    # Invariant 2: a 19-year-old at school, with each programme's input set
    # against the fact.
    rows = list(product((False, True), repeat=2))
    people = [
        person(
            19,
            current_education="UPPER_SECONDARY",
            **{SIXTEEN: False, NINETEEN: nineteen, UC_TERMINAL: uc_terminal},
        )
        for nineteen, uc_terminal in rows
    ]
    sim = simulate(people)
    np.testing.assert_array_equal(sim.calculate(UC, YEAR), [u for _, u in rows])
    np.testing.assert_array_equal(sim.calculate(PC, YEAR), [n for n, _ in rows])


DEFAULTED = (
    NINETEEN,
    UC_TERMINAL,
    "meets_qualifying_young_person_terminal_date_condition_for_pension_credit",
)


def test_formula_is_true_under_20_and_is_each_default():
    # Invariant 5, from age and months alone: every age to 25 and every
    # month since the last birthday, in three years.
    rows = list(product(range(26), range(12)))
    for year in (2022, 2026, 2030):
        situation = {"people": {}, "benunits": {}, "households": {}}
        for i, (age, months) in enumerate(rows):
            situation["people"][f"p{i}"] = {
                "age": {year: age},
                "months_since_last_birthday": {year: months},
            }
            situation["benunits"][f"b{i}"] = {"members": [f"p{i}"]}
            situation["households"][f"h{i}"] = {"members": [f"p{i}"]}
        with patch(
            "policyengine_uk.simulation.CountryTaxBenefitSystem",
            side_effect=_PROPERTY_SYSTEM.clone,
        ):
            sim = Simulation(situation=situation)
        under_20 = np.array([age < 20 for age, _ in rows])
        for variable in DEFAULTED:
            values = sim.calculate(variable, year)
            assert values[under_20].all(), (variable, year)
            assert sim.tax_benefit_system.variables[variable].default_value is True
        # Not vacuous: the fact is false for some people of 20 or more.
        assert not sim.calculate(NINETEEN, year)[~under_20].all()


def test_setting_one_person_leaves_the_others_status():
    # Invariant 5 in a household: two 19-year-olds at school, course begun
    # at 17. Each terminal-date variable is set false for the first only;
    # the second stays a qualifying young person for both programmes.
    for variable in DEFAULTED:
        people = {
            "parent": {"age": {YEAR: 70}, "is_claimant_or_partner": {YEAR: True}},
            **{
                name: {
                    "age": {YEAR: 19},
                    "current_education": {YEAR: "UPPER_SECONDARY"},
                    "age_started_or_accepted_current_education_or_training": {YEAR: 17},
                    "is_claimant_or_partner": {YEAR: False},
                }
                for name in ("first", "second")
            },
        }
        people["first"][variable] = {YEAR: False}
        situation = {
            "people": people,
            "benunits": {"b": {"members": list(people)}},
            "households": {"h": {"members": list(people)}},
        }
        with patch(
            "policyengine_uk.simulation.CountryTaxBenefitSystem",
            side_effect=_PROPERTY_SYSTEM.clone,
        ):
            sim = Simulation(situation=situation)
        uc = sim.calculate(UC, YEAR)
        pc = sim.calculate(PC, YEAR)
        # The second student is a qualifying young person for both.
        assert uc[2] and pc[2], variable
        # The first loses the status the variable governs.
        if variable == UC_TERMINAL:
            assert not uc[1] and pc[1]
        elif variable == NINETEEN:
            assert not uc[1] and not pc[1]
        else:
            assert uc[1] and not pc[1]


def test_crossed_settings_need_the_programme_variable_for_everyone():
    # Invariant 5's qualification. Two 19-year-olds at school: the first has
    # the date fact set false, the second the programme variable set false.
    # Set for the second alone, the programme variable gives the first its
    # default (true), so the first becomes eligible again for that
    # programme; set for both, both are excluded, as the documentation says.
    def household(programme_variable, both):
        people = {
            "pensioner": {"age": {YEAR: 70}, "is_claimant_or_partner": {YEAR: True}},
            **{
                name: {
                    "age": {YEAR: 19},
                    "current_education": {YEAR: "UPPER_SECONDARY"},
                    "age_started_or_accepted_current_education_or_training": {YEAR: 17},
                    "is_claimant_or_partner": {YEAR: False},
                }
                for name in ("first", "second")
            },
        }
        people["first"][NINETEEN] = {YEAR: False}
        people["second"][programme_variable] = {YEAR: False}
        if both:
            people["first"][programme_variable] = {YEAR: False}
        situation = {
            "people": people,
            "benunits": {"b": {"members": list(people)}},
            "households": {"h": {"members": list(people)}},
        }
        with patch(
            "policyengine_uk.simulation.CountryTaxBenefitSystem",
            side_effect=_PROPERTY_SYSTEM.clone,
        ):
            return Simulation(situation=situation)

    for variable, status in (
        (UC_TERMINAL, UC),
        (
            "meets_qualifying_young_person_terminal_date_condition_for_pension_credit",
            PC,
        ),
    ):
        partial = household(variable, both=False).calculate(status, YEAR)
        # The documented hazard: the first student takes the default.
        assert partial[1] and not partial[2], variable
        full = household(variable, both=True).calculate(status, YEAR)
        assert not full[1] and not full[2], variable
