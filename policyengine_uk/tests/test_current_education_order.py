"""current_education does not depend on the order of calculation.

The formula used to copy last year's value whenever one was stored, so a
year's enrolment depended on whether the year before had already been
calculated. Datasets enter every year through 2030 (extend_single_year_dataset),
so for eFRS 2024-25 a fresh 2032 imputed enrolment from age while 2032
calculated after 2031 kept the 2030 data.

Invariants:

1. Order independence: for any population, inputs, target year and sequence
   of years calculated first, the target year's value is bitwise equal to its
   value in a fresh simulation.
2. Reference semantics (differential): the value is the input for the year if
   there is one; otherwise the latest input for an earlier year; otherwise the
   age band of that year's age. Values the model calculated never carry.
3. A branch reads the same value as the simulation it was taken from.
"""

import numpy as np
import pandas as pd
import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation
from policyengine_uk.data.dataset_schema import UKSingleYearDataset
from policyengine_uk.utils.inputs import input_periods
from policyengine_uk.variables.household.demographic.highest_education import (
    EducationType,
)

EDUCATIONS = tuple(item.name for item in EducationType)
PROPERTY_SETTINGS = settings(
    max_examples=25,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow],
)


def age_band(age: float) -> str:
    """current_education's age imputation, written out independently."""
    if age < 4:
        return "PRE_PRIMARY"
    if age < 7:
        return "NOT_COMPLETED_PRIMARY"
    if age < 11:
        return "PRIMARY"
    if age < 14:
        return "LOWER_SECONDARY"
    if age < 16:
        return "UPPER_SECONDARY"
    if age < 18:
        return "POST_SECONDARY"
    if age < 20:
        return "TERTIARY"
    return "NOT_IN_EDUCATION"


def expected_enrolment(year, ages, entered, entered_years):
    """Invariant 2 for one person: ``ages`` maps year to age and ``entered``
    to the enrolment entered for them. Inputs are whole arrays, so in any
    year someone was given an enrolment (``entered_years``) everyone else
    holds the default as an entered value."""

    def value(input_year):
        return entered.get(input_year, "NOT_IN_EDUCATION")

    if year in entered_years:
        return value(year)
    earlier = [y for y in entered_years if y < year]
    if earlier:
        return value(max(earlier))
    return age_band(ages[year])


def household_simulation(people):
    """One single-person benefit unit and household per person. ``people`` is
    a list of (ages by year, entered enrolment by year)."""
    situation = {"people": {}, "benunits": {}, "households": {}}
    for index, (ages, entered) in enumerate(people):
        name = f"person_{index}"
        situation["people"][name] = {
            "age": {str(year): age for year, age in ages.items()},
            "current_education": {str(year): value for year, value in entered.items()},
        }
        situation["benunits"][f"benunit_{index}"] = {"members": [name]}
        situation["households"][f"household_{index}"] = {"members": [name]}
    return Simulation(situation=situation)


def enrolment(simulation, year):
    return np.asarray(simulation.calculate("current_education", year))


def small_dataset():
    """Three people whose data enrolment differs from the age imputation."""
    return UKSingleYearDataset(
        person=pd.DataFrame(
            {
                "person_id": [1, 2, 3],
                "person_benunit_id": [1, 2, 3],
                "person_household_id": [1, 2, 3],
                "age": [30.0, 17.0, 12.0],
                "current_education": ["TERTIARY", "NOT_IN_EDUCATION", "PRIMARY"],
            }
        ),
        benunit=pd.DataFrame({"benunit_id": [1, 2, 3]}),
        household=pd.DataFrame(
            {
                "household_id": [1, 2, 3],
                "region": ["LONDON", "NORTH_WEST", "WALES"],
                "tenure_type": [
                    "RENT_PRIVATELY",
                    "OWNED_OUTRIGHT",
                    "RENT_FROM_COUNCIL",
                ],
                "council_tax": [1_500.0, 1_200.0, 1_300.0],
                "rent": [12_000.0, 0.0, 6_000.0],
                "household_weight": [1.0, 1.0, 1.0],
            }
        ),
        fiscal_year=2025,
    )


DATA_ENROLMENT = ["TERTIARY", "NOT_IN_EDUCATION", "PRIMARY"]


