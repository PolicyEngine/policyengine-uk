"""The trading allowance claim status reads the allowance of the year the
input data were measured (PolicyEngine/policyengine-uk#2764).

A claimant's profit already deducts the allowance legislated for that year:
a dataset's first year, which Simulation projects to later years, and for
anything else, such as a situation, the year simulated, as the State Pension
variables read them. These tests build small datasets with earlier inputs,
so the data year and the simulated year differ, as they do for survey data
projected past the April 2027 raise to £3,000 (Budget 2026, paragraph
6.254). They also check that a situation's data year does not depend on how
or when its profit was given, and that a deduction which does not come from
its formula enters the claimant's election at the value applied.
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


def test_a_situation_reads_its_profit_as_measured_in_the_year_simulated():
    # A 2027 profit already deducts 2027-28's £3,000, and a 2026 profit
    # 2026-27's £1,000, which a raise to £3,000 then exceeds by £2,000.
    later = Simulation(
        situation=situation(
            {
                "age": {2027: 40},
                "self_employment_income": {2027: 5_000},
                "trading_allowance_claim_status": {2027: "CLAIMANT"},
            }
        )
    )
    assert deduction(later, 2027) == [0]
    person = {
        "age": {2026: 40},
        "self_employment_income": {2026: 5_000},
        "trading_allowance_claim_status": {2026: "CLAIMANT"},
    }
    assert deduction(Simulation(situation=situation(person)), 2026) == [0]
    raised = Simulation(
        situation=situation(person), reform={ALLOWANCE: {"2026": 3_000}}
    )
    assert deduction(raised, 2026) == pytest.approx([2_000])


def test_a_situation_reads_a_carried_profit_as_measured_in_the_year_simulated():
    # The documented limit: a profit given for 2025 and carried into 2027 is
    # read as net of 2027-28's £3,000, so the raise gives it nothing, where
    # the same record in a dataset measured in 2025 gains £2,000.
    carried = Simulation(
        situation=situation(
            {
                "age": {2025: 40},
                "employment_income": {2025: 30_000},
                "self_employment_income": {2025: 5_000},
                "trading_allowance_claim_status": {2025: "CLAIMANT"},
            }
        )
    )
    assert deduction(carried, 2027) == [0]
    assert deduction(Simulation(dataset=traders(2025)), 2027)[0] == pytest.approx(2_000)


def claimants(*profits):
    """Claimants from 2026 with £30,000 of pay, one for each mapping of years
    to self-employment profit given; an empty one gives no profit."""
    people = {}
    for index, profit in enumerate(profits):
        person = {
            "age": {2026: 40},
            "employment_income": {2026: 30_000},
            "trading_allowance_claim_status": {2026: "CLAIMANT"},
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


def test_a_situations_data_year_does_not_depend_on_how_its_profit_was_given():
    # Profits for each year from 2026 to 2030, given in the dictionary or
    # set one year at a time in any order, and two people's set in turn,
    # all read each year's profit as measured in that year.
    import numpy as np

    years = range(2026, 2031)
    given = Simulation(situation=claimants({year: 5_000 for year in years}))
    tax = given.calculate("income_tax", 2027)[0]
    assert deduction(given, 2027) == [0]
    for order in (years, reversed(years)):
        simulation = Simulation(situation=claimants({}))
        for year in order:
            simulation.set_input("self_employment_income", year, np.array([5_000.0]))
        assert deduction(simulation, 2027) == [0]
        assert simulation.calculate("income_tax", 2027)[0] == pytest.approx(tax)
    pair = Simulation(situation=claimants({}, {}))
    pair.set_input("self_employment_income", 2027, np.array([0.0, 5_000.0]))
    pair.set_input("self_employment_income", 2026, np.array([5_000.0, 0.0]))
    assert deduction(pair, 2027) == deduction(
        Simulation(situation=claimants({2026: 5_000}, {2027: 5_000})), 2027
    )


def test_derivatives_branches_and_modifiers_leave_a_situations_data_year():
    import numpy as np

    from policyengine_uk.dynamics.progression import calculate_derivative
    from policyengine_uk.utils.scenario import Scenario

    # A derivative of the profit, this package's or policyengine-core's,
    # and whether or not anything was calculated before it.
    def claimant():
        return Simulation(situation=claimants({2027: 5_000}))

    arguments = dict(input_variable="self_employment_income", year=2027, count_adults=1)
    assert calculate_derivative(claimant(), **arguments).tolist() == (
        calculate_derivative(claimant(), **arguments).tolist()
    )
    first = claimant().derivative("income_tax", "self_employment_income", 2027)
    calculated = claimant()
    calculated.calculate("income_tax", 2027)
    later = calculated.derivative("income_tax", "self_employment_income", 2027)
    assert first.tolist() == pytest.approx(later.tolist())
    # A branch given the profit reads it as a simulation given it does.
    branch = Simulation(situation=claimants({})).get_branch("raise")
    branch.set_input("self_employment_income", 2025, np.array([5_000.0]))
    alone = Simulation(situation=claimants({}))
    alone.set_input("self_employment_income", 2025, np.array([5_000.0]))
    assert deduction(branch, 2027) == deduction(alone, 2027)
    # A modifier that writes a profit back changes nothing.

    def write_back(simulation):
        simulation.set_input(
            "self_employment_income",
            2025,
            simulation.calculate("self_employment_income", 2025),
        )

    reformed = Simulation(
        situation=claimants({2027: 5_000}),
        scenario=Scenario(simulation_modifier=write_back),
    )
    assert reformed.calculate("income_tax", 2027)[0] == pytest.approx(
        reformed.baseline.calculate("income_tax", 2027)[0]
    )


def test_a_situation_taking_a_datasets_populations_reads_the_year_simulated():
    # The documented limit: only a simulation built from the data reads
    # their first year, so a situation that takes a dataset's populations
    # reads the year simulated, where the dataset gives £2,000.
    data = Simulation(dataset=traders(2025))
    simulation = Simulation(situation=situation({"age": {2026: 40}}))
    simulation.build_from_populations(data.populations)
    assert deduction(simulation, 2027)[0] == 0
    assert deduction(data, 2027)[0] == pytest.approx(2_000)


def test_a_household_subset_of_data_reads_their_first_year():
    # A subset is a branch of the data's simulation, so it reads the
    # dataset's first year, as the whole population does.
    import numpy as np

    from policyengine_uk.utils.household_subset import household_subset

    data = Simulation(dataset=traders(2025))
    with household_subset(data, "claimant", np.array([True, False, False])) as subset:
        assert subset.person is not None
        assert subset.simulation.calculate(
            "trading_allowance_deduction", 2027
        ).tolist() == pytest.approx([2_000])


def test_a_raise_never_withdraws_a_situation_claimants_carried_loss():
    # A 2025 loss carried into 2026 is not a supplied 2026 loss, so it does
    # not enter the election, for a claimant as for anyone: they take the
    # allowance at £1,000 and at £3,000 alike, and the raise adds its £2,000.
    person = {
        "age": {2026: 40},
        "employment_income": {2026: 30_000},
        "self_employment_income": {2026: 5_000},
        "trading_loss": {2025: 5_000},
        "trading_allowance_claim_status": {2026: "CLAIMANT"},
    }
    law = Simulation(situation=situation(person))
    raised = Simulation(
        situation=situation(person), reform={ALLOWANCE: {"2026": 3_000}}
    )
    assert raised.calculate("uses_trading_allowance", 2026).tolist() == [True]
    assert raised.calculate("income_tax", 2026)[0] == pytest.approx(
        law.calculate("income_tax", 2026)[0] - 400, abs=1
    )


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


def test_a_neutralised_deduction_keeps_a_raise_from_costing_a_claimant_their_loss():
    # The deduction applied is nil whatever the claimant elects, so their
    # election weighs it as the allowance's: it saves nothing over their
    # expenses, and they keep their £1,500 loss under a raise to £3,000.
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


DEDUCTIONS = (
    "trading_allowance_deduction",
    "miscellaneous_income_trading_allowance_deduction",
)
COMPARED = DEDUCTIONS + (
    "taxable_self_employment_income",
    "taxable_miscellaneous_income",
    "uses_trading_allowance",
    "trade_loss_relief_against_general_income",
    "ni_class_4",
    "income_tax",
)


def grid_situation():
    """One person for each status, profit, capital allowances, casual income
    and current loss, all for 2026, each in their own household."""
    import itertools

    people = {}
    for index, (status, profit, capital, casual, loss) in enumerate(
        itertools.product(
            ["CLAIMANT", "UNKNOWN", "NON_CLAIMANT"],
            [500, 2_500, 5_000],
            [0, 600],
            [0, 600, 1_000],
            [0, 400, 800, 1_500],
        )
    ):
        people[f"person_{index}"] = {
            "age": {2026: 40},
            "employment_income": {2026: 30_000},
            "self_employment_income": {2026: profit},
            "capital_allowances": {2026: capital},
            "miscellaneous_income": {2026: casual},
            "income_not_otherwise_charged": {2026: casual},
            "trading_loss": {2026: loss},
            "trading_allowance_claim_status": {2026: status},
        }
    return {
        "people": people,
        "benunits": {f"b_{name}": {"members": [name]} for name in people},
        "households": {f"h_{name}": {"members": [name]} for name in people},
    }


@pytest.mark.parametrize("allowance,share", [(1_000, 0.5), (3_000, 1.0), (300, 0.5)])
def test_a_deduction_pinned_to_its_formulas_value_changes_nothing(allowance, share):
    # Whichever deductions are pinned, supplied or set by the model, to the
    # values their formulas give, every status's election, deductions and
    # taxes stay as they are.
    from policyengine_uk.utils.supplied_inputs import set_model_value

    reform = {
        ALLOWANCE: {"2026": allowance},
        "gov.simulation.trading_allowance_claimant_expense_share": {"2026": share},
    }
    unpinned = Simulation(situation=grid_situation(), reform=reform)
    expected = {name: unpinned.calculate(name, 2026) for name in COMPARED}
    for pinned, by_model in (
        (DEDUCTIONS[:1], False),
        (DEDUCTIONS[1:], False),
        (DEDUCTIONS, False),
        (DEDUCTIONS[:1], True),
    ):
        simulation = Simulation(situation=grid_situation(), reform=reform)
        for name in pinned:
            if by_model:
                set_model_value(simulation, name, 2026, expected[name])
            else:
                simulation.set_input(name, 2026, expected[name])
        for name in COMPARED:
            actual = simulation.calculate(name, 2026)
            assert (
                actual.tolist() == expected[name].tolist()
                if actual.dtype == bool
                else actual.tolist() == pytest.approx(expected[name].tolist(), abs=0.01)
            ), (name, pinned, by_model)
