"""Income-related ESA that is not the award on the reported amounts.

income_support_eligible reads the claimant's and partner's reported
income-related ESA, after the esa_income capital test. When esa_income holds
anything else (an award entered directly, or a reform that replaces or
removes it), the reported amounts do not say whose award it is, so the gate
takes esa_income itself to be the claimant's or partner's. The test is on the
value the simulation reads, so it holds however that value got there: set
before or after the simulation is built, on a clone or a branch, for this year
or another, deleted and recalculated.

In each case below an adult outside the couple reports £3,000 of
income-related ESA, so the award on the reported amounts is £3,000. That
report alone must never bar the claim. Entered awards use £4,000, which no
reported amount here produces.
"""

import numpy as np

from policyengine_uk import Simulation
from policyengine_uk.utils.scenario import Scenario

YEAR = 2025
CARER = {
    "age": {YEAR: 40},
    "is_claimant_or_partner": {YEAR: True},
    "receives_carer_benefit": {YEAR: True},
    "income_support_reported": {YEAR: 1_000},
}
EXCLUDED_ADULT = {
    "age": {YEAR: 30},
    "is_claimant_or_partner": {YEAR: False},
    "current_education": {YEAR: "NOT_IN_EDUCATION"},
    "esa_income_reported": {YEAR: 3_000},
}
ENTERED = 4_000


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


def family(benunit=None):
    return simulation({"carer": CARER, "other_adult": EXCLUDED_ADULT}, benunit)


def eligible(sim):
    sim.delete_arrays("income_support_eligible")
    return bool(sim.calculate("income_support_eligible", YEAR)[0])


def test_the_excluded_adults_report_never_bars_the_claim():
    sim = family()
    assert sim.calculate("esa_income", YEAR)[0] == 3_000
    assert eligible(sim)


def test_an_award_entered_in_the_situation_bars_the_claim():
    assert not eligible(family({"esa_income": {YEAR: ENTERED}}))


def test_an_award_set_after_construction_bars_the_claim():
    sim = family()
    assert eligible(sim)
    sim.set_input("esa_income", YEAR, np.array([ENTERED]))
    assert not eligible(sim)


def test_an_award_set_on_a_branch_bars_the_claim_there_only():
    sim = family()
    branch = sim.get_branch("with_esa", clone_system=False)
    branch.set_input("esa_income", YEAR, np.array([ENTERED]))
    assert not eligible(branch)
    assert eligible(sim)


def test_an_award_entered_for_another_year_does_not_count_this_year():
    sim = family({"esa_income": {YEAR - 1: 0}})
    assert sim.calculate("esa_income", YEAR)[0] == 3_000
    assert eligible(sim)


def test_a_deleted_award_is_recalculated_from_the_reports():
    sim = family()
    sim.set_input("esa_income", YEAR, np.array([ENTERED]))
    assert not eligible(sim)
    sim.delete_arrays("esa_income")
    assert sim.calculate("esa_income", YEAR)[0] == 3_000
    assert eligible(sim)


def test_an_award_set_on_a_clone_does_not_reach_the_original():
    sim = family()
    assert sim.calculate("esa_income", YEAR)[0] == 3_000
    clone = sim.clone()
    clone.set_input("esa_income", YEAR, np.array([ENTERED]))
    assert not eligible(clone)
    assert eligible(sim)


def test_nested_branches_read_the_value_they_see():
    sim = family()
    outer = sim.get_branch("outer", clone_system=False)
    outer.set_input("esa_income", YEAR, np.array([ENTERED]))
    inner = outer.get_branch("inner", clone_system=False)
    assert not eligible(inner)
    inner.set_input("esa_income", YEAR, np.array([0.0]))
    assert eligible(inner)
    assert not eligible(outer)
    assert eligible(sim)


def test_a_zero_award_overrides_the_claimants_reported_esa():
    carer_with_esa = {**CARER, "esa_income_reported": {YEAR: 2_000}}
    assert not eligible(simulation({"carer": carer_with_esa}))
    assert eligible(simulation({"carer": carer_with_esa}, {"esa_income": {YEAR: 0}}))


def test_abolishing_income_related_esa_removes_the_bar():
    # A reform that neutralises esa_income pays no income-related ESA, so
    # the claimant's reported award no longer bars Income Support.
    sim = simulation({"carer": {**CARER, "esa_income_reported": {YEAR: 2_000}}})
    assert not eligible(sim)
    sim.tax_benefit_system.neutralize_variable("esa_income")
    sim.delete_arrays("esa_income")
    assert sim.calculate("esa_income", YEAR)[0] == 0
    assert eligible(sim)


def test_the_plain_reported_total_is_read_through_the_reports():
    # disable_simulated_benefits sets esa_income to the plain total of the
    # reported awards, before the capital test. With £10,000 of capital the
    # tariff income (£832 a year) extinguishes the partner's own £200, so the
    # claimant and partner have no income-related ESA; the £3,000 is the
    # excluded adult's.
    partner = {
        "age": {YEAR: 42},
        "is_claimant_or_partner": {YEAR: True},
        "esa_income_reported": {YEAR: 200},
    }
    sim = simulation(
        {"carer": CARER, "partner": partner, "other_adult": EXCLUDED_ADULT},
        {"esa_income_assessable_capital": {YEAR: 10_000}},
    )
    sim.set_input("esa_income", YEAR, np.array([3_200.0]))
    assert eligible(sim)


def test_an_award_equal_to_the_reported_amounts_is_read_through_them():
    # Intended: an entered award of exactly the £3,000 the reports give is
    # read as the excluded adult's award, so it does not bar the claim.
    assert eligible(family({"esa_income": {YEAR: 3_000}}))


def test_a_simulation_with_no_inputs_calculates_the_gate():
    sim = Simulation(
        situation={},
        scenario=Scenario(
            applied_before_data_load=True,
            parameter_changes={"gov.dwp.universal_credit.rebalancing.active": False},
        ),
    )
    assert sim.calculate("income_support_eligible", YEAR).shape == (1,)
