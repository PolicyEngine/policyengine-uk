"""Cash integration for the historical tax-credit support payment.

The Direction, Schedule paragraphs 2-3, gives GBP500 per single/joint award.
Finance Act 2021 section 31 exempts that payment from income tax. HMRC's
historical guidance says the payment does not affect benefits. The monetary
oracles below are those GBP500 accounting differences, not computed tax rates.
"""

import copy

import numpy as np
import pytest

from policyengine_uk import Simulation


pytestmark = pytest.mark.usefixtures("cloned_uk_tax_benefit_system")
YEAR = 2021
PAYMENT = "tax_credit_covid_support_payment"
INITIAL = "tax_credit_covid_support_payment_initial_eligible"
EXTENSION = "tax_credit_covid_support_payment_extension_eligible"
PAYMENT_YEAR = "tax_credit_covid_support_payment_year"


def pair(situation):
    """Change only the verified historical qualification, not current awards."""
    without = copy.deepcopy(situation)
    with_payment = copy.deepcopy(situation)
    for source, eligible in ((without, False), (with_payment, True)):
        for family in source["benunits"].values():
            family[INITIAL] = {YEAR: eligible}
            family[EXTENSION] = {YEAR: False}
            family[PAYMENT_YEAR] = {YEAR: YEAR}
    return Simulation(situation=without), Simulation(situation=with_payment)


def assert_cash_accounting(control, recipient, claim_count):
    # One GBP500 transfer per claim: it raises cash and spending, and lowers
    # government balance by the same amount. No unrelated baseline is a golden.
    np.testing.assert_array_equal(control.calculate(PAYMENT, YEAR), [0] * claim_count)
    np.testing.assert_array_equal(
        recipient.calculate(PAYMENT, YEAR), [500] * claim_count
    )
    for name in (
        "household_benefits",
        "household_net_income",
        "hbai_benefits",
        "hbai_household_net_income",
        "gov_spending",
    ):
        change = (
            np.asarray(recipient.calculate(name, YEAR)).sum()
            - np.asarray(control.calculate(name, YEAR)).sum()
        )
        assert change == pytest.approx(500 * claim_count, abs=0.01, rel=0)
    balance_change = (
        np.asarray(recipient.calculate("gov_balance", YEAR)).sum()
        - np.asarray(control.calculate("gov_balance", YEAR)).sum()
    )
    assert balance_change == pytest.approx(-500 * claim_count, abs=0.01, rel=0)


def assert_unchanged(control, recipient, names):
    for name in names:
        np.testing.assert_array_equal(
            recipient.calculate(name, YEAR), control.calculate(name, YEAR), err_msg=name
        )


def test_payment_keeps_positive_tax_ni_and_uc_and_adds_cash_once():
    situation = {
        "people": {
            "person1": {
                "age": {YEAR: 35},
                "employment_income": {YEAR: 20_000},
                "weekly_hours": {YEAR: 35},
            },
            "person2": {"age": {YEAR: 8}},
        },
        "benunits": {
            "benunit": {
                "members": ["person1", "person2"],
                "would_claim_uc": {YEAR: True},
                "would_claim_uc_at_legacy_closure": {YEAR: False},
                "working_tax_credit": {YEAR: 0},
                "child_tax_credit": {YEAR: 0},
            }
        },
        "households": {
            "household": {
                "members": ["person1", "person2"],
                "region": {YEAR: "SOUTH_EAST"},
                "tenure_type": {YEAR: "RENT_PRIVATELY"},
                "rent": {YEAR: 10_000},
                "council_tax": {YEAR: 1_500},
            }
        },
    }
    control, recipient = pair(situation)

    assert control.calculate("income_tax", YEAR).sum() > 0
    assert control.calculate("national_insurance", YEAR).sum() > 0
    assert control.calculate("universal_credit", YEAR).sum() > 0
    assert_unchanged(
        control,
        recipient,
        (
            "income_tax",
            "national_insurance",
            "universal_credit",
            "working_tax_credit",
            "child_tax_credit",
        ),
    )
    assert_cash_accounting(control, recipient, 1)


def test_joint_claim_keeps_positive_hb_ctr_and_cap_reduction():
    # Three pre-2017 children, no earnings, social rent and a continuing HB
    # claim give a positive capped award. The new payment must neither enter
    # the capped-benefit total nor grant the ordinary WTC cap exemption.
    people = {
        "person1": {
            "age": {YEAR: 35},
            "housing_benefit_reported": {YEAR: 1_000},
            "council_tax_benefit_reported": {YEAR: 1_000},
        },
        "person2": {"age": {YEAR: 35}},
        "person3": {"age": {YEAR: 12}},
        "person4": {"age": {YEAR: 10}},
        "person5": {"age": {YEAR: 8}},
    }
    situation = {
        "people": people,
        "benunits": {
            "benunit": {
                "members": list(people),
                "would_claim_uc": {YEAR: False},
                "would_claim_uc_at_legacy_closure": {YEAR: False},
                "working_tax_credit": {YEAR: 0},
                "child_tax_credit": {YEAR: 10_000},
            }
        },
        "households": {
            "household": {
                "members": list(people),
                "region": {YEAR: "SOUTH_EAST"},
                "local_authority": {YEAR: "MAIDSTONE"},
                "tenure_type": {YEAR: "RENT_FROM_COUNCIL"},
                "rent": {YEAR: 20_000},
                "council_tax": {YEAR: 1_500},
            }
        },
    }
    control, recipient = pair(situation)

    assert control.calculate("housing_benefit", YEAR).sum() > 0
    assert control.calculate("council_tax_benefit", YEAR).sum() > 0
    assert control.calculate("benefit_cap_reduction", YEAR).sum() > 0
    assert_unchanged(
        control,
        recipient,
        (
            "income_tax",
            "national_insurance",
            "housing_benefit",
            "council_tax_benefit",
            "benefit_cap_reduction",
            "working_tax_credit",
            "child_tax_credit",
        ),
    )
    assert_cash_accounting(control, recipient, 1)


def test_two_independent_claims_in_one_home_add_two_payments():
    situation = {
        "people": {
            "person1": {"age": {YEAR: 35}, "employment_income": {YEAR: 40_000}},
            "person2": {"age": {YEAR: 45}, "employment_income": {YEAR: 40_000}},
        },
        "benunits": {
            "benunit1": {"members": ["person1"]},
            "benunit2": {"members": ["person2"]},
        },
        "households": {
            "household": {
                "members": ["person1", "person2"],
                "tenure_type": {YEAR: "OWNED_OUTRIGHT"},
                "council_tax": {YEAR: 1_500},
            }
        },
    }
    control, recipient = pair(situation)

    assert_unchanged(control, recipient, ("income_tax", "national_insurance"))
    assert_cash_accounting(control, recipient, 2)
