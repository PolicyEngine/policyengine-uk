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
