"""The claimant-or-partner awards follow what esa_income and jsa_income hold.

claimant_or_partner_esa_income and claimant_or_partner_jsa_income use the
claimant's and partner's reported awards when esa_income or jsa_income holds
what the reported awards give, either after the capital test (the formula)
or as their plain total (the disable_simulated_benefits reform). Otherwise
they take the stored value to be the claimant's or partner's: an award entered
directly, or a reform that replaces or removes it. The rule is decided by
value, so it holds through deletion, clones and branches. Each case has a
claimant with no award of their own and an adult outside the couple who
reports £3,000 of the award. Whenever the stored award is what the reports
give, the claimant-or-partner award must be £0; when it is anything else, it
must be that value.

These mirror #2025's test_entered_directly_lifecycle.py and
test_income_support_direct_inputs.py, which assert the same rule through
income_support_eligible.
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


@pytest.mark.parametrize("award", AWARDS)
def test_an_entered_award_equal_to_the_reports_is_read_through_them(award):
    simulation = family(award)
    # 3,000 is what the other adult's report gives, so the reports decide
    # whose award it is: not the claimant's.
    simulation.set_input(award, YEAR, [3_000])
    assert scoped(simulation, award) == 0


@pytest.mark.parametrize("award", AWARDS)
def test_the_raw_reported_total_is_read_through_the_reports(award):
    """disable_simulated_benefits sets the award to the raw total of every
    member's report. Here the partner reports £200 and an adult outside the
    couple £3,000, with savings of £10,000. Tariff income of
    ceil(4,000 / 250) x £1 x 52 = £832 a year extinguishes the partner's
    award. The raw total, £3,200, differs from the screened award, £2,368,
    but is still what the reports give. As the reform uses reported amounts
    unscreened, the claimant-or-partner award is the partner's raw report,
    £200."""
    reported, _ = AWARDS[award]
    members = ["claimant", "partner", "other_adult"]
    simulation = Simulation(
        situation={
            "people": {
                "claimant": {"age": {YEAR: 40}, "is_claimant_or_partner": {YEAR: True}},
                "partner": {
                    "age": {YEAR: 40},
                    "is_claimant_or_partner": {YEAR: True},
                    reported: {YEAR: 200},
                },
                "other_adult": {
                    "age": {YEAR: 30},
                    "is_claimant_or_partner": {YEAR: False},
                    "current_education": {YEAR: "NOT_IN_EDUCATION"},
                    reported: {YEAR: 3_000},
                },
            },
            "benunits": {"family": {"members": members}},
            "households": {"home": {"members": members, "savings": {YEAR: 10_000}}},
        }
    )
    assert simulation.calculate(award, YEAR)[0] == 2_368
    assert scoped(simulation, award) == 0
    simulation.set_input(award, YEAR, [3_200])
    assert scoped(simulation, award) == 200
    # A different award entered directly is the couple's.
    simulation.set_input(award, YEAR, [4_000])
    assert scoped(simulation, award) == 4_000


@pytest.mark.parametrize("award", AWARDS)
def test_a_neutralised_award_switches_the_claimants_award_off(award):
    reported, _ = AWARDS[award]
    simulation = family(award)
    simulation.set_input(reported, YEAR, [3_000, 0])
    simulation.delete_arrays(award)
    assert scoped(simulation, award) == 3_000
    simulation.tax_benefit_system.neutralize_variable(award)
    simulation.delete_arrays(award)
    assert simulation.calculate(award, YEAR)[0] == 0
    assert scoped(simulation, award) == 0


@pytest.mark.parametrize("award", AWARDS)
def test_a_stored_zero_is_never_the_claimants_award(award):
    """A stored award of zero is no award, even when the reports give a
    fraction of a penny that rounds to it."""
    reported, _ = AWARDS[award]
    simulation = family(award)
    simulation.set_input(reported, YEAR, [0.004, 0])
    simulation.set_input(award, YEAR, [0])
    assert scoped(simulation, award) == 0


@pytest.mark.parametrize("award", AWARDS)
def test_large_reports_are_compared_at_storage_precision(award):
    """Awards are stored as float32. Two reports of £65,536.01 and £65,536.00
    from adults outside the couple give £131,072.01, which float32 rounds;
    the formula's own award must still be recognised as the formula's."""
    reported, _ = AWARDS[award]
    members = ["claimant", "other_adult", "third_adult"]
    simulation = Simulation(
        situation={
            "people": {
                "claimant": {"age": {YEAR: 40}, "is_claimant_or_partner": {YEAR: True}},
                "other_adult": {
                    "age": {YEAR: 30},
                    "is_claimant_or_partner": {YEAR: False},
                    "current_education": {YEAR: "NOT_IN_EDUCATION"},
                    reported: {YEAR: 65_536.01},
                },
                "third_adult": {
                    "age": {YEAR: 31},
                    "is_claimant_or_partner": {YEAR: False},
                    "current_education": {YEAR: "NOT_IN_EDUCATION"},
                    reported: {YEAR: 65_536.00},
                },
            },
            "benunits": {"family": {"members": members}},
            "households": {"home": {"members": members}},
        }
    )
    assert simulation.calculate(award, YEAR)[0] > 131_000
    assert scoped(simulation, award) == 0


@pytest.mark.parametrize("award", AWARDS)
def test_an_entered_scoped_award_states_ownership(award):
    """Entering the claimant-or-partner award itself is the explicit way to
    say whose an award is: another member's report then never changes it."""
    _, variable = AWARDS[award]
    for other_report in [2_000, 3_000]:
        simulation = family(award)
        reported, _ = AWARDS[award]
        simulation.set_input(reported, YEAR, [0, other_report])
        simulation.set_input(award, YEAR, [3_000])
        simulation.set_input(variable, YEAR, [3_000])
        assert simulation.calculate(variable, YEAR)[0] == 3_000


def test_a_removed_esa_award_takes_an_excluded_students_status_with_it():
    """An adult outside the couple who reports income-related ESA is on it
    while the model pays it; once a reform removes esa_income, neither their
    status nor the maintenance loan schedule follows the report alone."""
    members = ["parent", "student"]
    simulation = Simulation(
        situation={
            "people": {
                "parent": {
                    "age": {YEAR: 50},
                    "is_claimant_or_partner": {YEAR: True},
                    "is_parent": {YEAR: False},
                },
                "student": {
                    "age": {YEAR: 19},
                    "is_claimant_or_partner": {YEAR: False},
                    "current_education": {YEAR: "TERTIARY"},
                    "esa_income_reported": {YEAR: 3_000},
                },
            },
            "benunits": {"family": {"members": members}},
            "households": {"home": {"members": members, "country": {YEAR: "ENGLAND"}}},
        }
    )
    assert simulation.calculate("is_on_income_related_esa", YEAR)[1]
    assert simulation.calculate("maintenance_loan_entitled_to_benefits", YEAR)[1]
    simulation.tax_benefit_system.neutralize_variable("esa_income")
    for variable in [
        "esa_income",
        "is_on_income_related_esa",
        "maintenance_loan_entitled_to_benefits",
    ]:
        simulation.delete_arrays(variable)
    assert not simulation.calculate("is_on_income_related_esa", YEAR)[1]
    assert not simulation.calculate("maintenance_loan_entitled_to_benefits", YEAR)[1]
