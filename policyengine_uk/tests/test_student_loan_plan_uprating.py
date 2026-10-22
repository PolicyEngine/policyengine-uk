"""Student loan plans in projected years (uprate_student_loan_plans, #2572).

Projected datasets copy the base year with ages fixed, so in a later year a
person of a given age stands for a later university intake. Tertiary-educated
people without a loan in the data, above the base year's oldest holder of a
plan, take up that plan at a flat rate in later years. The base year is the
dataset's own, and each person's draw is keyed on person_id.
"""

import numpy as np
import pandas as pd
import pytest

from policyengine_uk.data import UKSingleYearDataset
from policyengine_uk.data.economic_assumptions import (
    extend_single_year_dataset,
    uprate_student_loan_plans,
)
from policyengine_uk.system import system

AGES = range(18, 51)
PEOPLE_PER_AGE = 600
TAKE_UP = 0.4


def mock_dataset(
    base_year: int,
    *,
    ages=AGES,
    region="LONDON",
    people_per_age=PEOPLE_PER_AGE,
) -> UKSingleYearDataset:
    """MOCK data: tertiary-educated people, none with a loan."""
    ages = np.repeat(list(ages), people_per_age)
    ids = np.arange(1, len(ages) + 1)
    person = pd.DataFrame(
        {
            "person_id": ids,
            "person_benunit_id": ids,
            "person_household_id": ids,
            "age": ages,
            "student_loan_plan": "NONE",
            "highest_education": "TERTIARY",
            "student_loan_repayments": 0.0,
        }
    )
    household = pd.DataFrame(
        {
            "household_id": ids,
            "household_weight": 1.0,
            "region": region,
            "tenure_type": "OWNED_OUTRIGHT",
            "rent": 0.0,
            "council_tax": 0.0,
        }
    )
    return UKSingleYearDataset(
        person=person,
        benunit=pd.DataFrame({"benunit_id": ids}),
        household=household,
        fiscal_year=base_year,
    )


def projected_plans(base_year: int, end_year: int = 2029) -> dict[int, pd.DataFrame]:
    projected = extend_single_year_dataset(
        mock_dataset(base_year), system.parameters, end_year=end_year
    )
    return {
        year: projected.datasets[year].person.set_index("person_id")[
            ["age", "student_loan_plan"]
        ]
        for year in projected.datasets
    }


@pytest.fixture(scope="module")
def from_2024():
    return projected_plans(2024)


def share(plans: pd.DataFrame, plan: str, ages) -> float:
    band = plans[plans.age.isin(list(ages))]
    return (band.student_loan_plan == plan).mean()


def test_new_plan_2_holders_are_aged_31_to_35_in_2029(from_2024):
    # The 2012 intake was 30 in 2024. By 2029, with ages fixed, Plan 2 covers
    # intakes up to age 35 (started 2012), so ages 31 to 35 take it up.
    plans = from_2024[2029]
    assert share(plans, "PLAN_2", range(31, 36)) == pytest.approx(TAKE_UP, abs=0.03)
    assert share(plans, "PLAN_2", range(25, 31)) == 0
    assert share(plans, "PLAN_2", range(36, 51)) == 0


def test_the_base_year_comes_from_the_dataset(from_2024):
    # With a 2023 base the oldest Plan 2 holder was 29, so 30-year-olds take
    # it up too. With a 2024 base they were already covered by the data.
    from_2023 = projected_plans(2023)[2029]
    assert share(from_2023, "PLAN_2", [30]) == pytest.approx(TAKE_UP, abs=0.06)
    assert share(from_2024[2029], "PLAN_2", [30]) == 0


def test_new_plan_1_holders_are_older_than_the_first_income_contingent_intake(
    from_2024,
):
    # The 1998 intake was 44 in 2024; loans are written off 29 years after
    # the intake, so from 47.
    plans = from_2024[2029]
    assert share(plans, "PLAN_1", range(45, 47)) == pytest.approx(TAKE_UP, abs=0.05)
    assert share(plans, "PLAN_1", range(36, 45)) == 0
    assert share(plans, "PLAN_1", range(47, 51)) == 0


def test_a_persons_draw_is_the_same_in_every_year(from_2024):
    # Ages 31 to 34 are in the Plan 2 band in both 2028 and 2029.
    in_band = from_2024[2028].age.between(31, 34)
    took_up_2028 = from_2024[2028].student_loan_plan[in_band] == "PLAN_2"
    took_up_2029 = from_2024[2029].student_loan_plan[in_band] == "PLAN_2"
    assert took_up_2028.any()
    pd.testing.assert_series_equal(took_up_2028, took_up_2029)


