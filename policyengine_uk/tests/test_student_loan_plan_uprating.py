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
from policyengine_uk.data.economic_assumptions import extend_single_year_dataset
from policyengine_uk.system import system

AGES = range(18, 51)
PEOPLE_PER_AGE = 600
TAKE_UP = 0.4


def mock_dataset(base_year: int) -> UKSingleYearDataset:
    """MOCK data: tertiary-educated people in England, none with a loan."""
    ages = np.repeat(list(AGES), PEOPLE_PER_AGE)
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
            "region": "LONDON",
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
