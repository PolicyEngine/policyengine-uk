"""HB reg 74 / SPC reg 55 and SPC reg 59: factual exception and change cases."""

import json

import numpy as np
import pytest

from policyengine_uk import Simulation


def non_dep_simulation(
    *,
    year=2026,
    claimant=None,
    non_dep=None,
    family=None,
    country="ENGLAND",
    other_claim=None,
):
    claimant_values = {"age": 70, "is_claimant_or_partner": True}
    claimant_values.update(claimant or {})
    non_dep_values = {
        "age": 30,
        "is_claimant_or_partner": True,
        "is_non_dependant_of_household_head": True,
        "household_benefits_individual_non_dep_deduction": 40 * 52,
        "housing_benefit_non_dep_full_time_student": False,
    }
    non_dep_values.update(non_dep or {})
    claim = {
        "housing_benefit_pension_age_regulations_apply": True,
        "housing_benefit_assessment_date": "2026-10-06",
        "housing_benefit_continuous_award_start": "2020-01-01",
        "benunit_is_rent_liable": True,
        "share_of_household_rent": 1,
    }
    claim.update(family or {})
    people = {"claimant": claimant_values, "non_dep": non_dep_values}
    families = {
        "claim": {"members": ["claimant"], **claim},
        "non_dep_family": {
            "members": ["non_dep"],
            "benunit_is_rent_liable": False,
            "share_of_household_rent": 0,
            "housing_benefit_pension_age_regulations_apply": False,
        },
    }
    if other_claim:
        people["other_claimant"] = {"age": 40, "is_claimant_or_partner": True}
        families["other_claim"] = {
            "members": ["other_claimant"],
            "benunit_is_rent_liable": True,
            "housing_benefit_pension_age_regulations_apply": False,
            "share_of_household_rent": 0.5,
            **other_claim,
        }
        families["claim"]["share_of_household_rent"] = 0.5
    situation = {
        "people": {
            name: {key: {str(year): value} for key, value in values.items()}
            for name, values in people.items()
        },
        "benunits": {
            name: {
                key: value if key == "members" else {str(year): value}
                for key, value in values.items()
            }
            for name, values in families.items()
        },
        "households": {
            "home": {"members": list(people), "country": {str(year): country}}
        },
    }
    return Simulation(situation=situation)


def history(*events, previous=20, last="2020-01-01", person_id="non_dep"):
    return json.dumps(
        [
            {
                "person_id": person_id,
                "previous_weekly_deduction": previous,
                "last_effective_date": last,
                "increases": [{"date": day, "kind": kind} for day, kind in events],
            }
        ]
    )


@pytest.mark.parametrize(
    "facts,exempt",
    [
        ({"housing_benefit_non_dep_normal_home_elsewhere": True}, True),
        ({"housing_benefit_non_dep_youth_training_allowance": True}, True),
        (
            {
                "age": 24,
                "esa_income_reported": 1000,
                "esa_support_group": False,
                "esa_work_related_activity_group": False,
            },
            True,
        ),
        (
            {
                "age": 24,
                "esa_income_reported": 1000,
                "esa_work_related_activity_group": True,
            },
            False,
        ),
        ({"age": 24, "esa_income_reported": 1000, "esa_support_group": True}, False),
        ({"age": 25, "esa_income_reported": 1000}, False),
        (
            {
                "housing_benefit_non_dep_absent": True,
                "is_hospital_inpatient": True,
                "housing_benefit_non_dep_linked_inpatient_days": 364,
            },
            False,
        ),
        (
            {
                "housing_benefit_non_dep_absent": True,
                "is_hospital_inpatient": True,
                "housing_benefit_non_dep_linked_inpatient_days": 365,
            },
            True,
        ),
        (
            {
                "housing_benefit_non_dep_absent": False,
                "is_hospital_inpatient": True,
                "housing_benefit_non_dep_linked_inpatient_days": 365,
            },
            False,
        ),
        (
            {
                "housing_benefit_non_dep_absent": True,
                "is_in_prison": True,
                "housing_benefit_non_dep_custody_excludes_mental_health_hospital": True,
            },
            True,
        ),
        (
            {
                "housing_benefit_non_dep_absent": True,
                "is_in_prison": True,
                "housing_benefit_non_dep_custody_excludes_mental_health_hospital": False,
            },
            False,
        ),
        (
            {
                "housing_benefit_non_dep_absent": True,
                "housing_benefit_non_dep_military_operations": True,
            },
            True,
        ),
        (
            {
                "housing_benefit_non_dep_absent": False,
                "housing_benefit_non_dep_military_operations": True,
            },
            False,
        ),
    ],
)
def test_additional_exception_facts(facts, exempt):
    simulation = non_dep_simulation(non_dep=facts)
    assert (
        bool(
            simulation.calculate("housing_benefit_non_dep_additional_exception", 2026)[
                1
            ]
        )
        is exempt
    )
    assert (
        bool(
            simulation.calculate(
                "housing_benefit_individual_non_dep_deduction_eligible", 2026
            )[1]
        )
        is not exempt
    )