@pytest.mark.parametrize(
    "order",
    [
        (2032,),
        (2031, 2032),
        (2033, 2032),
        (2031, 2033, 2032),
        (2025, 2030, 2032),
    ],
)
def test_years_past_the_data_keep_the_last_data_year_in_any_order(order):
    # The data covers 2025-2030 after extension; later years keep 2030's
    # enrolment whatever was calculated first, never the age imputation
    # (TERTIARY at 17, LOWER_SECONDARY at 12, NOT_IN_EDUCATION at 30).
    simulation = Simulation(dataset=small_dataset())
    assert [
        period.start.year for period in input_periods(simulation, "current_education")
    ] == list(range(2025, 2031))
    for year in order:
        simulation.calculate("current_education", year)
    assert list(enrolment(simulation, 2032)) == DATA_ENROLMENT
    assert list(enrolment(Simulation(dataset=small_dataset()), 2032)) == (
        DATA_ENROLMENT
    )


def test_fresh_year_equals_the_year_after_the_one_before_it():
    # The originally reported case: fresh 2032 against 2032 after 2031.
    fresh = enrolment(Simulation(dataset=small_dataset()), 2032)
    after = Simulation(dataset=small_dataset())
    after.calculate("current_education", 2031)
    assert np.array_equal(fresh, enrolment(after, 2032))


def test_an_entered_enrolment_carries_forward_past_years_with_no_input():
    simulation = household_simulation(
        [({2024: 30, 2025: 30, 2026: 30}, {2024: "TERTIARY"})]
    )
    assert list(enrolment(simulation, 2026)) == ["TERTIARY"]
    simulation = household_simulation(
        [({2024: 30, 2025: 30, 2026: 30}, {2024: "TERTIARY"})]
    )
    simulation.calculate("current_education", 2025)
    assert list(enrolment(simulation, 2026)) == ["TERTIARY"]


def test_without_an_earlier_input_enrolment_is_imputed_from_that_years_age():
    # The input for 2027 does not reach back to 2025, and calculating 2027 or
    # 2028 first does not change 2025.
    ages = {2025: 17, 2026: 18, 2027: 19, 2028: 20}
    for first in [(), (2027,), (2028, 2026)]:
        simulation = household_simulation([(ages, {2027: "NOT_IN_EDUCATION"})])
        for year in first:
            simulation.calculate("current_education", year)
        assert list(enrolment(simulation, 2025)) == ["POST_SECONDARY"]
        assert list(enrolment(simulation, 2026)) == ["TERTIARY"]
        assert list(enrolment(simulation, 2028)) == ["NOT_IN_EDUCATION"]


def test_calculated_values_never_carry_forward():
    # 2025 is imputed (TERTIARY at 19); 2026 is imputed from its own age, not
    # copied from the stored 2025 value.
    ages = {2025: 19, 2026: 25}
    simulation = household_simulation([(ages, {})])
    assert list(enrolment(simulation, 2025)) == ["TERTIARY"]
    assert list(enrolment(simulation, 2026)) == ["NOT_IN_EDUCATION"]
    assert input_periods(simulation, "current_education") == []


def test_a_branch_reads_the_same_enrolment():
    simulation = Simulation(dataset=small_dataset())
    branch = simulation.get_branch("pay_rise")
    assert list(enrolment(branch, 2032)) == DATA_ENROLMENT
    assert np.array_equal(enrolment(branch, 2032), enrolment(simulation, 2032))


YEARS = range(2023, 2034)


@st.composite
def people_and_order(draw):
    people = []
    for _ in range(draw(st.integers(1, 3))):
        base_age = draw(st.integers(0, 30))
        ages_with_time = draw(st.booleans())
        ages = {
            year: base_age + (year - 2023 if ages_with_time else 0) for year in YEARS
        }
        entered_years = draw(
            st.lists(st.sampled_from(range(2024, 2029)), max_size=3, unique=True)
        )
        entered = {year: draw(st.sampled_from(EDUCATIONS)) for year in entered_years}
        people.append((ages, entered))
    target = draw(st.sampled_from(range(2024, 2033)))
    first = draw(st.lists(st.sampled_from(YEARS), max_size=4))
    return people, target, first


@PROPERTY_SETTINGS
@given(people_and_order())
def test_enrolment_is_order_independent_and_matches_the_reference(case):
    people, target, first = case
    fresh = enrolment(household_simulation(people), target)
    ordered = household_simulation(people)
    for year in first:
        ordered.calculate("current_education", year)
    after = enrolment(ordered, target)
    # Invariant 1, bitwise.
    assert np.array_equal(fresh, after)
    # Invariant 2.
    entered_years = {year for _, entered in people for year in entered}
    expected = [
        expected_enrolment(target, ages, entered, entered_years)
        for ages, entered in people
    ]
    assert list(fresh) == expected
