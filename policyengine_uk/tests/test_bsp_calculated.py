"""Actual-receipt timing and compatibility of additional calculated BSP cash.

GOV.UK and NI Direct give initial amounts of GBP2500/3500 and recurring
amounts of GBP100/350. The tests supply independently qualified receipts;
they do not infer entitlement, retained-capital treatment or a payment calendar.
"""

import copy

import numpy as np
import pytest
from policyengine_core.periods import period

from policyengine_uk import Simulation
from policyengine_uk.utils.scenario import Scenario


pytestmark = pytest.mark.usefixtures("cloned_uk_tax_benefit_system")
YEAR = 2026


def award_facts(year=YEAR):
    return {
        "bsp_add_calculated_award": {year: True},
        "bsp_initial_payment_year": {year: year},
        "bsp_initial_payment_rate": {year: "STANDARD"},
        "bsp_standard_instalments": {year: 3},
        "bsp_higher_instalments": {year: 2},
        "bsp_instalments_received_before_year": {year: 4},
    }


def one_person(person):
    return {
        "people": {"person1": person},
        "benunits": {"benunit": {"members": ["person1"]}},
        "households": {"household": {"members": ["person1"]}},
    }


def test_initial_receipt_is_fixed_and_instalments_need_real_current_year_facts():
    person = {
        "age": {2025: 40, 2026: 41, 2027: 42},
        "bsp_add_calculated_award": {2025: True, 2026: True, 2027: True},
        "bsp_initial_payment_year": {2025: 2025},
        "bsp_initial_payment_rate": {2025: "STANDARD"},
        "bsp_standard_instalments": {2025: 2, 2026: 3},
        "bsp_higher_instalments": {2025: 0, 2026: 0, 2027: 0},
        "bsp_instalments_received_before_year": {2025: 0, 2026: 2, 2027: 5},
        "bsp_reported": {2025: 123.45, 2026: 456.78, 2027: 789.01},
    }
    sim = Simulation(situation=one_person(copy.deepcopy(person)))
    assert sim.calculate("bsp_calculated", 2025).tolist() == [2700]
    assert sim.calculate("bsp_calculated_initial_payment", 2026).tolist() == [0]
    assert sim.calculate("bsp_calculated", 2026).tolist() == [300]
    # Both higher=0 and history=5 are genuine2027 inputs, but standard=3 is
    # only a previous year's stock fact, not another three actual receipts.
    assert sim.calculate("bsp_calculated", 2027).tolist() == [0]
    assert sim.calculate("bsp", 2027)[0] == pytest.approx(789.01, abs=0.01, rel=0)

    missing_history = copy.deepcopy(person)
    missing_history["bsp_standard_instalments"][2027] = 1
    del missing_history["bsp_instalments_received_before_year"][2027]
    unknown = Simulation(situation=one_person(missing_history))
    assert unknown.calculate("bsp_calculated_monthly_payments", 2027).tolist() == [0]

    derived = Simulation(
        situation=one_person(
            {
                "bsp_add_calculated_award": {2027: True},
                "bsp_initial_payment_rate": {2027: "HIGHER"},
            }
        )
    )
    for name, value in (
        ("bsp_initial_payment_year", 2027),
        ("bsp_standard_instalments", 1),
        ("bsp_higher_instalments", 1),
        ("bsp_instalments_received_before_year", 5),
    ):
        derived.get_holder(name).put_in_cache(
            np.array([value]), period(2027), derived.branch_name, derived=True
        )
    # A genuine category alone cannot turn a derived receipt year into cash.
    assert derived.calculate("bsp_calculated", 2027).tolist() == [0]

    actual = copy.deepcopy(person)
    actual["bsp_standard_instalments"][2027] = 1
    actual["bsp_higher_instalments"][2027] = 1
    paid = Simulation(situation=one_person(actual))
    assert paid.calculate("bsp_calculated_initial_payment", 2027).tolist() == [0]
    assert paid.calculate("bsp_calculated_monthly_payments", 2027).tolist() == [450]


