"""The claimant-or-partner awards follow direct inputs through their lifecycle.

claimant_or_partner_esa_income and claimant_or_partner_jsa_income take an
esa_income or jsa_income entered directly to be the claimant's or partner's
award, and otherwise use the claimant's and partner's reported awards.
entered_directly decides which, from core's record of explicit inputs, which
the UK Simulation keeps in step with storage through deletion, clones and
branches. Each case has a claimant with no award of their own and an adult
outside the couple who reports £3,000 of the award. Whenever the stored award
is a formula result, the claimant-or-partner award must be £0; when it is an
input, it must be the input.

These mirror test_entered_directly_lifecycle.py on #2025, which asserts the
same lifecycle through income_support_eligible.
"""

import pytest

from policyengine_uk import Simulation

YEAR = 2025

AWARDS = {
    "esa_income": ("esa_income_reported", "claimant_or_partner_esa_income"),
    "jsa_income": ("jsa_income_reported", "claimant_or_partner_jsa_income"),
}


def family(award):
    reported, _ = AWARDS[award]
    members = ["claimant", "other_adult"]
    return Simulation(
        situation={
            "people": {
                "claimant": {
                    "age": {YEAR: 40},
                    "is_claimant_or_partner": {YEAR: True},
                },
                "other_adult": {
                    "age": {YEAR: 30},
                    "is_claimant_or_partner": {YEAR: False},
                    "current_education": {YEAR: "NOT_IN_EDUCATION"},
                    reported: {YEAR: 3_000},
                },
            },
            "benunits": {"family": {"members": members}},
            "households": {"home": {"members": members}},
        }
    )


def scoped(simulation, award):
    _, variable = AWARDS[award]
    simulation.delete_arrays(variable)
    return float(simulation.calculate(variable, YEAR)[0])


@pytest.mark.parametrize("award", AWARDS)
def test_another_members_report_is_never_the_claimants_award(award):
    simulation = family(award)
    assert simulation.calculate(award, YEAR)[0] == 3_000
    assert scoped(simulation, award) == 0


@pytest.mark.parametrize("award", AWARDS)
def test_a_deleted_input_does_not_make_a_later_formula_result_direct(award):
    simulation = family(award)
    simulation.set_input(award, YEAR, [1_000])
    assert scoped(simulation, award) == 1_000
    simulation.delete_arrays(award)
    assert simulation.calculate(award, YEAR)[0] == 3_000
    assert scoped(simulation, award) == 0


@pytest.mark.parametrize("award", AWARDS)
def test_an_input_on_a_clone_does_not_reach_the_original(award):
    simulation = family(award)
    assert simulation.calculate(award, YEAR)[0] == 3_000
    clone = simulation.clone()
    clone.set_input(award, YEAR, [1_000])
    assert scoped(clone, award) == 1_000
    assert scoped(simulation, award) == 0


@pytest.mark.parametrize("award", AWARDS)
def test_a_parent_input_does_not_reach_an_earlier_branch(award):
    simulation = family(award)
    assert simulation.calculate(award, YEAR)[0] == 3_000
    branch = simulation.get_branch("before", clone_system=False)
    simulation.set_input(award, YEAR, [1_000])
    assert scoped(simulation, award) == 1_000
    # The branch still stores the formula result it copied.
    assert scoped(branch, award) == 0


@pytest.mark.parametrize("award", AWARDS)
def test_a_branch_made_after_a_parent_input_inherits_it(award):
    simulation = family(award)
    simulation.set_input(award, YEAR, [1_000])
    branch = simulation.get_branch("after", clone_system=False)
    assert scoped(branch, award) == 1_000


@pytest.mark.parametrize("award", AWARDS)
def test_nested_branches_read_the_nearest_stored_input(award):
    simulation = family(award)
    outer = simulation.get_branch("outer", clone_system=False)
    outer.set_input(award, YEAR, [1_000])
    inner = outer.get_branch("inner", clone_system=False)
    assert scoped(inner, award) == 1_000
    inner.set_input(award, YEAR, [500])
    assert scoped(inner, award) == 500
    assert scoped(outer, award) == 1_000
    assert scoped(simulation, award) == 0
