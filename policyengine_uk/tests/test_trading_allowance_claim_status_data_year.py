"""The trading allowance claim status reads the allowance of the year the
input data were measured (PolicyEngine/policyengine-uk#2764).

A claimant's profit already deducts the allowance legislated for that year:
a dataset's first year, which Simulation projects to later years, or in a
situation the latest year, up to the one simulated, for which the status was
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


def test_a_raise_never_withdraws_a_claimants_loss_relief():
    kept = {ALLOWANCE: {str(year): 1_000 for year in range(2027, 2029)}}
    law = Simulation(dataset=traders(2025, loss=5_000))
    at_1000 = Simulation(dataset=traders(2025, loss=5_000), reform=kept)
    # The claimant's claim gave the loss up at £1,000 and still does at
    # £3,000, so the raise only adds the £2,000 deduction.
    tax = law.calculate("income_tax", 2027)[0]
    assert tax == pytest.approx(at_1000.calculate("income_tax", 2027)[0] - 400, abs=1)


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
    # Inputs supplied for 2027 were measured under 2027-28's £3,000, so they
    # gain nothing from it; 2026 still reads the 2025 inputs, at £1,000.
    simulation = Simulation(
        situation=situation(
            {
                "age": {2025: 40},
                "self_employment_income": {2025: 5_000, 2027: 5_000},
                "trading_allowance_claim_status": {
                    2025: "CLAIMANT",
                    2027: "CLAIMANT",
                },
            }
        )
    )
    assert deduction(simulation, 2026) == [0]
    assert deduction(simulation, 2027) == [0]


def test_a_raise_never_withdraws_a_situation_claimants_loss_relief():
    # The situation's inputs are for 2025, so in 2027 the raise to £3,000
    # gives this claimant £2,000. Their claim gave the loss up at £1,000 and
    # still does at £3,000, so the raise only lowers their tax.
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
