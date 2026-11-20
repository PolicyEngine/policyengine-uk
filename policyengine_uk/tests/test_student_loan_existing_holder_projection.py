"""Preserve observed plans when projection lacks loan dates (#2636).

GOV.UK's plan and cancellation rules depend on funding agency, course dates,
first loan payment and April first due to repay. Current age and residence do
not supply those facts:
https://www.gov.uk/repaying-your-student-loan/which-repayment-plan-you-are-on
https://www.gov.uk/repaying-your-student-loan/when-your-student-loan-gets-written-off-or-cancelled

These tests specify the conservative missing-date projection contract: retain
the observed category and stored repayment. They do not assert exact legal
write-off dates, infer a mature starter's intake, or change repayment precedence.
"""

import pandas as pd
import pytest

from policyengine_uk.data import UKSingleYearDataset
from policyengine_uk.data.economic_assumptions import uprate_student_loan_plans
from policyengine_uk.system import system


def observed_holders(rows):
    """Build small synthetic observations; no course or funding dates exist."""
    person = pd.DataFrame(
        [
            {
                "person_id": person_id,
                "person_benunit_id": 2000 + position,
                "person_household_id": 1000 + position,
                "age": age,
                "student_loan_plan": plan,
                "highest_education": "TERTIARY" if age >= 21 else "SECONDARY",
                "student_loan_repayments": repayment,
            }
            for position, (person_id, age, plan, region, repayment) in enumerate(rows)
        ]
    )
    household = pd.DataFrame(
        [
            {
                "household_id": 1000 + position,
                "household_weight": 1.0,
                "region": region,
                "tenure_type": "OWNED_OUTRIGHT",
                "rent": 0.0,
                "council_tax": 0.0,
            }
            for position, (_, _, _, region, _) in enumerate(rows)
        ]
    )
    return UKSingleYearDataset(
        person=person,
        benunit=pd.DataFrame({"benunit_id": 2000 + pd.RangeIndex(len(rows))}),
        household=household,
        fiscal_year=2024,
    )


def project_observations(base, year, *, explicit_base_year=True, order=None):
    current = base.copy()
    current.time_period = str(year)
    if order is not None:
        current.person = current.person.iloc[order].reset_index(drop=True)
        current.household = current.household.iloc[::-1].reset_index(drop=True)
    kwargs = {"base_year": 2024} if explicit_base_year else {}
    return uprate_student_loan_plans(current, base, system.parameters, **kwargs)


def assert_observation(result, plan, repayment=500.0):
    assert result.person.student_loan_repayments.tolist() == [repayment]
    assert result.person.student_loan_plan.tolist() == [plan]


def test_existing_ni_plan_1_is_preserved_in_first_projection():
    # Residence does not prove funding agency. The observed category takes
    # precedence under the missing-date contract, not an inferred age-18 intake.
    base = observed_holders([(1, 25, "PLAN_1", "NORTHERN_IRELAND", 500.0)])
    assert_observation(project_observations(base, 2025), "PLAN_1")


@pytest.mark.parametrize(
    "age,plan,region",
    [
        (33, "PLAN_2", "LONDON"),
        (45, "PLAN_1", "LONDON"),
        (50, "PLAN_1", "LONDON"),
        (30, "PLAN_4", "SCOTLAND"),
        (40, "PLAN_4", "SCOTLAND"),
        (22, "PLAN_2", "WALES"),
        (28, "POSTGRADUATE", "LONDON"),
    ],
    ids=[
        "plan2-age33",
        "plan1-age45",
        "plan1-age50",
        "plan4-age30",
        "plan4-age40",
        "welsh-plan2",
        "postgraduate",
    ],
)
def test_reported_existing_holder_profiles_keep_observations(age, plan, region):
    # With the NI example above, these are the issue's eight profiles. Age33
    # plus PLAN_2 does not identify the reported mature starter's 2014 intake.
    base = observed_holders([(41, age, plan, region, 500.0)])
    assert_observation(project_observations(base, 2025), plan)


@pytest.mark.parametrize(
    "age,plan,region",
    [
        (30, "PLAN_4", "LONDON"),
        (25, "PLAN_1", "SCOTLAND"),
        (40, "PLAN_4", "UNKNOWN"),
        (22, "PLAN_5", "UNKNOWN"),
    ],
    ids=["plan4-mover", "plan1-mover", "unknown-region-plan4", "unknown-region-plan5"],
)
def test_known_category_does_not_follow_current_residence(age, plan, region):
    base = observed_holders([(73, age, plan, region, 500.0)])
    assert_observation(project_observations(base, 2025), plan)


@pytest.mark.parametrize("age", [64, 65])
def test_age_alone_does_not_establish_write_off(age):
    # Retention at65 is explicitly the missing-date fallback. No first-payment
    # date is observed, so this is not a claim about pre2006 legal cancellation.
    base = observed_holders([(9, age, "PLAN_1", "LONDON", 500.0)])
    assert_observation(project_observations(base, 2025), "PLAN_1")


MIXED_OBSERVATIONS = [
    (900, 50, "PLAN_1", "LONDON", 120.0),
    (42, 33, "PLAN_2", "UNKNOWN", 250.0),
    (1337, 30, "PLAN_4", "LONDON", 0.0),
    (8, 25, "PLAN_5", "SCOTLAND", 123.0),
    (77, 28, "POSTGRADUATE", "WALES", 499.5),
    (5, 10, "NONE", "NORTHERN_IRELAND", 0.0),
]


def observations_by_person(dataset):
    return dataset.person.set_index("person_id")[
        ["student_loan_plan", "student_loan_repayments"]
    ].sort_index()


def test_mixed_rows_keep_person_identity_and_original_base():
    base = observed_holders(MIXED_OBSERVATIONS)
    original_tables = {
        name: getattr(base, name).copy(deep=True)
        for name in ("person", "benunit", "household")
    }
    expected = observations_by_person(base).copy(deep=True)
    projected = project_observations(base, 2025, order=[5, 2, 4, 0, 3, 1])
    pd.testing.assert_frame_equal(observations_by_person(projected), expected)
    for name, original in original_tables.items():
        pd.testing.assert_frame_equal(getattr(base, name), original)


@pytest.mark.parametrize(
    "explicit_base_year", [True, False], ids=["explicit", "fallback"]
)
def test_repeated_projection_starts_from_original_observations(explicit_base_year):
    base = observed_holders(MIXED_OBSERVATIONS)
    expected = observations_by_person(base).copy(deep=True)
    # Going back to2025 between two2040 projections must not accumulate state.
    for year in (2040, 2025, 2040):
        projected = project_observations(
            base, year, explicit_base_year=explicit_base_year
        )
        pd.testing.assert_frame_equal(observations_by_person(projected), expected)
    pd.testing.assert_frame_equal(observations_by_person(base), expected)
