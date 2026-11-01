"""The trading allowance claim status reads the allowance of the year the
input data were measured (PolicyEngine/policyengine-uk#2764).

A claimant's profit already deducts the allowance legislated for that year:
a dataset's first year, which Simulation projects to later years, or in a
situation the latest year, up to the one simulated, of those it gave the
profit for, as recorded when it was built or took another simulation's
populations, failing that as supplied when the allowance was first
calculated. These tests build small datasets and situations with earlier
inputs, so the data year and the simulated year differ, as they do for
survey data projected past the April 2027 raise to £3,000 (Budget 2026,
paragraph 6.254). The last checks that uses_trading_allowance follows a
deduction that does not come from its formula.
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


def claimant_given_2025_inputs_after_a_bare_build():
    import numpy as np

    simulation = Simulation(
        situation=situation({"age": {2025: 40}, "employment_income": {2025: 30_000}})
    )
    simulation.set_input("self_employment_income", 2025, np.array([5_000.0]))
    simulation.set_input("trading_allowance_claim_status", 2025, np.array(["CLAIMANT"]))
    return simulation


def test_a_profit_set_after_a_bare_build_is_kept_from_the_first_calculation():
    # The bare build recorded no profit, so the 2025 profit set before the
    # first calculation is the one measured, and a derivative's later writes
    # of the 2027 profit leave it, as they do for a situation that gave the
    # profit.
    from policyengine_uk.dynamics.progression import calculate_derivative

    bare = claimant_given_2025_inputs_after_a_bare_build()
    given = Simulation(
        situation=situation(
            {
                "age": {2025: 40},
                "employment_income": {2025: 30_000},
                "self_employment_income": {2025: 5_000},
                "trading_allowance_claim_status": {2025: "CLAIMANT"},
            }
        )
    )
    arguments = dict(input_variable="self_employment_income", year=2027, count_adults=1)
    assert calculate_derivative(bare, **arguments).tolist() == (
        calculate_derivative(given, **arguments).tolist()
    )
    assert deduction(bare, 2027) == pytest.approx([2_000])


def test_a_branch_that_sets_the_profit_keeps_the_data_year():
    import numpy as np

    branch = claimant_given_2025_inputs_after_a_bare_build().get_branch("raise")
    branch.set_input("self_employment_income", 2027, np.array([5_000.0]))
    assert deduction(branch, 2027) == pytest.approx([2_000])


def test_with_no_recorded_year_up_to_the_one_simulated_a_set_profit_counts():
    # The situation gave a profit for 2028 only, so 2027 reads the 2025
    # profit set afterwards, as it would had every input been set that way.
    import numpy as np

    simulation = Simulation(
        situation=situation(
            {
                "age": {2025: 40},
                "self_employment_income": {2028: 5_000},
                "trading_allowance_claim_status": {2028: "CLAIMANT"},
            }
        )
    )
    simulation.set_input("self_employment_income", 2025, np.array([5_000.0]))
    simulation.set_input("trading_allowance_claim_status", 2025, np.array(["CLAIMANT"]))
    assert deduction(simulation, 2027) == pytest.approx([2_000])


def test_replacing_the_populations_keeps_the_donors_record():
    # The donor gave a 2025 profit; its 2027 profit set afterwards leaves its
    # data year at 2025, and populations taken from it bring that record.
    import numpy as np

    donor = Simulation(situation=claimant_with_2025_inputs())
    donor.set_input("self_employment_income", 2027, np.array([5_000.0]))
    simulation = Simulation(situation=situation({"age": {2026: 40}}))
    simulation.build_from_populations(donor.populations)
    assert deduction(donor, 2027) == pytest.approx([2_000])
    assert deduction(simulation, 2027) == pytest.approx([2_000])


def test_a_situation_taking_a_datasets_populations_reads_its_first_year():
    data = Simulation(dataset=traders(2025))
    simulation = Simulation(situation=situation({"age": {2026: 40}}))
    simulation.build_from_populations(data.populations)
    assert deduction(simulation, 2027)[0] == pytest.approx(2_000)


def core_simulation_over_a_claimant_frame():
    """A policyengine-core simulation over a frame holding a claimant's £5,000
    profit for each year from 2025 to 2028."""
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
    return CoreSimulation(tax_benefit_system=system, dataset=frame)


def test_a_core_simulation_over_data_reads_the_first_year_of_the_profit():
    # Data stored for every year, as a policyengine-core simulation over a
    # data frame holds them, were measured in their first year: 2025, under
    # £1,000, so the 2027 raise gives the claimant £2,000.
    simulation = core_simulation_over_a_claimant_frame()
    assert simulation.calculate("trading_allowance_deduction", 2027).tolist() == (
        pytest.approx([2_000])
    )


def claimants(*profits):
    """Claimants from 2025 with £30,000 of pay, one for each mapping of years
    to self-employment profit given; an empty one gives no profit."""
    people = {}
    for index, profit in enumerate(profits):
        person = {
            "age": {2025: 40},
            "employment_income": {2025: 30_000},
            "trading_allowance_claim_status": {2025: "CLAIMANT"},
        }
        if profit:
            person["self_employment_income"] = profit
        people[f"person_{index}"] = person
    return {
        "people": people,
        "benunits": {
            f"benunit_{index}": {"members": [name]} for index, name in enumerate(people)
        },
        "households": {"household": {"members": list(people)}},
    }


def test_profits_set_one_year_at_a_time_read_as_a_dictionary_giving_them_all():
    # A £5,000 profit for each year from 2025 to 2030, set one year at a
    # time and in any order before the first calculation, is read as the
    # dictionary giving them all reads it: in 2027 the 2027 profit, measured
    # under £3,000, which gains nothing from it.
    import numpy as np

    years = range(2025, 2031)
    given = Simulation(situation=claimants({year: 5_000 for year in years}))
    assert deduction(given, 2027) == [0]
    tax = given.calculate("income_tax", 2027)[0]
    for order in (years, reversed(years), (2027, 2025, 2026, 2028, 2029, 2030)):
        simulation = Simulation(situation=claimants({}))
        for year in order:
            simulation.set_input("self_employment_income", year, np.array([5_000.0]))
        assert deduction(simulation, 2027) == [0]
        assert simulation.calculate("income_tax", 2027)[0] == pytest.approx(tax)


def test_two_peoples_profits_set_in_turn_read_as_a_dictionary_giving_both():
    # One claimant's profit was given for 2025 and the other's for 2027; the
    # builder stores each year for both, the other at nil. Set that way in
    # either order, they are read as the dictionary reads them.
    import numpy as np

    given = Simulation(situation=claimants({2025: 5_000}, {2027: 5_000}))
    assert deduction(given, 2027) == [0, 0]
    profits = {2025: [5_000.0, 0.0], 2027: [0.0, 5_000.0]}
    for order in ((2025, 2027), (2027, 2025)):
        simulation = Simulation(situation=claimants({}, {}))
        for year in order:
            simulation.set_input(
                "self_employment_income", year, np.array(profits[year])
            )
        assert deduction(simulation, 2027) == [0, 0]


def test_a_modifier_writing_back_a_profit_on_a_bare_situation_changes_nothing():
    # The modifier writes back the 2025 profit, nil, before a 2027 profit is
    # given to the reform and its baseline alike. Its year joins the 2027
    # one, so both read that profit as measured in 2027.
    import numpy as np

    from policyengine_uk.utils.scenario import Scenario

    def write_back(simulation):
        simulation.set_input(
            "self_employment_income",
            2025,
            simulation.calculate("self_employment_income", 2025),
        )

    reformed = Simulation(
        situation=claimants({}), scenario=Scenario(simulation_modifier=write_back)
    )
    for simulation in (reformed, reformed.baseline):
        simulation.set_input("self_employment_income", 2027, np.array([5_000.0]))
    assert deduction(reformed, 2027) == deduction(reformed.baseline, 2027) == [0]
    assert reformed.calculate("income_tax", 2027)[0] == pytest.approx(
        reformed.baseline.calculate("income_tax", 2027)[0]
    )


def test_writes_after_the_first_calculation_leave_a_later_profits_fallback():
    # The situation gave a profit for 2028 only, so 2027 reads the 2025
    # profit set before the first calculation. A derivative's writes of the
    # 2027 profit, and a branch's, leave that year, as they leave it where
    # every profit was set.
    import numpy as np

    from policyengine_uk.dynamics.progression import calculate_derivative

    def given_2028_then_set_2025():
        simulation = Simulation(situation=claimants({2028: 5_000}))
        simulation.set_input("self_employment_income", 2025, np.array([5_000.0]))
        return simulation

    every_profit_set = Simulation(situation=claimants({}))
    for year in (2025, 2028):
        every_profit_set.set_input("self_employment_income", year, np.array([5_000.0]))
    arguments = dict(input_variable="self_employment_income", year=2027, count_adults=1)
    simulation = given_2028_then_set_2025()
    assert calculate_derivative(simulation, **arguments).tolist() == (
        calculate_derivative(every_profit_set, **arguments).tolist()
    )
    assert deduction(simulation, 2027) == pytest.approx([2_000])
    parent = given_2028_then_set_2025()
    branch = parent.get_branch("raise")
    branch.set_input("self_employment_income", 2027, np.array([5_000.0]))
    assert deduction(branch, 2027) == pytest.approx([2_000])
    assert deduction(parent, 2027) == pytest.approx([2_000])


def test_a_profit_the_model_sets_is_not_a_year_supplied():
    # A scenario's own value (set_model_value) is not supplied, so a 2027
    # profit the model sets first leaves the 2025 profit set afterwards as
    # the one measured.
    import numpy as np

    from policyengine_uk.utils.supplied_inputs import set_model_value

    simulation = Simulation(situation=claimants({}))
    set_model_value(simulation, "self_employment_income", 2027, np.array([5_000.0]))
    simulation.set_input("self_employment_income", 2025, np.array([5_000.0]))
    assert deduction(simulation, 2027) == pytest.approx([2_000])


def test_rebuilding_from_its_own_populations_keeps_the_record():
    # The 2027 profit set after the build stays out of the record when the
    # simulation takes its own populations back.
    import numpy as np

    simulation = Simulation(situation=claimant_with_2025_inputs())
    simulation.set_input("self_employment_income", 2027, np.array([5_000.0]))
    simulation.build_from_populations(simulation.populations)
    assert deduction(simulation, 2027) == pytest.approx([2_000])


def test_populations_from_data_without_years_bring_their_earliest_profit_year():
    # The frame holds a profit for each year from 2025, measured in 2025.
    simulation = Simulation(situation=situation({"age": {2026: 40}}))
    simulation.build_from_populations(
        core_simulation_over_a_claimant_frame().populations
    )
    assert deduction(simulation, 2027) == pytest.approx([2_000])


def test_populations_pass_a_datasets_first_year_on():
    data = Simulation(dataset=traders(2025))
    first = Simulation(situation=situation({"age": {2026: 40}}))
    first.build_from_populations(data.populations)
    second = Simulation(situation=situation({"age": {2026: 40}}))
    second.build_from_populations(first.populations)
    assert deduction(second, 2027)[0] == pytest.approx(2_000)


def test_a_neutralised_deduction_keeps_a_raise_from_costing_a_claimant_their_loss():
    # The deduction applied is nil whatever the claimant chooses, so the
    # flag follows it, as for anyone: they keep their £1,500 loss under a
    # raise to £3,000, and pay what they pay at £1,000.
    from policyengine_core.reforms import Reform

    class neutralise_deduction(Reform):
        def apply(self):
            self.neutralize_variable("trading_allowance_deduction")

    person = {
        "age": {2026: 40},
        "employment_income": {2026: 30_000},
        "self_employment_income": {2026: 2_500},
        "trading_loss": {2026: 1_500},
        "trading_allowance_claim_status": {2026: "CLAIMANT"},
    }
    simulation = Simulation(
        situation=situation(person),
        reform=(neutralise_deduction, {ALLOWANCE: {"2026": 3_000}}),
    )
    assert simulation.calculate("uses_trading_allowance", 2026).tolist() == [False]
    assert simulation.calculate(
        "trade_loss_relief_against_general_income", 2026
    ).tolist() == pytest.approx([1_500])
    # (30,000 + 2,500 - 1,500 - 12,570) x 20%
    assert simulation.calculate("income_tax", 2026).tolist() == pytest.approx([3_686])
