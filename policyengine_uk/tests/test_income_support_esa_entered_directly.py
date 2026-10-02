"""An income-related ESA award entered directly bars Income Support only for
the period it was entered for.

income_support_eligible takes an esa_income entered directly (an input, not
the formula) to be the claimant's or partner's award, because the reported
amounts do not say whose it is. Otherwise it uses the award on the claimant's
and partner's reported amounts. "Entered directly" has to follow the input:

- set with set_input after the simulation is built;
- set on a branch;
- for this year only, not for another year.
"""

import numpy as np

from policyengine_uk import Simulation
from policyengine_uk.utils.inputs import entered_directly

YEAR = 2025
CARER = {
    "age": {YEAR: 40},
    "is_claimant_or_partner": {YEAR: True},
    "receives_carer_benefit": {YEAR: True},
    "income_support_reported": {YEAR: 1_000},
}


def simulation(people, benunit=None):
    names = list(people)
    return Simulation(
        situation={
            "people": people,
            "benunits": {
                "b": {
                    "members": names,
                    "income_support_assessable_capital": {YEAR: 0},
                    "esa_income_assessable_capital": {YEAR: 0},
                    **(benunit or {}),
                }
            },
            "households": {"h": {"members": names}},
        }
    )


def test_award_set_after_construction_bars_income_support():
    sim = simulation({"carer": CARER})
    assert sim.calculate("income_support_eligible", YEAR)[0]
    sim.set_input("esa_income", YEAR, np.array([3_000.0]))
    sim.delete_arrays("income_support_eligible")
    assert sim.calculate("esa_income", YEAR)[0] == 3_000
    assert not sim.calculate("income_support_eligible", YEAR)[0]


def test_award_set_on_a_branch_bars_income_support_there():
    sim = simulation({"carer": CARER})
    branch = sim.get_branch("with_esa", clone_system=False)
    branch.set_input("esa_income", YEAR, np.array([3_000.0]))
    assert not branch.calculate("income_support_eligible", YEAR)[0]
    assert sim.calculate("income_support_eligible", YEAR)[0]


def test_award_entered_for_another_year_does_not_count_this_year():
    # An excluded adult reports ESA in 2025; esa_income is entered only for
    # 2024. In 2025 esa_income comes from the formula, so the gate reads the
    # claimant's and partner's reports, and the excluded adult's award does
    # not bar the claim.
    excluded_adult = {
        "age": {YEAR: 30},
        "is_claimant_or_partner": {YEAR: False},
        "current_education": {YEAR: "NOT_IN_EDUCATION"},
        "esa_income_reported": {YEAR: 3_000},
    }
    sim = simulation(
        {"carer": CARER, "other_adult": excluded_adult},
        {"esa_income": {YEAR - 1: 0}},
    )
    assert sim.calculate("esa_income", YEAR)[0] == 3_000
    assert sim.calculate("income_support_eligible", YEAR)[0]


# The record of direct inputs follows the stored value through deletion,
# clones and branches (the ESA cases of #2025's
# test_entered_directly_lifecycle.py, which also covers jsa_income). In each,
# an adult outside the couple reports £3,000 of income-related ESA, so the
# formula's esa_income is £3,000; that report alone must never bar the claim.

EXCLUDED_ADULT = {
    "age": {YEAR: 30},
    "is_claimant_or_partner": {YEAR: False},
    "current_education": {YEAR: "NOT_IN_EDUCATION"},
    "esa_income_reported": {YEAR: 3_000},
}


def family():
    return simulation({"carer": CARER, "other_adult": EXCLUDED_ADULT})


def eligible(sim):
    sim.delete_arrays("income_support_eligible")
    return bool(sim.calculate("income_support_eligible", YEAR)[0])


def direct(sim, period=YEAR):
    return entered_directly(sim.benunit, "esa_income", period)


def test_the_excluded_adults_report_never_bars_the_claim():
    sim = family()
    assert sim.calculate("esa_income", YEAR)[0] == 3_000
    assert not direct(sim)
    assert eligible(sim)


def test_a_deleted_input_does_not_make_a_later_formula_result_direct():
    sim = family()
    sim.set_input("esa_income", YEAR, [0])
    assert direct(sim) and eligible(sim)
    sim.delete_arrays("esa_income")
    assert not direct(sim)
    assert sim.calculate("esa_income", YEAR)[0] == 3_000
    assert not direct(sim)
    assert eligible(sim)


def test_a_deleted_input_then_the_gate_reads_reports():
    sim = family()
    sim.set_input("esa_income", YEAR, [3_000])
    assert not eligible(sim)
    sim.delete_arrays("esa_income")
    assert eligible(sim)


def test_an_input_on_a_clone_does_not_reach_the_original():
    sim = family()
    assert sim.calculate("esa_income", YEAR)[0] == 3_000
    clone = sim.clone()
    clone.set_input("esa_income", YEAR, [0])
    assert direct(clone)
    assert not direct(sim)
    assert eligible(sim)


def test_a_parent_input_does_not_reach_an_earlier_branch():
    sim = family()
    assert sim.calculate("esa_income", YEAR)[0] == 3_000
    branch = sim.get_branch("before", clone_system=False)
    sim.set_input("esa_income", YEAR, [3_000])
    assert direct(sim) and not eligible(sim)
    assert not direct(branch)
    assert eligible(branch)


def test_a_branch_made_after_a_parent_input_inherits_it():
    sim = family()
    sim.set_input("esa_income", YEAR, [3_000])
    branch = sim.get_branch("after", clone_system=False)
    assert direct(branch)
    assert not eligible(branch)


def test_nested_branches_read_the_nearest_stored_input():
    sim = family()
    outer = sim.get_branch("outer", clone_system=False)
    outer.set_input("esa_income", YEAR, [3_000])
    inner = outer.get_branch("inner", clone_system=False)
    assert direct(inner) and not eligible(inner)
    inner.set_input("esa_income", YEAR, [0])
    assert direct(inner) and eligible(inner)
    assert not eligible(outer)
    assert not direct(sim) and eligible(sim)


def test_a_period_given_as_a_string_is_the_same_year():
    sim = family()
    sim.set_input("esa_income", YEAR, [0])
    assert direct(sim, str(YEAR))
    assert not direct(sim, str(YEAR + 1))
