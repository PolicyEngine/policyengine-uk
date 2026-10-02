"""The award the gate reads follows the stored value through any lifecycle.

income_support_eligible reads income-related ESA and income-based JSA from
the claimant's and partner's reported awards (SSCBA 1992 s.124(1)(f), (h)),
through claimant_or_partner_esa_income and claimant_or_partner_jsa_income,
unless esa_income or jsa_income holds a different award from the one all
the reported amounts give, which is then taken to be the couple's. The rule
depends only on the value the simulation reads, so it holds through
deletion, clones and branches. Each family has an adult outside the couple
who reports £3,000 of the award: whenever the stored award is what the
reports give, that adult's report must not bar the claim.
"""

import pytest

from policyengine_uk import Simulation

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
    # The gate reads the claimant-or-partner awards, which are calculated and
    # cached like any other variable. Recalculate them too after changing an
    # input they depend on.
    for variable in (
        "income_support_eligible",
        "claimant_or_partner_esa_income",
        "claimant_or_partner_jsa_income",
    ):
        simulation.delete_arrays(variable)
    return bool(simulation.calculate("income_support_eligible", YEAR)[0])


@pytest.mark.parametrize("award", AWARDS)
def test_the_excluded_adults_report_never_bars_the_claim(award):
    simulation = family(award)
    # The award's own formula counts the excluded adult's report ...
    assert simulation.calculate(award, YEAR)[0] == 3_000
    # ... but the gate reads only the claimant's and partner's.
    assert eligible(simulation)


@pytest.mark.parametrize("award", AWARDS)
def test_an_entered_award_equal_to_the_reports_is_read_through_them(award):
    # Intended: an award that is exactly what the reports give is read
    # through the reports, which say it is the excluded adult's.
    simulation = family(award)
    simulation.set_input(award, YEAR, [3_000])
    assert eligible(simulation)


@pytest.mark.parametrize("award", AWARDS)
def test_a_deleted_input_then_a_formula_result_reads_reports(award):
    simulation = family(award)
    simulation.set_input(award, YEAR, [0])
    assert eligible(simulation)
    simulation.set_input(award, YEAR, [4_000])
    assert not eligible(simulation)
    simulation.delete_arrays(award)
    assert simulation.calculate(award, YEAR)[0] == 3_000
    assert eligible(simulation)


@pytest.mark.parametrize("award", AWARDS)
def test_a_deleted_input_then_the_gate_reads_reports(award):
    simulation = family(award)
    simulation.set_input(award, YEAR, [4_000])
    assert not eligible(simulation)
    simulation.delete_arrays(award)
    assert eligible(simulation)


@pytest.mark.parametrize("award", AWARDS)
def test_an_input_on_a_clone_does_not_reach_the_original(award):
    simulation = family(award)
    assert simulation.calculate(award, YEAR)[0] == 3_000
    clone = simulation.clone()
    clone.set_input(award, YEAR, [4_000])
    assert not eligible(clone)
    assert eligible(simulation)


@pytest.mark.parametrize("award", AWARDS)
def test_a_parent_input_does_not_reach_an_earlier_branch(award):
    simulation = family(award)
    assert simulation.calculate(award, YEAR)[0] == 3_000
    branch = simulation.get_branch("before", clone_system=False)
    simulation.set_input(award, YEAR, [4_000])
    assert not eligible(simulation)
    # The branch still stores the formula result it copied.
    assert eligible(branch)


@pytest.mark.parametrize("award", AWARDS)
def test_a_branch_made_after_a_parent_input_inherits_it(award):
    simulation = family(award)
    simulation.set_input(award, YEAR, [4_000])
    branch = simulation.get_branch("after", clone_system=False)
    assert not eligible(branch)


@pytest.mark.parametrize("award", AWARDS)
def test_nested_branches_read_the_nearest_stored_award(award):
    simulation = family(award)
    outer = simulation.get_branch("outer", clone_system=False)
    outer.set_input(award, YEAR, [4_000])
    inner = outer.get_branch("inner", clone_system=False)
    assert not eligible(inner)
    inner.set_input(award, YEAR, [0])
    assert eligible(inner)
    assert not eligible(outer)
    assert eligible(simulation)