def test_full_reported_cells_and_explicit_final_cash_overrides_are_preserved():
    person = {"age": {YEAR: 40}, "bsp_reported": {YEAR: 7123.45}, **award_facts()}
    sim = Simulation(situation=one_person(copy.deepcopy(person)))
    # GBP2500 +3x100 +2x350 is additional to every penny of the mixed report.
    assert sim.calculate("bsp_calculated", YEAR).tolist() == [3500]
    assert sim.calculate("bsp", YEAR)[0] == pytest.approx(10623.45, abs=0.01, rel=0)
    for direct in (0, 9876.54):
        overridden = copy.deepcopy(person)
        overridden["bsp"] = {YEAR: direct}
        cash = Simulation(situation=one_person(overridden))
        assert cash.calculate("bsp", YEAR)[0] == pytest.approx(direct, abs=0.01, rel=0)


def test_standard_instalment_rate_reform_changes_only_its_own_received_components():
    person = {"age": {YEAR: 40}, "bsp_reported": {YEAR: 725.13}, **award_facts()}
    situation = one_person(person)
    baseline = Simulation(situation=copy.deepcopy(situation))
    reformed = Simulation(
        situation=copy.deepcopy(situation),
        scenario=Scenario(
            parameter_changes={"gov.dwp.bsp.standard_monthly_payment": {YEAR: 110}}
        ),
    )
    assert baseline.calculate("bsp_calculated_initial_payment", YEAR).tolist() == [2500]
    assert reformed.calculate("bsp_calculated_initial_payment", YEAR).tolist() == [2500]
    assert baseline.calculate("bsp_calculated_monthly_payments", YEAR).tolist() == [
        1000
    ]
    assert reformed.calculate("bsp_calculated_monthly_payments", YEAR).tolist() == [
        1030
    ]
    assert reformed.calculate("bsp_reported", YEAR)[0] == pytest.approx(
        725.13, abs=0.01, rel=0
    )
    assert reformed.calculate("bsp", YEAR)[0] == pytest.approx(4255.13, abs=0.01, rel=0)


def test_additional_cash_uses_the_existing_bsp_accounting_once_and_keeps_other_awards():
    person = {
        "age": {YEAR: 40},
        "employment_income": {YEAR: 20_000},
        "weekly_hours": {YEAR: 35},
        "bsp_reported": {YEAR: 725.13},
        **award_facts(),
    }
    situation = {
        "people": {"person1": person, "person2": {"age": {YEAR: 8}}},
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
                "region": {YEAR: "SOUTH_EAST"},
                "tenure_type": {YEAR: "RENT_PRIVATELY"},
                "rent": {YEAR: 10_000},
                "council_tax": {YEAR: 1_500},
            }
        },
    }
    no_new_cash = copy.deepcopy(situation)
    no_new_cash["people"]["person1"]["bsp_add_calculated_award"] = {YEAR: False}
    control = Simulation(situation=no_new_cash)
    recipient = Simulation(situation=situation)
    assert control.calculate("income_tax", YEAR).sum() > 0
    assert control.calculate("national_insurance", YEAR).sum() > 0
    assert control.calculate("universal_credit", YEAR).sum() > 0
    for name in (
        "income_tax",
        "national_insurance",
        "universal_credit",
        "housing_benefit",
        "council_tax_benefit",
        "benefit_cap_reduction",
    ):
        np.testing.assert_array_equal(
            recipient.calculate(name, YEAR), control.calculate(name, YEAR), err_msg=name
        )
    for name in (
        "bsp",
        "household_benefits",
        "household_net_income",
        "hbai_household_net_income",
        "gov_spending",
    ):
        change = (
            recipient.calculate(name, YEAR).sum() - control.calculate(name, YEAR).sum()
        )
        assert change == pytest.approx(3500, abs=0.01, rel=0), name
    change = (
        recipient.calculate("gov_balance", YEAR).sum()
        - control.calculate("gov_balance", YEAR).sum()
    )
    assert change == pytest.approx(-3500, abs=0.01, rel=0)
