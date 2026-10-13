"""A reform applied to a built simulation keeps the inputs it stores.

input_variables is taken when a simulation is built, and reset_calculations
deletes the values of every variable it does not name (as derivative did
before policyengine-core 3.33.0, from which it keeps every input). So
Simulation.apply_reform names each variable the reform stored an input for
that the simulation still holds afterwards, however the reform stored it, and
no other: an input set since the build that the reform did not store is still
deleted by a reset, as before, unless the reform names its variable.
input_variables names whole variables, so a reset keeps every input of a named
variable. See _InputKeyLog in policyengine_uk/simulation.py.

Each simulation is one adult, the claimant, with £3,000 of income-related ESA
entered for 2026, so their claimant-or-partner award that year is £3,000
unless an input replaces it.
"""

import copy
import pickle
import threading
from functools import cache

import numpy as np
import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from policyengine_core.periods import period

from policyengine_uk import Simulation
from policyengine_uk.model_api import (
    MONTH,
    YEAR,
    BenUnit,
    Reform,
    Variable,
    set_input_dispatch_by_period,
)

SCOPED = "claimant_or_partner_esa_income"
AWARD_YEAR = 2026
SITUATION = {
    "people": {
        "claimant": {
            "age": {2025: 40, 2026: 40, 2027: 40},
            "is_claimant_or_partner": {2025: True, 2026: True, 2027: True},
        }
    },
    "benunits": {
        "benunit": {"members": ["claimant"], "esa_income": {AWARD_YEAR: 3_000}}
    },
    "households": {"household": {"members": ["claimant"]}},
}


def as_reform(apply):
    return type("TestReform", (Reform,), {"apply": apply})


def built():
    # An input set after the build: recorded as an input, not named.
    simulation = Simulation(situation=SITUATION)
    simulation.set_input(SCOPED, AWARD_YEAR, [100])
    assert SCOPED not in simulation.input_variables
    return simulation


def through_the_simulation(reform):
    reform.simulation.set_input(SCOPED, AWARD_YEAR, [0])


def through_the_holder(reform):
    simulation = reform.simulation
    holder = simulation.get_holder(SCOPED)
    holder.set_input(period(AWARD_YEAR), [0], simulation.branch_name)


def from_another_thread(reform):
    worker = threading.Thread(
        target=reform.simulation.set_input, args=(SCOPED, AWARD_YEAR, [0])
    )
    worker.start()
    worker.join()


def while_another_simulation_applies_a_reform(reform):
    simulation = reform.simulation
    other = simulation.clone()
    other.apply_reform(
        as_reform(lambda _: simulation.set_input(SCOPED, AWARD_YEAR, [0]))
    )


def after_applying_another_reform_to_itself(reform):
    simulation = reform.simulation
    simulation.apply_reform(as_reform(lambda _: None))
    simulation.set_input(SCOPED, AWARD_YEAR, [0])


def after_its_record_is_rebuilt(reform):
    # Core replaces the record when it rebinds the simulation to its system.
    simulation = reform.simulation
    simulation._bind_to_tax_benefit_system()
    simulation.set_input(SCOPED, AWARD_YEAR, [0])


STORING = {
    "the simulation's set_input": as_reform(through_the_simulation),
    "a holder's set_input": as_reform(through_the_holder),
    "another thread": as_reform(from_another_thread),
    "while another simulation applies a reform": as_reform(
        while_another_simulation_applies_a_reform
    ),
    "after applying another reform to itself": as_reform(
        after_applying_another_reform_to_itself
    ),
    "after its record is rebuilt": as_reform(after_its_record_is_rebuilt),
    "a tuple's second reform": (
        as_reform(lambda _: None),
        as_reform(through_the_simulation),
    ),
}


@pytest.mark.parametrize("route", STORING)
def test_a_reform_keeps_what_it_stores_through_a_reset(route):
    simulation = built()
    names = simulation.input_variables
    recorded = list(names)
    simulation.apply_reform(STORING[route])
    assert simulation.input_variables == recorded + [SCOPED]
    assert names == recorded
    assert type(simulation._user_input_keys) is set
    assert simulation.tax_benefit_system.simulation is simulation
    assert simulation.calculate(SCOPED, AWARD_YEAR).tolist() == [0]
    # From policyengine-core 3.33.0 derivative keeps every input, named or not.
    assert not simulation.derivative(SCOPED, "employment_income", AWARD_YEAR).any()
    simulation.reset_calculations()
    assert simulation.calculate(SCOPED, AWARD_YEAR).tolist() == [0]


