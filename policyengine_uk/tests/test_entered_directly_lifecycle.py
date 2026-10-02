"""A direct award stays tied to the stored value it was entered as.

income_support_eligible takes an income-related ESA or income-based JSA
entered directly (esa_income, jsa_income) to be the claimant's or partner's
award, and otherwise reads only their reported awards (SSCBA 1992
s.124(1)(f), (h)). entered_directly decides which, from core's record of
explicit inputs. These cases follow that record through deletion, clones and
branches, with an adult outside the couple who reports £3,000 of the award:
whenever the stored award is a formula result, that adult's report must not
bar the claim.
"""

import pytest

from policyengine_uk import Simulation
from policyengine_uk.utils.inputs import entered_directly

YEAR = 2025

AWARDS = {
    "jsa_income": ("jsa_income_reported", "jsa_income_assessable_capital"),
    "esa_income": ("esa_income_reported", "esa_income_assessable_capital"),
}


def family(award):
    """A caring award holder and an excluded adult who reports the award."""
    reported, capital = AWARDS[award]
    members = ["carer", "other_adult"]
    return Simulation(
        situation={
            "people": {
                "carer": {
                    "age": {YEAR: 40},
                    "is_claimant_or_partner": {YEAR: True},
                    "receives_carer_benefit": {YEAR: True},
                    "income_support_reported": {YEAR: 1_000},
                },
                "other_adult": {
                    "age": {YEAR: 30},
                    "is_claimant_or_partner": {YEAR: False},
                    reported: {YEAR: 3_000},
                },
            },
            "benunits": {
                "family": {
                    "members": members,
                    "income_support_assessable_capital": {YEAR: 0},
                    capital: {YEAR: 0},
                }
            },
            "households": {"home": {"members": members}},
        }
    )


def eligible(simulation):
    simulation.delete_arrays("income_support_eligible")
    return bool(simulation.calculate("income_support_eligible", YEAR)[0])


def direct(simulation, award):
    return entered_directly(simulation.benunit, award, YEAR)


@pytest.mark.parametrize("award", AWARDS)
def test_the_excluded_adults_report_never_bars_the_claim(award):
    simulation = family(award)
    # The award's own formula counts the excluded adult's report ...
    assert simulation.calculate(award, YEAR)[0] == 3_000
    # ... but the gate reads only the claimant's and partner's.
    assert not direct(simulation, award)
    assert eligible(simulation)


@pytest.mark.parametrize("award", AWARDS)
def test_a_deleted_input_does_not_make_a_later_formula_result_direct(award):
    simulation = family(award)
    simulation.set_input(award, YEAR, [0])
    assert direct(simulation, award) and eligible(simulation)
    simulation.delete_arrays(award)
    assert not direct(simulation, award)
    assert simulation.calculate(award, YEAR)[0] == 3_000
    assert not direct(simulation, award)
    assert eligible(simulation)


@pytest.mark.parametrize("award", AWARDS)
def test_a_deleted_input_then_the_gate_reads_reports(award):
    simulation = family(award)
    simulation.set_input(award, YEAR, [3_000])
    assert not eligible(simulation)
    simulation.delete_arrays(award)
    assert eligible(simulation)


@pytest.mark.parametrize("award", AWARDS)
def test_an_input_on_a_clone_does_not_reach_the_original(award):
    simulation = family(award)
    assert simulation.calculate(award, YEAR)[0] == 3_000
    clone = simulation.clone()
    clone.set_input(award, YEAR, [0])
    assert clone._user_input_keys is not simulation._user_input_keys
    assert direct(clone, award)
    assert not direct(simulation, award)
    assert eligible(simulation)


@pytest.mark.parametrize("award", AWARDS)
def test_a_parent_input_does_not_reach_an_earlier_branch(award):
    simulation = family(award)
    assert simulation.calculate(award, YEAR)[0] == 3_000
    branch = simulation.get_branch("before", clone_system=False)
    simulation.set_input(award, YEAR, [3_000])
    # The parent's input is its own; the branch still stores the formula
    # result it copied, which counts the excluded adult.
    assert direct(simulation, award) and not eligible(simulation)
    assert not direct(branch, award)
    assert eligible(branch)


@pytest.mark.parametrize("award", AWARDS)
def test_a_branch_made_after_a_parent_input_inherits_it(award):
    simulation = family(award)
    simulation.set_input(award, YEAR, [3_000])
    branch = simulation.get_branch("after", clone_system=False)
    assert direct(branch, award)
    assert not eligible(branch)


@pytest.mark.parametrize("award", AWARDS)
def test_nested_branches_read_the_nearest_stored_input(award):
    simulation = family(award)
    outer = simulation.get_branch("outer", clone_system=False)
    outer.set_input(award, YEAR, [3_000])
    inner = outer.get_branch("inner", clone_system=False)
    assert direct(inner, award) and not eligible(inner)
    inner.set_input(award, YEAR, [0])
    assert direct(inner, award) and eligible(inner)
    assert not eligible(outer)
    assert not direct(simulation, award) and eligible(simulation)


@pytest.mark.parametrize("award", AWARDS)
def test_a_period_given_as_a_string_is_the_same_year(award):
    simulation = family(award)
    simulation.set_input(award, YEAR, [0])
    assert entered_directly(simulation.benunit, award, str(YEAR))
    assert not entered_directly(simulation.benunit, award, str(YEAR + 1))
