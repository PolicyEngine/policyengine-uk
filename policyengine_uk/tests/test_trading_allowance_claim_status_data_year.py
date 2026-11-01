"""The trading allowance claim status reads the allowance of the year the
input data were measured (PolicyEngine/policyengine-uk#2764).

A claimant's profit already deducts the allowance legislated for that year:
a dataset's first year, which Simulation projects to later years, or in a
situation the latest year, up to the one simulated, for which the profit was
supplied. These tests build small datasets and situations with earlier
inputs, so the data year and the simulated year differ, as they do for
survey data projected past the April 2027 raise to £3,000 (Budget 2026,
paragraph 6.254).
"""

import pandas as pd
import pytest

from policyengine_uk import Simulation
from policyengine_uk.data import UKSingleYearDataset

pytestmark = pytest.mark.usefixtures("cloned_uk_tax_benefit_system")

STATUSES = ["CLAIMANT", "NON_CLAIMANT", "UNKNOWN"]
ALLOWANCE = "gov.hmrc.income_tax.allowances.trading_allowance"


def traders(year, *, loss=0.0):
    """A claimant, a non-claimant and a trader of unknown status, measured in
    ``year``, each with £30,000 of pay and £5,000 of profit."""
    count = len(STATUSES)
    person = pd.DataFrame(
        {
            "person_id": range(1, count + 1),
            "person_benunit_id": range(1, count + 1),
            "person_household_id": range(1, count + 1),
            "age": [40] * count,
            "employment_income": [30_000.0] * count,
            "self_employment_income": [5_000.0] * count,
            "trading_loss": [loss] * count,
            "trading_allowance_claim_status": STATUSES,
        }
    )
    household = pd.DataFrame(
        {
            "household_id": range(1, count + 1),
            "region": ["LONDON"] * count,
            "tenure_type": ["OWNED_OUTRIGHT"] * count,
            "council_tax": [0.0] * count,
            "rent": [0.0] * count,
            "household_weight": [1.0] * count,
        }
    )
    return UKSingleYearDataset(
        person=person,
        benunit=pd.DataFrame({"benunit_id": range(1, count + 1)}),
        household=household,
        fiscal_year=year,
    )


def deduction(simulation, year):
    return simulation.calculate("trading_allowance_deduction", year).tolist()


def test_the_budget_raise_reaches_claimants_measured_at_1000():
    simulation = Simulation(dataset=traders(2025))
    # 2026-27: £1,000, which the claimant's profit already deducts.
    assert deduction(simulation, 2026) == [0, 0, 0]
    # 2027-28: £3,000 on the claimant's receipts of profit + £1,000. The
    # non-claimant elects nothing, and the unknown profit is above £3,000.
    assert deduction(simulation, 2027) == pytest.approx([2_000, 0, 0])


def test_data_measured_at_3000_gain_nothing_from_it():
    simulation = Simulation(dataset=traders(2027))
    for year in (2027, 2028):
        assert deduction(simulation, year) == [0, 0, 0]


def test_a_reform_of_the_data_year_leaves_the_input_allowance():
    reform = {ALLOWANCE: {str(year): 5_000 for year in range(2025, 2028)}}
    simulation = Simulation(dataset=traders(2025), reform=reform)
    # The profit still deducts the £1,000 legislated for 2025-26.
    assert deduction(simulation, 2026)[0] == pytest.approx(4_000)


def test_a_raise_never_raises_a_claimants_tax_when_they_have_a_loss():
    kept = {ALLOWANCE: {str(year): 1_000 for year in range(2027, 2029)}}
    law = Simulation(dataset=traders(2025, loss=1_000))
    at_1000 = Simulation(dataset=traders(2025, loss=1_000), reform=kept)
    # At £1,000 the allowance saves the claimant nothing over their
    # expenses, so they claim the loss. At £3,000 it saves £2,000, more than
    # the loss, so they take it and give the loss up (s. 783AM).
    assert not at_1000.calculate("uses_trading_allowance", 2027)[0]
    assert law.calculate("uses_trading_allowance", 2027)[0]
    assert (
        law.calculate("income_tax", 2027)[0] < at_1000.calculate("income_tax", 2027)[0]
    )


def situation(person):
    return {
        "people": {"person": person},
        "benunits": {"benunit": {"members": ["person"]}},
        "households": {"household": {"members": ["person"]}},
    }


def test_the_status_carries_forward_from_the_year_supplied():
    simulation = Simulation(
        situation=situation(
            {
                "age": {2025: 40},
                "self_employment_income": {2025: 2_500},
                "trading_allowance_claim_status": {2025: "CLAIMANT"},
            }
        )
    )
    # Simulation.calculate returns enum names.
    status = simulation.calculate("trading_allowance_claim_status", 2027)
    assert status.tolist() == ["CLAIMANT"]


