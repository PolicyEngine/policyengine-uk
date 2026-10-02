"""A jsa_income that differs from the reported award is the couple's award.

income_support_eligible reads income-based JSA (SSCBA 1992 s.124(1)(f)) from
the claimant's and partner's reported awards after the jsa_income capital
screen. Where jsa_income holds a different award from the one all the
reported amounts give, that award is used instead and taken to be the
claimant's or partner's. That covers an award entered directly (when the
simulation is built or later, or on a branch) and a reform that changes or
removes jsa_income. An award entered for one year says nothing about another.
YAML cases cover inputs given when the simulation is built
(income_support_work_and_jsa.yaml).
"""

from policyengine_uk import Simulation

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


PARTNER_WITH_JSA = {
    "age": {YEAR: 40},
    "is_claimant_or_partner": {YEAR: True},
    "jsa_income_reported": {YEAR: 3_000},
}


def eligible(simulation, year=YEAR):
    simulation.delete_arrays("income_support_eligible")
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
    assert not eligible(simulation)


def test_jsa_income_set_on_a_branch_bars_the_claim_on_that_branch_only():
    simulation = carer_family()
    branch = simulation.get_branch("with_jsa", clone_system=False)
    branch.set_input("jsa_income", YEAR, [4_000])
    assert not eligible(branch)
    assert eligible(simulation)


def test_zero_jsa_income_set_after_construction_overrides_reports():
    simulation = carer_family(other_adult=PARTNER_WITH_JSA)
    assert not eligible(simulation)
    simulation.set_input("jsa_income", YEAR, [0])
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


def test_a_reform_that_removes_income_based_jsa_lifts_the_bar():
    # A reform that neutralises jsa_income pays no income-based JSA, so the
    # partner's reported award no longer bars Income Support.
    simulation = carer_family(other_adult=PARTNER_WITH_JSA)
    assert not eligible(simulation)
    simulation.tax_benefit_system.neutralize_variable("jsa_income")
    simulation.delete_arrays("jsa_income")
    assert simulation.calculate("jsa_income", YEAR)[0] == 0
    assert eligible(simulation)


def test_the_raw_reported_total_is_read_through_the_reports():
    """disable_simulated_benefits sets jsa_income to the raw total of every
    member's report. Here the partner reports £200 and an adult outside the
    couple £3,000, with capital of £10,000. Tariff income of
    ceil(4,000 / 250) x £1 x 52 = £832 a year extinguishes the partner's
    award, so the claimant and partner have no income-based JSA. The raw
    total, £3,200, differs from the screened award, £3,200 - £832 = £2,368,
    but is still what the reports give, so the reports decide whose it is."""
    members = ["carer", "partner", "other_adult"]
    simulation = Simulation(
        situation={
            "people": {
                "carer": {
                    "age": {YEAR: 40},
                    "is_claimant_or_partner": {YEAR: True},
                    "receives_carer_benefit": {YEAR: True},
                    "income_support_reported": {YEAR: 1_000},
                },
                "partner": {
                    "age": {YEAR: 40},
                    "is_claimant_or_partner": {YEAR: True},
                    "jsa_income_reported": {YEAR: 200},
                },
                "other_adult": {
                    "age": {YEAR: 30},
                    "is_claimant_or_partner": {YEAR: False},
                    "jsa_income_reported": {YEAR: 3_000},
                },
            },
            "benunits": {
                "family": {
                    "members": members,
                    "income_support_assessable_capital": {YEAR: 10_000},
                    "jsa_income_assessable_capital": {YEAR: 10_000},
                }
            },
            "households": {"home": {"members": members}},
        }
    )
    assert simulation.calculate("jsa_income", YEAR)[0] == 2_368
    assert eligible(simulation)
    simulation.set_input("jsa_income", YEAR, [3_200])
    assert eligible(simulation)
    # A different award entered directly is the couple's.
    simulation.set_input("jsa_income", YEAR, [4_000])
    assert not eligible(simulation)
