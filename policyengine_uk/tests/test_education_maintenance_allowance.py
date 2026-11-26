"""Focused EMA receipt timing, cash accounting and legacy-input regressions.

The weekly oracles are GBP40 (Wales) and GBP30 (Northern Ireland), with
institution-qualified NI bonuses of GBP100. Receipt inputs allocate an actual
AY2026/27 award to fiscal years; they do not create a calendar or attendance
ledger. This model adds EMA to HBAI net income as education income and leaves
the HBAI benefits subtotal unchanged.
"""

import copy

import numpy as np
import pytest
from policyengine_core.periods import period

from policyengine_uk import Simulation


pytestmark = pytest.mark.usefixtures("cloned_uk_tax_benefit_system")
YEAR = 2026
PAYMENT = "education_maintenance_allowance"


def assessment(country="WALES"):
    """A source-qualified assessment; no production eligibility helper is used."""
    facts = {
        "ema_assessment_country": country,
        "ema_academic_year": 2026,
        "ema_date_of_birth": 20090401,
        "ema_residency_conditions_met": True,
        "ema_financial_category": "DEPENDENT",
        "ema_assessed_income": 0,
        "ema_income_is_known": True,
        "ema_course_type": "FURTHER_EDUCATION",
        "ema_provider_approved": True,
        "ema_course_is_full_time": True,
        "ema_course_learning_hours": 15,
        "ema_course_duration_weeks": 40,
        "ema_qualification_level": 2,
        "ema_school_leaving_academic_year": 2025,
        "ema_prior_supported_academic_years": 0,
        "ema_prior_positive_or_negative_confirmations": 0,
    }
    return facts


def test_receipts_require_real_inputs_in_the_exact_supported_fiscal_year():
    # The January and June bonuses can belong to different fiscal years. A
    # genuine AY assessment may be reused, but received weeks/bonuses may not.
    student = {
        name: {year: value for year in (2025, 2026, 2027, 2028)}
        for name, value in assessment("NORTHERN_IRELAND").items()
    }
    student["age"] = {2026: 17, 2027: 18}
    student["ema_payable_weeks"] = {2025: 2, 2026: 2, 2028: 2}
    student["ema_qualifying_bonus_count"] = {2025: 1, 2026: 1, 2028: 1}
    situation = {
        "people": {"person1": student},
        "benunits": {"benunit": {"members": ["person1"]}},
        "households": {"household": {"members": ["person1"]}},
    }
    sim = Simulation(situation=copy.deepcopy(situation))
    assert sim.calculate(PAYMENT, 2026).tolist() == [160]
    assert sim.calculate(PAYMENT, 2027).tolist() == [0]
    assert sim.calculate(PAYMENT, 2025).tolist() == [0]
    assert sim.calculate(PAYMENT, 2028).tolist() == [0]

    derived = Simulation(situation=copy.deepcopy(situation))
    for name, value in (("ema_payable_weeks", 9), ("ema_qualifying_bonus_count", 2)):
        derived.get_holder(name).put_in_cache(
            np.array([value]), period(2027), derived.branch_name, derived=True
        )
    assert derived.calculate(PAYMENT, 2027).tolist() == [0]

    actual = copy.deepcopy(situation)
    actual["people"]["person1"]["ema_payable_weeks"][2027] = 3
    actual["people"]["person1"]["ema_qualifying_bonus_count"][2027] = 1
    actual["people"]["person1"]["ema_prior_positive_or_negative_confirmations"] = {
        2026: 0,
        2027: 2,
    }
    paid = Simulation(situation=actual)
    assert paid.calculate(PAYMENT, 2026).tolist() == [160]
    assert paid.calculate(PAYMENT, 2027).tolist() == [190]


def paired_award(situation):
    without = copy.deepcopy(situation)
    with_payment = copy.deepcopy(situation)
    for source, accepted in ((without, False), (with_payment, True)):
        student = source["people"]["person2"]
        student.update({name: {YEAR: value} for name, value in assessment().items()})
        student["ema_residency_conditions_met"] = {YEAR: accepted}
        student["ema_payable_weeks"] = {YEAR: 2}
    return Simulation(situation=without), Simulation(situation=with_payment)