def test_a_situation_reads_carried_inputs_as_measured_in_the_year_supplied():
    # This claimant's profit was net of 2025-26's £1,000, so in 2027-28 the
    # raise to £3,000 gives them £2,000, as the same inputs in a dataset
    # measured in 2025 do (test_the_budget_raise_reaches_claimants_measured_at_1000).
    simulation = Simulation(
        situation=situation(
            {
                "age": {2025: 40},
                "self_employment_income": {2025: 5_000},
                "trading_allowance_claim_status": {2025: "CLAIMANT"},
            }
        )
    )
    assert deduction(simulation, 2027) == pytest.approx([2_000])


def test_a_situation_reads_each_year_supplied_as_measured_then():
    # The 2027 profit was measured under 2027-28's £3,000, so it gains
    # nothing from it. 2026 reads the 2025 profit, not the later one: a
    # claimant at £1,000, who would gain £2,000 from a raise to £3,000.
    person = {
        "age": {2025: 40},
        "self_employment_income": {2025: 5_000, 2027: 5_000},
        "trading_allowance_claim_status": {2025: "CLAIMANT"},
    }
    simulation = Simulation(situation=situation(person))
    assert deduction(simulation, 2027) == [0]
    assert deduction(simulation, 2026) == [0]
    assert simulation.calculate("uses_trading_allowance", 2026).tolist() == [True]
    raised = Simulation(
        situation=situation(person), reform={ALLOWANCE: {"2026": 3_000}}
    )
    assert deduction(raised, 2026) == pytest.approx([2_000])


def test_a_situation_reads_the_year_of_the_profit_not_of_the_status():
    # A 2027 profit was measured in 2027-28, under £3,000, whatever year the
    # status was given for; a 2025 profit carried to 2027 was measured under
    # £1,000.
    later_profit = Simulation(
        situation=situation(
            {
                "age": {2027: 40},
                "self_employment_income": {2027: 5_000},
                "trading_allowance_claim_status": {2025: "CLAIMANT"},
            }
        )
    )
    assert deduction(later_profit, 2027) == [0]
    earlier_profit = Simulation(
        situation=situation(
            {
                "age": {2025: 40},
                "self_employment_income": {2025: 5_000},
                "trading_allowance_claim_status": {2027: "CLAIMANT"},
            }
        )
    )
    assert deduction(earlier_profit, 2027) == pytest.approx([2_000])


def test_a_raise_never_withdraws_a_situation_claimants_carried_loss():
    # The situation's inputs are for 2025, so in 2027 the raise to £3,000
    # gives this claimant £2,000. The 2025 loss carried into 2027 is not a
    # supplied 2027 loss, so it does not enter the election, for a claimant
    # as for anyone: they take the allowance at £1,000 and at £3,000 alike,
    # and the raise only adds its £2,000.
    person = {
        "age": {2025: 40},
        "employment_income": {2025: 30_000},
        "self_employment_income": {2025: 5_000},
        "trading_loss": {2025: 5_000},
        "trading_allowance_claim_status": {2025: "CLAIMANT"},
    }
    kept = {ALLOWANCE: {"2027": 1_000}}
    law = Simulation(situation=situation(person))
    at_1000 = Simulation(situation=situation(person), reform=kept)
    tax = law.calculate("income_tax", 2027)[0]
    assert tax == pytest.approx(at_1000.calculate("income_tax", 2027)[0] - 400, abs=1)


def test_a_situation_claimants_supplied_loss_meets_the_allowance_in_the_election():
    # A £1,000 loss supplied for 2027 itself enters the election. At £1,000
    # the allowance saves nothing over the claimant's expenses, so they
    # claim the loss; at £3,000 it saves £2,000, more than the loss, so they
    # take the allowance and give the loss up.
    person = {
        "age": {2025: 40},
        "employment_income": {2025: 30_000},
        "self_employment_income": {2025: 5_000},
        "trading_loss": {2027: 1_000},
        "trading_allowance_claim_status": {2025: "CLAIMANT"},
    }
    kept = {ALLOWANCE: {"2027": 1_000}}
    law = Simulation(situation=situation(person))
    at_1000 = Simulation(situation=situation(person), reform=kept)
    assert law.calculate("uses_trading_allowance", 2027).tolist() == [True]
    assert at_1000.calculate("uses_trading_allowance", 2027).tolist() == [False]
    assert at_1000.calculate("trade_loss_relief_against_general_income", 2027)[
        0
    ] == pytest.approx(1_000)
    assert (
        law.calculate("income_tax", 2027)[0] < at_1000.calculate("income_tax", 2027)[0]
    )