class ended_award(Variable):
    value_type = float
    entity = BenUnit
    label = "An award that ends in 2026"
    definition_period = YEAR
    end = "2026-12-31"

    def formula(benunit, period, parameters):
        return 42


def stores_then_deletes_another_year(simulation):
    def apply(reform):
        reform.simulation.set_input(SCOPED, AWARD_YEAR + 1, [0])
        reform.simulation.delete_arrays(SCOPED, AWARD_YEAR + 1)

    simulation.apply_reform(as_reform(apply))
    return SCOPED, AWARD_YEAR, 3_000


def sets_a_year_after_the_variables_end(simulation):
    simulation.tax_benefit_system.add_variable(ended_award)
    simulation.set_input("ended_award", AWARD_YEAR, [100])
    simulation.apply_reform(
        as_reform(
            lambda reform: reform.simulation.set_input(
                "ended_award", AWARD_YEAR + 1, [0]
            )
        )
    )
    return "ended_award", AWARD_YEAR, 42


class monthly_flag(Variable):
    value_type = bool
    entity = BenUnit
    label = "A monthly flag a yearly input sets in each month"
    definition_period = MONTH
    set_input = set_input_dispatch_by_period

    def formula(benunit, period, parameters):
        return False


def sets_a_year_whose_months_a_helper_keeps(simulation):
    # The helper sets a yearly input in each month, skipping a month that
    # already holds an input.
    simulation.tax_benefit_system.add_variable(monthly_flag)
    for month in range(1, 13):
        simulation.set_input("monthly_flag", f"{AWARD_YEAR}-{month:02}", [True])
    simulation.apply_reform(
        as_reform(
            lambda reform: reform.simulation.set_input(
                "monthly_flag", AWARD_YEAR, [False]
            )
        )
    )
    january = f"{AWARD_YEAR}-01"
    assert simulation.calculate("monthly_flag", january).tolist() == [True]
    return "monthly_flag", january, False


NOT_STORING = {
    "stores and deletes another year": stores_then_deletes_another_year,
    "sets a year after the variable's end": sets_a_year_after_the_variables_end,
    "sets a year whose months a helper keeps": sets_a_year_whose_months_a_helper_keeps,
}


@pytest.mark.parametrize("case", NOT_STORING)
def test_a_reform_names_no_input_it_did_not_store(case):
    # The reform tries to set the variable but leaves no input of its own,
    # while one set since the build survives. That one is not the reform's,
    # so it is not named, and a reset deletes it as it would have anyway.
    simulation = built()
    recorded = list(simulation.input_variables)
    variable, year, calculated = NOT_STORING[case](simulation)
    assert simulation.input_variables == recorded
    simulation.reset_calculations()
    assert simulation.calculate(variable, year).tolist() == [calculated]


class added_award(Variable):
    value_type = float
    entity = BenUnit
    label = "An award added after the build"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        return 42


def test_a_reform_names_no_input_of_a_variable_it_neutralizes():
    # Core stores nothing for a variable neutralized before the simulation
    # makes its holder. (The build makes a holder for every variable it has
    # then, and a holder keeps the definition it was made with, so this
    # variable is added after the build.)
    def apply(reform):
        reform.neutralize_variable("added_award")
        reform.simulation.set_input("added_award", AWARD_YEAR, [0])

    simulation = built()
    simulation.tax_benefit_system.add_variable(added_award)
    recorded = list(simulation.input_variables)
    with pytest.warns(Warning, match="neutralized"):
        simulation.apply_reform(as_reform(apply))
    assert simulation.input_variables == recorded
    assert simulation.calculate("added_award", AWARD_YEAR).tolist() == [0]


@pytest.mark.parametrize("route", ["clone", "branch"])
def test_a_reform_names_nothing_it_stores_on_a_clone_or_branch(route):
    def apply(reform):
        simulation = reform.simulation
        other = (
            simulation.clone() if route == "clone" else simulation.get_branch("other")
        )
        other.set_input(SCOPED, AWARD_YEAR, [0])

    simulation = built()
    names = simulation.input_variables
    recorded = list(names)
    simulation.apply_reform(as_reform(apply))
    assert simulation.input_variables is names
    assert names == recorded
    assert simulation.calculate(SCOPED, AWARD_YEAR).tolist() == [100]


