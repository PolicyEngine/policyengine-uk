"""A directly entered income-based JSA counts for its own period and branch.

income_support_eligible takes a jsa_income entered directly to be the
claimant's or partner's award (SSCBA 1992 s.124(1)(f)), and otherwise reads
their reported awards after the jsa_income capital screen. Whether jsa_income
was entered is decided by entered_directly, per period and branch, so an
input set after the simulation is built, or on a branch, is respected, and an
input for one year does not apply to another. YAML cases cover inputs given
when the simulation is built (income_support_work_and_jsa.yaml).
"""

from policyengine_uk import Simulation
from policyengine_uk.utils.inputs import entered_directly

YEAR = 2025


def carer_family(benunit_inputs=None, other_adult=None):
    """A carer aged 40 with an Income Support award, and nothing else."""
    people = {
        "carer": {
            "age": {YEAR: 40},
            "is_claimant_or_partner": {YEAR: True},
            "receives_carer_benefit": {YEAR: True},
            "income_support_reported": {YEAR: 1_000},
        }
    }
    if other_adult is not None:
        people["other_adult"] = other_adult
    members = list(people)
    return Simulation(
        situation={
            "people": people,
            "benunits": {
                "family": {
                    "members": members,
                    "income_support_assessable_capital": {YEAR: 0},
                    "jsa_income_assessable_capital": {YEAR: 0},
                    **(benunit_inputs or {}),
                }
            },
            "households": {"home": {"members": members}},
        }
    )


def eligible(simulation, year=YEAR):
    return bool(simulation.calculate("income_support_eligible", year)[0])


def test_carer_family_is_eligible_without_jsa():
    assert eligible(carer_family())


def test_jsa_income_set_after_construction_bars_the_claim():
    simulation = carer_family()
    simulation.set_input("jsa_income", YEAR, [3_000])
    assert simulation.calculate("jsa_income", YEAR)[0] == 3_000
    assert not eligible(simulation)


def test_jsa_income_set_after_the_gate_was_calculated_bars_the_claim():
    simulation = carer_family()
    assert eligible(simulation)
    simulation.set_input("jsa_income", YEAR, [3_000])
    simulation.delete_arrays("income_support_eligible")
    assert not eligible(simulation)


def test_jsa_income_set_on_a_branch_bars_the_claim_on_that_branch_only():
    simulation = carer_family()
    branch = simulation.get_branch("with_jsa", clone_system=False)
    branch.set_input("jsa_income", YEAR, [4_000])
    assert not eligible(branch)
    assert eligible(simulation)


def test_zero_jsa_income_set_after_construction_overrides_reports():
    simulation = carer_family(
        other_adult={
            "age": {YEAR: 40},
            "is_claimant_or_partner": {YEAR: True},
            "jsa_income_reported": {YEAR: 3_000},
        }
    )
    assert not eligible(simulation)
    simulation.set_input("jsa_income", YEAR, [0])
    simulation.delete_arrays("income_support_eligible")
    assert eligible(simulation)


def test_jsa_income_entered_for_another_year_does_not_apply():
    excluded_adult_with_jsa = {
        "age": {YEAR: 30},
        "is_claimant_or_partner": {YEAR: False},
        "jsa_income_reported": {YEAR: 3_000},
    }
    simulation = carer_family(
        benunit_inputs={"jsa_income": {YEAR - 1: 0}},
        other_adult=excluded_adult_with_jsa,
    )
    assert eligible(simulation)
    assert not entered_directly(simulation.benunit, "jsa_income", YEAR)
    assert entered_directly(simulation.benunit, "jsa_income", YEAR - 1)


def test_entered_directly_is_false_for_a_calculated_value():
    simulation = carer_family()
    simulation.calculate("jsa_income", YEAR)
    assert not entered_directly(simulation.benunit, "jsa_income", YEAR)
    assert entered_directly(
        simulation.benunit, "income_support_assessable_capital", YEAR
    )