def claimant_with_2025_inputs():
    return situation(
        {
            "age": {2025: 40},
            "employment_income": {2025: 30_000},
            "self_employment_income": {2025: 5_000},
            "trading_allowance_claim_status": {2025: "CLAIMANT"},
        }
    )


def test_a_derivative_of_the_profit_leaves_the_data_year():
    # calculate_derivative steps the 2027 profit and sets it back, but the
    # situation's profit was given for 2025, and stays read as measured then.
    from policyengine_uk.dynamics.progression import calculate_derivative

    simulation = Simulation(situation=claimant_with_2025_inputs())
    before = simulation.calculate("income_tax", 2027)[0]
    assert deduction(simulation, 2027) == pytest.approx([2_000])
    calculate_derivative(
        simulation,
        input_variable="self_employment_income",
        year=2027,
        count_adults=1,
    )
    assert deduction(simulation, 2027) == pytest.approx([2_000])
    assert simulation.calculate("income_tax", 2027)[0] == pytest.approx(before)


def test_a_modifier_that_writes_the_profit_back_changes_nothing():
    from policyengine_uk.utils.scenario import Scenario

    def write_back(simulation):
        simulation.set_input(
            "self_employment_income",
            2027,
            simulation.calculate("self_employment_income", 2027),
        )

    reformed = Simulation(
        situation=claimant_with_2025_inputs(),
        scenario=Scenario(simulation_modifier=write_back),
    )
    assert reformed.calculate("income_tax", 2027)[0] == pytest.approx(
        reformed.baseline.calculate("income_tax", 2027)[0]
    )
    assert deduction(reformed, 2027) == pytest.approx([2_000])


def test_a_situation_built_without_a_profit_reads_the_years_one_is_set_for():
    # Nothing was recorded at the build, so the profit set afterwards for
    # 2025 is the one measured: under £1,000, so the 2027 raise gives £2,000.
    import numpy as np

    simulation = Simulation(situation=situation({"age": {2025: 40}}))
    simulation.set_input("self_employment_income", 2025, np.array([5_000.0]))
    simulation.set_input("trading_allowance_claim_status", 2025, np.array(["CLAIMANT"]))
    assert deduction(simulation, 2027) == pytest.approx([2_000])


def test_a_profit_set_after_the_build_leaves_the_recorded_year():
    # The situation gave a 2025 profit, so a 2027 profit set afterwards is
    # read as measured in 2025, as a modifier's or a derivative's would be.
    import numpy as np

    simulation = Simulation(situation=claimant_with_2025_inputs())
    simulation.set_input("self_employment_income", 2027, np.array([5_000.0]))
    assert deduction(simulation, 2027) == pytest.approx([2_000])


def test_replacing_the_populations_takes_their_profits_years():
    # Populations taken from a situation whose profit was given for 2027
    # bring that year, so the profit already deducts £3,000, as in a fresh
    # build from that situation.
    donor = Simulation(
        situation=situation(
            {
                "age": {2027: 40},
                "self_employment_income": {2027: 5_000},
                "trading_allowance_claim_status": {2027: "CLAIMANT"},
            }
        )
    )
    simulation = Simulation(situation=claimant_with_2025_inputs())
    simulation.build_from_populations(donor.populations)
    assert deduction(simulation, 2027) == [0]


def test_a_core_simulation_over_data_reads_the_first_year_of_the_profit():
    # Data stored for every year, as a policyengine-core simulation over a
    # data frame holds them, were measured in their first year: 2025, under
    # £1,000, so the 2027 raise gives the claimant £2,000.
    from policyengine_core.simulations import Simulation as CoreSimulation

    from policyengine_uk.system import system

    record = pd.DataFrame(
        {
            "person_id": [1],
            "person_benunit_id": [1],
            "person_household_id": [1],
            "benunit_id": [1],
            "household_id": [1],
            "age": [40],
            "self_employment_income": [5_000.0],
            "trading_allowance_claim_status": ["CLAIMANT"],
            "household_weight": [1.0],
        }
    )
    frame = pd.concat(
        [
            record.rename(columns=lambda column: f"{column}__{year}")
            for year in range(2025, 2029)
        ],
        axis=1,
    )
    simulation = CoreSimulation(tax_benefit_system=system, dataset=frame)
    assert simulation.calculate("trading_allowance_deduction", 2027).tolist() == (
        pytest.approx([2_000])
    )