def test_draws_do_not_depend_on_row_order(from_2024):
    dataset = mock_dataset(2024)
    order = np.random.default_rng(0).permutation(len(dataset.person))
    shuffled = UKSingleYearDataset(
        person=dataset.person.iloc[order].reset_index(drop=True),
        benunit=dataset.benunit,
        household=dataset.household,
        fiscal_year=2024,
    )
    projected = extend_single_year_dataset(shuffled, system.parameters, end_year=2029)
    plans = projected.datasets[2029].person.set_index("person_id").student_loan_plan
    pd.testing.assert_series_equal(
        plans.sort_index(), from_2024[2029].student_loan_plan.sort_index()
    )


@pytest.fixture
def all_graduates_take_up(monkeypatch):
    """Make the funding-plan regressions independent of random take-up."""
    monkeypatch.setattr(
        "policyengine_uk.data.economic_assumptions.splitmix64_uniform",
        lambda ids, salt: np.zeros(len(ids)),
    )


@pytest.mark.parametrize(
    "region, expected_plan",
    [
        ("LONDON", "PLAN_2"),
        ("WALES", "PLAN_2"),
        ("SCOTLAND", "PLAN_4"),
        ("NORTHERN_IRELAND", "PLAN_1"),
        ("UNKNOWN", "NONE"),
    ],
)
def test_extended_2012_intakes_follow_funding_nation(
    all_graduates_take_up, region, expected_plan
):
    # GOV.UK: England/Wales 2012-2022 undergraduate intakes use Plan 2;
    # SAAS uses Plan 4 and Student Finance NI uses Plan 1. Residence proxies
    # for funding nation. In 2024 the 2012 intake was 30; projecting to 2029
    # adds ages 31 (2016 intake) through 35 (2012 intake). Ages 30 and 36
    # remain outside this new band. Unknown residence supplies no proxy.
    dataset = mock_dataset(2024, ages=[30, 31, 35, 36], region=region, people_per_age=1)
    projected = extend_single_year_dataset(dataset, system.parameters, end_year=2029)
    assert projected.datasets[2029].person.student_loan_plan.tolist() == [
        "NONE",
        expected_plan,
        expected_plan,
        "NONE",
    ]


@pytest.mark.parametrize(
    "region, expected_plan",
    [
        ("LONDON", "PLAN_1"),
        ("WALES", "PLAN_1"),
        ("SCOTLAND", "PLAN_4"),
        ("NORTHERN_IRELAND", "PLAN_1"),
    ],
)
def test_extended_pre_2012_intakes_follow_funding_nation(
    all_graduates_take_up, region, expected_plan
):
    # The existing extension starts above age 44 (2024 - 1998 + 18).
    # In 2029 ages 45/46 represent the 2002/2001 intakes: England/Wales
    # use Plan 1 before September 2012; SAAS uses Plan 4; NI uses Plan 1.
    previous = mock_dataset(2024, ages=[44, 45, 46], region=region, people_per_age=1)
    current = previous.copy()
    current.time_period = "2029"
    projected = uprate_student_loan_plans(current, previous, system.parameters)
    assert projected.person.student_loan_plan.tolist() == [
        "NONE",
        expected_plan,
        expected_plan,
    ]


@pytest.mark.parametrize(
    "region, plan_from_2023, plan_before_2023",
    [
        ("LONDON", "PLAN_5", "PLAN_2"),
        ("WALES", "PLAN_2", "PLAN_2"),
        ("SCOTLAND", "PLAN_4", "PLAN_4"),
        ("NORTHERN_IRELAND", "PLAN_1", "PLAN_1"),
        ("UNKNOWN", "NONE", "NONE"),
    ],
)
def test_new_intakes_follow_funding_nation_and_entry_year(
    all_graduates_take_up, region, plan_from_2023, plan_before_2023
):
    # https://www.gov.uk/repaying-your-student-loan/which-repayment-plan-you-are-on
    # Only England switches to Plan 5 in 2023; Wales retains Plan 2.
    # In 2029 age 24 represents entry in 2023, age 25 entry in 2022.
    # A 2018 base's Plan 2 coverage ends at 24, so both are newly assigned.
    # Age 21 (2026 entry) qualifies; age 20 has not finished a degree.
    previous = mock_dataset(
        2018, ages=[20, 21, 24, 25], region=region, people_per_age=1
    )
    current = previous.copy()
    current.time_period = "2029"
    projected = uprate_student_loan_plans(current, previous, system.parameters)
    assert projected.person.student_loan_plan.tolist() == [
        "NONE",
        plan_from_2023,
        plan_from_2023,
        plan_before_2023,
    ]
