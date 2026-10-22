"""Ownership of the model's annual legacy-closure proxy (#2395).

These fixtures keep the existing annual dates and eligibility screens. They
do not represent actual migration notices, deadlines, or statutory run-ons.
The separate adult's award is conditional on their own zero-capital,
non-working claim; sharing a benefit unit does not make it the couple's.
"""

import pytest

from policyengine_uk import Simulation


def household(year, claimant=None, partner=None, outside=None, child=False):
    members = {
        "claimant": {"age": 30, "is_claimant_or_partner": True},
        "partner": {"age": 30, "is_claimant_or_partner": True},
        "outside": {
            "age": 40,
            "is_claimant_or_partner": False,
            "current_education": "NOT_IN_EDUCATION",
        },
    }
    for name, changes in (
        ("claimant", claimant),
        ("partner", partner),
        ("outside", outside),
    ):
        members[name].update(changes or {})
    if child:
        members["claimant"]["is_parent"] = True
        members["partner"]["is_parent"] = True
        members["child"] = {"age": 5, "is_claimant_or_partner": False}
    return {
        "people": {
            name: {key: {str(year): value} for key, value in inputs.items()}
            for name, inputs in members.items()
        },
        "benunits": {
            "unit": {
                "members": list(members),
                "esa_income_assessable_capital": {str(year): 0},
                "jsa_income_assessable_capital": {str(year): 0},
            }
        },
        "households": {"household": {"members": list(members)}},
    }


@pytest.mark.parametrize("report", ["income_support_reported", "jsa_income_reported"])
@pytest.mark.parametrize("payee", ["claimant", "partner"])
def test_outside_closed_report_does_not_close_couple_award(report, payee):
    inputs = {payee: {"esa_income_reported": 5_000}}
    sim = Simulation(situation=household(2027, **inputs, outside={report: 1_000}))
    assert not sim.calculate("legacy_benefits_closed", 2027)[0]
    assert sim.calculate("claimant_or_partner_esa_income", 2027)[0] == 5_000
    assert sim.calculate("esa_income", 2027)[0] == 5_000


def test_outside_pension_credit_report_does_not_shield_couple_closure():
    sim = Simulation(
        situation=household(
            2027,
            claimant={"income_support_reported": 1_000, "esa_income_reported": 5_000},
            outside={"age": 70, "pension_credit_reported": 1_000},
        )
    )
    assert sim.calculate("legacy_benefits_closed", 2027)[0]
    assert sim.calculate("claimant_or_partner_esa_income", 2027)[0] == 0


@pytest.mark.parametrize("award", ["esa_income", "jsa_income"])
def test_couple_closure_does_not_end_outside_own_award(award):
    # Tax credits are closed in 2025, while income-based JSA is still active.
    sim = Simulation(
        situation=household(
            2025,
            claimant={"child_tax_credit_reported": 2_000},
            outside={f"{award}_reported": 5_000},
            child=True,
        )
    )
    assert sim.calculate("legacy_benefits_closed", 2025)[0]
    assert sim.calculate(award, 2025)[0] == 5_000
    assert sim.calculate(f"claimant_or_partner_{award}", 2025)[0] == 0
    status = (
        "is_on_income_related_esa"
        if award == "esa_income"
        else "is_on_income_based_jsa"
    )
    assert sim.calculate(status, 2025).tolist() == [False, False, True, False]


def test_outside_own_closed_report_still_ends_only_their_own_claim():
    sim = Simulation(
        situation=household(
            2027,
            claimant={"esa_income_reported": 5_000},
            outside={"esa_income_reported": 5_000, "income_support_reported": 1_000},
        )
    )
    assert not sim.calculate("legacy_benefits_closed", 2027)[0]
    assert sim.calculate("esa_income", 2027)[0] == 5_000
    assert sim.calculate("is_on_income_related_esa", 2027).tolist() == [
        True,
        False,
        False,
    ]


def test_preclosure_report_does_not_end_outside_own_award():
    sim = Simulation(
        situation=household(
            2024,
            claimant={"child_tax_credit_reported": 2_000},
            outside={"esa_income_reported": 5_000},
            child=True,
        )
    )
    assert not sim.calculate("legacy_benefits_closed", 2024)[0]
    assert sim.calculate("esa_income", 2024)[0] == 5_000
    assert sim.calculate("is_on_income_related_esa", 2024).tolist() == [
        False,
        False,
        True,
        False,
    ]


def test_existing_pension_age_exception_is_preserved():
    sim = Simulation(
        situation=household(
            2027,
            claimant={"age": 70, "income_support_reported": 1_000},
            partner={"age": 70},
        )
    )
    assert not sim.calculate("legacy_benefits_closed", 2027)[0]


@pytest.mark.parametrize("award", ["esa_income", "jsa_income"])
@pytest.mark.parametrize(
    "mode", ["formula", "raw_total", "distinct_entered", "nil", "neutralized"]
)
def test_closed_reports_preserve_stored_award_value_contract(award, mode):
    inputs = household(
        2025,
        claimant={"child_tax_credit_reported": 2_000, f"{award}_reported": 5_000},
        outside={f"{award}_reported": 5_000},
        child=True,
    )
    if mode in {"raw_total", "distinct_entered", "nil"}:
        entered = {"raw_total": 10_000, "distinct_entered": 7_000, "nil": 0}[mode]
        inputs["benunits"]["unit"][award] = {"2025": entered}
    sim = Simulation(situation=inputs)
    if mode == "neutralized":
        sim.tax_benefit_system.neutralize_variable(award)
    # Raw report totals retain the held-award path; distinct direct amounts
    # remain the couple's. Formula awards instead omit only closed reports.
    aggregate, scoped = {
        "formula": (5_000, 0),
        "raw_total": (10_000, 5_000),
        "distinct_entered": (7_000, 7_000),
        "nil": (0, 0),
        "neutralized": (0, 0),
    }[mode]
    assert sim.calculate(award, 2025)[0] == aggregate
    assert sim.calculate(f"claimant_or_partner_{award}", 2025)[0] == scoped
    status = (
        "is_on_income_related_esa"
        if award == "esa_income"
        else "is_on_income_based_jsa"
    )
    assert bool(sim.calculate(status, 2025)[2]) == (mode not in {"nil", "neutralized"})


def test_outside_own_pension_credit_age_input_is_used():
    sim = Simulation(
        situation=household(
            2027,
            outside={
                "income_support_reported": 1_000,
                "has_attained_state_pension_credit_qualifying_age": True,
                "is_SP_age": False,
            },
        )
    )
    # An explicit qualifying-age input tests the interface mapping, not a
    # new assertion about the legal timetable or actual migration notices.
    assert not sim.calculate("person_legacy_benefits_closed", 2027)[2]