def test_a_branchs_reform_keeps_what_it_stores_after_its_parent_applies_one():
    # A reform applied to a simulation rebuilds its branches' records too.
    parent = built()
    branch = parent.get_branch("reformed")

    def apply(reform):
        parent.apply_reform(as_reform(lambda _: None))
        reform.simulation.set_input(SCOPED, AWARD_YEAR, [0])

    branch.apply_reform(as_reform(apply))
    assert SCOPED in branch.input_variables
    assert SCOPED not in parent.input_variables
    branch.reset_calculations()
    assert branch.calculate(SCOPED, AWARD_YEAR).tolist() == [0]


def test_a_record_copied_while_a_reform_runs_is_a_plain_set():
    copies = []

    def apply(reform):
        simulation = reform.simulation
        simulation.set_input(SCOPED, AWARD_YEAR, [0])
        keys = simulation._user_input_keys
        copies.extend(
            [copy.copy(keys), copy.deepcopy(keys), pickle.loads(pickle.dumps(keys))]
        )

    simulation = built()
    simulation.apply_reform(as_reform(apply))
    assert SCOPED in simulation.input_variables
    for keys in copies:
        assert type(keys) is set
        assert (SCOPED, "default", period(AWARD_YEAR)) in keys


def test_a_reform_that_raises_leaves_the_record_as_it_was():
    def apply(reform):
        reform.simulation.set_input(SCOPED, AWARD_YEAR, [0])
        raise ValueError("raised by the reform")

    simulation = built()
    recorded = list(simulation.input_variables)
    with pytest.raises(ValueError, match="raised by the reform"):
        simulation.apply_reform(as_reform(apply))
    # A failed reform names nothing, and logs nothing afterwards.
    assert simulation.input_variables == recorded
    assert type(simulation._user_input_keys) is set
    assert simulation.tax_benefit_system.simulation is simulation
    simulation.set_input(SCOPED, AWARD_YEAR, [5])
    assert simulation.calculate(SCOPED, AWARD_YEAR).tolist() == [5]


# Property: drawn inputs set since the build, then a reform that sets and
# deletes inputs by any route. The reform names exactly the variables it
# leaves an input of its own for. A reset keeps every input of those
# variables (its own, and any set since the build that it left in place),
# and every variable it does not name recalculates as if nothing had been
# set since the build.
VARIABLES = [SCOPED, "claimant_or_partner_jsa_income"]
YEARS = [AWARD_YEAR - 1, AWARD_YEAR, AWARD_YEAR + 1]
ROUTES = ["simulation", "holder", "thread", "delete"]
EARLIER = 7


@cache
def base():
    return Simulation(situation=SITUATION)


def write(simulation, route, variable, year, value):
    if route == "simulation":
        simulation.set_input(variable, year, [value])
    elif route == "holder":
        holder = simulation.get_holder(variable)
        holder.set_input(period(year), [value], simulation.branch_name)
    elif route == "thread":
        worker = threading.Thread(
            target=simulation.set_input, args=(variable, year, [value])
        )
        worker.start()
        worker.join()
    else:
        simulation.delete_arrays(variable, year)


cells = st.tuples(st.sampled_from(VARIABLES), st.sampled_from(YEARS))


@settings(
    max_examples=20,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow],
)
@given(
    st.sets(cells),
    st.lists(st.tuples(st.sampled_from(ROUTES), cells), max_size=6),
)
def test_a_reform_names_exactly_the_variables_it_leaves_inputs_for(earlier, operations):
    parent = base()
    names = parent.input_variables
    recorded = list(names)
    simulation = parent.clone()
    for variable, year in earlier:
        simulation.set_input(variable, year, [EARLIER])
    # The inputs left after the reform, by variable and year: those set since
    # the build, then each write replacing and each deletion removing one.
    left = dict.fromkeys(earlier, EARLIER)
    for value, (route, (variable, year)) in enumerate(operations, start=100):
        if route == "delete":
            left.pop((variable, year), None)
        else:
            left[(variable, year)] = value

    def apply(reform):
        for value, (route, (variable, year)) in enumerate(operations, start=100):
            write(reform.simulation, route, variable, year, value)

    simulation.apply_reform(as_reform(apply))
    named = {variable for (variable, _), value in left.items() if value != EARLIER}
    assert simulation.input_variables == recorded + sorted(named)
    assert parent.input_variables is names
    assert names == recorded
    simulation.reset_calculations()
    for (variable, year), value in left.items():
        if variable in named:
            assert simulation.calculate(variable, year).tolist() == [value]
    pristine = parent.clone()
    for variable in set(VARIABLES) - named:
        for year in YEARS:
            np.testing.assert_array_equal(
                simulation.calculate(variable, year),
                pristine.calculate(variable, year),
                err_msg=f"{variable} {year}",
            )