@pytest.mark.parametrize(
    "pension,summer,study,works,expected",
    [
        (False, False, True, True, 0),
        (False, True, False, False, 0),
        (False, True, False, True, 40 * 52),
        (True, True, False, True, 0),
    ],
)
def test_student_study_summer_work_and_pension_rules(
    pension, summer, study, works, expected
):
    simulation = non_dep_simulation(
        claimant={"age": 70 if pension else 40, "is_SP_age": pension},
        family={"housing_benefit_pension_age_regulations_apply": pension},
        non_dep={
            "housing_benefit_non_dep_full_time_student": True,
            "housing_benefit_non_dep_period_of_study": study,
            "housing_benefit_non_dep_summer_vacation": summer,
            "housing_benefit_remunerative_work": works,
        },
    )
    assert (
        simulation.calculate("housing_benefit_non_dep_deductions", 2026)[0] == expected
    )


@pytest.mark.parametrize(
    "country,age,expected",
    [
        ("ENGLAND", 64, 0),
        ("NORTHERN_IRELAND", 64, 40 * 52),
        ("NORTHERN_IRELAND", 65, 0),
    ],
)
def test_pension_student_ni_retains_age_65_condition(country, age, expected):
    simulation = non_dep_simulation(
        country=country,
        claimant={"age": age},
        non_dep={
            "housing_benefit_non_dep_full_time_student": True,
            "housing_benefit_non_dep_period_of_study": False,
            "housing_benefit_non_dep_summer_vacation": True,
            "housing_benefit_remunerative_work": True,
        },
    )
    assert (
        simulation.calculate("housing_benefit_non_dep_deductions", 2026)[0] == expected
    )


def test_unrelated_pensioner_does_not_exempt_other_claimant_student():
    simulation = non_dep_simulation(
        non_dep={
            "housing_benefit_non_dep_full_time_student": True,
            "housing_benefit_non_dep_period_of_study": False,
            "housing_benefit_non_dep_summer_vacation": True,
            "housing_benefit_remunerative_work": True,
        },
        other_claim={"housing_benefit_pension_age_regulations_apply": False},
    )
    np.testing.assert_allclose(
        simulation.calculate("housing_benefit_non_dep_deductions", 2026),
        [0, 0, 20 * 52],
    )


@pytest.mark.parametrize(
    "date,expected", [("2026-10-11", 20 * 52), ("2026-10-12", 40 * 52)]
)
@pytest.mark.parametrize("country", ["ENGLAND", "NORTHERN_IRELAND"])
def test_pension_increase_postponed_and_rounded_to_monday(date, expected, country):
    simulation = non_dep_simulation(
        country=country,
        family={
            "housing_benefit_assessment_date": date,
            "housing_benefit_non_dep_increase_history": history(
                ("2026-04-08", "circumstances")
            ),
        },
    )
    assert (
        simulation.calculate("housing_benefit_non_dep_deductions", 2026)[0] == expected
    )


def test_second_increase_does_not_restart_clock():
    simulation = non_dep_simulation(
        family={
            "housing_benefit_assessment_date": "2026-10-12",
            "housing_benefit_non_dep_increase_history": history(
                ("2026-04-08", "circumstances"), ("2026-08-01", "circumstances")
            ),
        }
    )
    assert (
        simulation.calculate("housing_benefit_non_dep_deductions", 2026)[0] == 40 * 52
    )


@pytest.mark.parametrize(
    "events,previous,award_start,current,expected",
    [
        ([("2026-08-01", "arrival")], 0, "2020-01-01", 40, 0),
        ([("2026-04-01", "uprating")], 20, "2020-01-01", 40, 40),
        ([("2026-01-01", "arrival")], 0, "2026-05-01", 40, 40),
        ([("2026-08-01", "circumstances")], 40, "2020-01-01", 20, 20),
        ([("2026-08-01", "circumstances")], 20, "2020-01-01", 0, 0),
    ],
)
def test_arrival_uprating_initial_claim_reductions_and_exemptions(
    events, previous, award_start, current, expected
):
    simulation = non_dep_simulation(
        non_dep={"household_benefits_individual_non_dep_deduction": current * 52},
        family={
            "housing_benefit_continuous_award_start": award_start,
            "housing_benefit_non_dep_increase_history": history(
                *events, previous=previous
            ),
        },
    )
    assert (
        simulation.calculate("housing_benefit_non_dep_deductions", 2026)[0]
        == expected * 52
    )


def test_postponement_is_claim_specific_before_rent_allocation():
    simulation = non_dep_simulation(
        family={
            "housing_benefit_non_dep_increase_history": history(
                ("2026-08-01", "arrival"), previous=0
            )
        },
        other_claim={
            "housing_benefit_pension_age_regulations_apply": True,
            "housing_benefit_continuous_award_start": "2026-09-01",
            "housing_benefit_non_dep_increase_history": history(
                ("2026-08-01", "arrival"), previous=0
            ),
        },
    )
    np.testing.assert_allclose(
        simulation.calculate("housing_benefit_non_dep_deductions", 2026),
        [0, 0, 20 * 52],
    )


@pytest.mark.parametrize(
    "bad",
    [
        "not JSON",
        "{}",
        '[{"person_id":"non_dep"}]',
        history(("2026-08-01", "circumstances"), previous=-1),
        history(("2026-08-01", "unknown")),
        history(("2026-08-01", "arrival"), person_id="missing"),
    ],
)
def test_invalid_postponement_history_is_not_silently_accepted(bad):
    simulation = non_dep_simulation(
        family={"housing_benefit_non_dep_increase_history": bad}
    )
    with pytest.raises(ValueError):
        simulation.calculate("housing_benefit_non_dep_deductions", 2026)