def assert_cash_and_neutrality(control, recipient, positive_awards):
    np.testing.assert_array_equal(control.calculate(PAYMENT, YEAR), [0, 0])
    np.testing.assert_array_equal(recipient.calculate(PAYMENT, YEAR), [0, 80])
    for name in positive_awards:
        assert control.calculate(name, YEAR).sum() > 0, name
    for name in (
        "income_tax",
        "national_insurance",
        "universal_credit",
        "housing_benefit",
        "council_tax_benefit",
        "benefit_cap_reduction",
        "hbai_benefits",
    ):
        np.testing.assert_array_equal(
            recipient.calculate(name, YEAR), control.calculate(name, YEAR), err_msg=name
        )
    for name in (
        "household_benefits",
        "household_net_income",
        "hbai_household_net_income",
        "gov_spending",
    ):
        change = (
            recipient.calculate(name, YEAR).sum() - control.calculate(name, YEAR).sum()
        )
        assert change == pytest.approx(80, abs=0.01, rel=0), name
    change = (
        recipient.calculate("gov_balance", YEAR).sum()
        - control.calculate("gov_balance", YEAR).sum()
    )
    assert change == pytest.approx(-80, abs=0.01, rel=0)


def test_new_welsh_cash_keeps_positive_tax_ni_and_uc_and_adds_education_income_once():
    situation = {
        "people": {
            "person1": {
                "age": {YEAR: 40},
                "employment_income": {YEAR: 20_000},
                "weekly_hours": {YEAR: 35},
            },
            "person2": {
                "age": {YEAR: 17},
                "current_education": {YEAR: "UPPER_SECONDARY"},
            },
        },
        "benunits": {
            "benunit": {
                "members": ["person1", "person2"],
                "would_claim_uc": {YEAR: True},
                "would_claim_uc_at_legacy_closure": {YEAR: False},
            }
        },
        "households": {
            "household": {
                "members": ["person1", "person2"],
                "region": {YEAR: "WALES"},
                "tenure_type": {YEAR: "RENT_PRIVATELY"},
                "rent": {YEAR: 10_000},
                "council_tax": {YEAR: 1_500},
            }
        },
    }
    control, recipient = paired_award(situation)
    assert_cash_and_neutrality(
        control, recipient, ("income_tax", "national_insurance", "universal_credit")
    )


def test_new_welsh_cash_keeps_positive_housing_and_council_tax_support():
    situation = {
        "people": {
            "person1": {
                "age": {YEAR: 40},
                "housing_benefit_reported": {YEAR: 1_000},
                "council_tax_benefit_reported": {YEAR: 1_000},
            },
            "person2": {
                "age": {YEAR: 17},
                "current_education": {YEAR: "UPPER_SECONDARY"},
            },
        },
        "benunits": {
            "benunit": {
                "members": ["person1", "person2"],
                "would_claim_uc": {YEAR: False},
                "would_claim_uc_at_legacy_closure": {YEAR: False},
            }
        },
        "households": {
            "household": {
                "members": ["person1", "person2"],
                "region": {YEAR: "WALES"},
                "local_authority": {YEAR: "CARDIFF"},
                "tenure_type": {YEAR: "RENT_FROM_COUNCIL"},
                "rent": {YEAR: 25_000},
                "council_tax": {YEAR: 1_500},
            }
        },
    }
    control, recipient = paired_award(situation)
    assert_cash_and_neutrality(
        control,
        recipient,
        ("housing_benefit", "council_tax_benefit", "benefit_cap_reduction"),
    )


def test_legacy_reported_ema_is_preserved_without_an_explicit_new_assessment():
    # The model cannot tell whether a legacy amount duplicates a supplied new
    # award. Input producers must keep those amounts disjoint; this test makes
    # no invented automatic mapping or subtraction from reported legacy cash.
    sim = Simulation(
        situation={
            "people": {
                "person1": {
                    "age": {YEAR: 17},
                    "adult_ema": {YEAR: 300},
                    "child_ema": {YEAR: 900},
                    "education_grants": {YEAR: 200},
                    "access_fund": {YEAR: 50},
                }
            },
            "benunits": {"benunit": {"members": ["person1"]}},
            "households": {"household": {"members": ["person1"]}},
        }
    )
    assert sim.calculate("adult_ema", YEAR).tolist() == [300]
    assert sim.calculate("child_ema", YEAR).tolist() == [900]
    assert sim.calculate("student_payments", YEAR).tolist() == [1450]
    assert sim.calculate(PAYMENT, YEAR).tolist() == [0]
