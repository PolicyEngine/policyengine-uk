"""input_periods lists entered values only, as the simulation branch reads them."""

from policyengine_uk import Simulation
from policyengine_uk.utils.inputs import (
    has_input_by,
    input_periods,
    latest_input_period_before,
)

SITUATION = {
    "people": {
        "person": {
            "age": {2024: 30},
            "employment_income": {2024: 20_000, 2026: 25_000},
        }
    },
    "benunits": {"benunit": {"members": ["person"]}},
    "households": {"household": {"members": ["person"]}},
}


def years(periods):
    return [period.start.year for period in periods]


def test_values_the_model_calculated_are_not_inputs():
    sim = Simulation(situation=SITUATION)
    # A formula result, a carried-over input and a default are all stored.
    sim.calculate("current_education", 2024)
    sim.calculate("age", 2027)
    sim.calculate("in_HE", 2025)
    assert input_periods(sim, "current_education") == []
    assert years(input_periods(sim, "age")) == [2024]
    assert input_periods(sim, "in_HE") == []


def test_inputs_are_listed_earliest_first_and_queried_by_period():
    sim = Simulation(situation=SITUATION)
    assert years(input_periods(sim, "age")) == [2024]
    assert latest_input_period_before(sim, "age", _year(2024)) is None
    assert latest_input_period_before(sim, "age", _year(2030)).start.year == 2024
    assert has_input_by(sim, "age", _year(2024))
    assert not has_input_by(sim, "age", _year(2023))


def test_a_branch_reads_its_ancestors_inputs_but_not_a_siblings():
    sim = Simulation(situation=SITUATION)
    parent = sim.get_branch("parent")
    parent.set_input("in_HE", 2025, [True])
    child = parent.get_branch("child")
    sibling = sim.get_branch("sibling")
    sibling.set_input("in_HE", 2026, [True])
    assert years(input_periods(child, "in_HE")) == [2025]
    assert years(input_periods(parent, "in_HE")) == [2025]
    assert years(input_periods(sibling, "in_HE")) == [2026]
    assert input_periods(sim, "in_HE") == []


def test_an_input_entered_after_branching_is_not_read_by_the_branch():
    # A branch copies its parent's values when it is created, so it does not
    # read what the parent is given later; input_periods follows what it reads.
    sim = Simulation(situation=SITUATION)
    branch = sim.get_branch("branch")
    sim.set_input("in_HE", 2025, [True])
    assert input_periods(branch, "in_HE") == []
    assert branch.get_holder("in_HE").get_array(_year(2025), "branch") is None
    assert years(input_periods(sim, "in_HE")) == [2025]


def test_deleted_inputs_are_left_out():
    sim = Simulation(situation=SITUATION)
    sim.set_input("in_HE", 2025, [True])
    sim.get_holder("in_HE").delete_arrays(_year(2025))
    assert input_periods(sim, "in_HE") == []


def _year(year):
    from policyengine_core.periods import period

    return period(str(year))
