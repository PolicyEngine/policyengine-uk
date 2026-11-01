"""An input set for an earlier year reaches a year already grown (#2774).

For a year an input variable holds no input for, Core grows the latest earlier
input by the variable's ``uprating`` index, or carries the latest input over,
and caches the result in the variable's holder. Simulation grows a stored
household total the same way. An input set afterwards for a year in between
changes what that year should be. On a named branch Core drops the values that
may depend on the input. On the default branch Simulation drops what it
calculated before its next calculation (``drop_calculated_values``), and keeps
only the years Core records as supplied, through the data or ``set_input``, of
each input variable.

Invariants, for any amounts and any order of inputs and calculations:

- the default branch, a named branch and a new simulation given the same inputs
  give the same value for every input variable in every year;
- every year the data, a caller or a scenario's modifier supplied keeps the
  value supplied, whether it comes before or after a year set later;
- a branch keeps the values it held when it was created when its parent
  changes.
"""

import numpy as np
import pandas as pd
import pytest
from hypothesis import example, given, settings
from hypothesis import strategies as st
from policyengine_core.periods import period
from policyengine_core.simulations.simulation import _uprating_index_value

from policyengine_uk import Simulation
from policyengine_uk.data.dataset_schema import UKSingleYearDataset
from policyengine_uk.data.economic_assumptions import PROJECTION_END_YEAR
from policyengine_uk.scenarios import no_economic_assumptions
from policyengine_uk.utils.scenario import Scenario

pytestmark = pytest.mark.usefixtures("cloned_uk_tax_benefit_system")

DATA_YEAR = 2025
LAST_YEAR = 2040
YEARS = range(DATA_YEAR, LAST_YEAR + 1)
# A person balance grown by GDP per capita, a person income the uprating map
# grows by the private pension index, and a person input with no index, which
# Core carries over flat.
VARIABLES = ("cash_isa_balance", "private_pension_income", "car_list_price")
PROPERTY_SETTINGS = settings(
    max_examples=6,
    deadline=None,
    derandomize=True,
    database=None,
)


def _frame(**columns):
    """One person, with a ``name__year`` column for each value given."""
    return pd.DataFrame(
        {
            f"{name}__{DATA_YEAR}": [value]
            for name, value in (
                ("person_id", 1),
                ("person_benunit_id", 1),
                ("person_household_id", 1),
            )
        }
        | {name: [value] for name, value in columns.items()}
    )


def _growth(simulation, name, year, base):
    """The factor Core grows ``name`` by from ``base`` to ``year``."""
    parameters = simulation.tax_benefit_system.parameters
    index = parameters.get_child(simulation.tax_benefit_system.variables[name].uprating)
    return _uprating_index_value(index, period(year).start) / _uprating_index_value(
        index, period(base).start
    )


# Each row of the issue: the variables, then each one's value in 2035 grown
# from £3,000 in 2025, and grown from £10,000 in 2030. savings_interest_income
# depends on the ISA balances, so it has a simulation of its own.
ISSUE_ROWS = {
    "balances": {
        "cash_isa_balance": (4_197.81, 11_773.88),
        "savings": (4_197.81, 11_773.88),
    },
    "savings interest": {"savings_interest_income": (4_288.88, 11_773.92)},
}


@pytest.mark.parametrize("row", ISSUE_ROWS)
def test_an_input_set_for_an_earlier_year_reaches_a_year_already_grown(row):
    # The issue's reproduction: the data supply £3,000 for 2025. Each path
    # grows it to 2035, then gets £10,000 for 2030, and grows that instead,
    # as a new simulation given both inputs does. A branch made before the
    # input keeps the value its parent held then.
    expected = ISSUE_ROWS[row]
    simulation = Simulation(
        dataset=_frame(**{f"{name}__{DATA_YEAR}": 3_000.0 for name in expected})
    )
    named = simulation.get_branch("edited")
    untouched = simulation.get_branch("untouched")
    for name, (grown, _) in expected.items():
        for path in (simulation, named, untouched):
            assert path.calculate(name, 2035)[0] == pytest.approx(grown, abs=0.005)
            assert path.calculate(name, 2035)[0] == pytest.approx(
                3_000 * _growth(simulation, name, 2035, DATA_YEAR), rel=1e-6
            )
    for name in expected:
        for path in (simulation, named):
            path.set_input(name, 2030, np.array([10_000.0]))
    new = Simulation(
        dataset=_frame(
            **{f"{name}__{DATA_YEAR}": 3_000.0 for name in expected},
            **{f"{name}__2030": 10_000.0 for name in expected},
        )
    )
    for name, (grown, regrown) in expected.items():
        values = [path.calculate(name, 2035)[0] for path in (simulation, named, new)]
        assert values == [values[-1]] * 3, name
        assert values[-1] == pytest.approx(regrown, abs=0.005)
        assert values[-1] == pytest.approx(
            10_000 * _growth(simulation, name, 2035, 2030), rel=1e-6
        )
        assert untouched.calculate(name, 2035)[0] == pytest.approx(grown, abs=0.005)
        for path in (simulation, named):
            assert path.calculate(name, DATA_YEAR)[0] == 3_000
            assert path.calculate(name, 2030)[0] == 10_000


def _two_adults_with_a_stored_cash_isa():
    return UKSingleYearDataset(
        person=pd.DataFrame(
            {
                "person_id": [1, 2],
                "person_benunit_id": [1, 1],
                "person_household_id": [1, 1],
                "age": [30, 28],
            }
        ),
        benunit=pd.DataFrame({"benunit_id": [1]}),
        household=pd.DataFrame(
            {
                "household_id": [1],
                "household_weight": [1.0],
                "region": ["LONDON"],
                "tenure_type": ["RENT_PRIVATELY"],
                "cash_isa": [3_000.0],
            }
        ),
        fiscal_year=DATA_YEAR,
    )


def test_a_balance_set_for_an_earlier_year_reaches_a_total_already_summed():
    # The issue's total: the data store cash_isa through PROJECTION_END_YEAR.
    # A balance of £100 for 2034, newer than the stored total, gives cash_isa
    # in 2040 as £117.74. A balance of £200 then set for 2035 gives £227.91
    # on the default branch, as on a named branch and in a simulation given
    # both balances before calculating anything.
    assert PROJECTION_END_YEAR < 2034
    simulation = Simulation(dataset=_two_adults_with_a_stored_cash_isa())
    named = simulation.get_branch("edited")
    new = Simulation(dataset=_two_adults_with_a_stored_cash_isa())
    for path in (simulation, named, new):
        path.set_input("cash_isa_balance", 2034, np.array([100.0, 0.0]))
    for path in (simulation, named):
        assert path.calculate("cash_isa", 2040)[0] == pytest.approx(117.74, abs=0.005)
        path.set_input("cash_isa_balance", 2035, np.array([200.0, 0.0]))
    new.set_input("cash_isa_balance", 2035, np.array([200.0, 0.0]))
    values = [path.calculate("cash_isa", 2040)[0] for path in (simulation, named, new)]
    assert values == [values[-1]] * 3
    assert values[-1] == pytest.approx(227.91, abs=0.005)
    assert values[-1] == pytest.approx(
        200 * _growth(simulation, "cash_isa_balance", 2040, 2035), rel=1e-6
    )
    for path in (simulation, named):
        assert path.calculate("cash_isa", DATA_YEAR)[0] == 3_000


def test_years_the_data_supply_after_a_later_input_keep_their_values():
    # The frame supplies 2025 and 2033. After 2030 and 2035 are grown, an
    # input for 2028 replaces what 2030 grew from, but not 2033, nor 2035,
    # which grows from 2033.
    data = {
        f"cash_isa_balance__{DATA_YEAR}": 3_000.0,
        "cash_isa_balance__2033": 5_000.0,
    }
    simulation = Simulation(dataset=_frame(**data))
    named = simulation.get_branch("edited")
    for path in (simulation, named):
        for year in (2030, 2035):
            path.calculate("cash_isa_balance", year)
        path.set_input("cash_isa_balance", 2028, np.array([10_000.0]))
    new = Simulation(dataset=_frame(**data, cash_isa_balance__2028=10_000.0))
    for year in YEARS:
        values = [
            path.calculate("cash_isa_balance", year)[0]
            for path in (simulation, named, new)
        ]
        assert values == [values[-1]] * 3, year
    for path in (simulation, named):
        assert path.calculate("cash_isa_balance", 2033)[0] == 5_000
        assert path.calculate("cash_isa_balance", 2035)[0] == pytest.approx(
            5_000 * _growth(simulation, "cash_isa_balance", 2035, 2033), rel=1e-6
        )
        assert path.calculate("cash_isa_balance", 2030)[0] == pytest.approx(
            10_000 * _growth(simulation, "cash_isa_balance", 2030, 2028), rel=1e-6
        )


def test_years_a_dataset_projects_under_a_reform_before_data_load_stay():
    # no_economic_assumptions applies before data load, so the dataset holds
    # cash_isa flat at £3,000 in each year it projects, through
    # PROJECTION_END_YEAR. A balance set after a calculation for the first of
    # those years replaces none of the others.
    simulation = Simulation(
        scenario=no_economic_assumptions,
        dataset=_two_adults_with_a_stored_cash_isa(),
    )
    later = PROJECTION_END_YEAR + 3
    assert simulation.calculate("cash_isa", later)[0] == 3_000
    simulation.set_input("cash_isa", DATA_YEAR + 1, np.array([10_000.0]))
    assert simulation.calculate("cash_isa", DATA_YEAR + 1)[0] == 10_000
    for year in range(DATA_YEAR + 2, PROJECTION_END_YEAR + 1):
        assert simulation.calculate("cash_isa", year)[0] == 3_000, year
    assert simulation.calculate("cash_isa", later)[0] == 3_000


def _sets_a_later_balance(simulation):
    simulation.set_input("cash_isa_balance", 2038, np.array([7_000.0]))


@pytest.mark.parametrize("route", ["modifier", "simulation", "holder"])
def test_a_year_set_for_later_than_a_later_input_keeps_its_value(route):
    # A scenario's modifier, which runs once the data are built, or a caller,
    # through the simulation or straight through the holder, sets £7,000 for
    # 2038 before anything is calculated. After 2040 is grown from it, an
    # input for 2030 replaces only the years before 2038.
    data = _frame(**{f"cash_isa_balance__{DATA_YEAR}": 3_000.0})
    if route == "modifier":
        simulation = Simulation(
            scenario=Scenario(simulation_modifier=_sets_a_later_balance), dataset=data
        )
    else:
        simulation = Simulation(dataset=data)
        if route == "simulation":
            _sets_a_later_balance(simulation)
        else:
            simulation.get_holder("cash_isa_balance").set_input(
                period(2038), np.array([7_000.0])
            )
    grown = 7_000 * _growth(simulation, "cash_isa_balance", 2040, 2038)
    assert simulation.calculate("cash_isa_balance", 2040)[0] == pytest.approx(
        grown, rel=1e-6
    )
    assert simulation.calculate("cash_isa_balance", 2035)[0] == pytest.approx(
        3_000 * _growth(simulation, "cash_isa_balance", 2035, DATA_YEAR), rel=1e-6
    )
    simulation.set_input("cash_isa_balance", 2030, np.array([10_000.0]))
    assert simulation.calculate("cash_isa_balance", 2035)[0] == pytest.approx(
        10_000 * _growth(simulation, "cash_isa_balance", 2035, 2030), rel=1e-6
    )
    assert simulation.calculate("cash_isa_balance", 2038)[0] == 7_000
    assert simulation.calculate("cash_isa_balance", 2040)[0] == pytest.approx(
        grown, rel=1e-6
    )


def test_a_reset_drops_grown_years_and_keeps_supplied_ones():
    # reset_calculations keeps what the drop before a calculation keeps: the
    # years the data or a caller supplied, here 2025 and 2038, and not the
    # years grown from them.
    simulation = Simulation(
        dataset=_frame(**{f"cash_isa_balance__{DATA_YEAR}": 3_000.0})
    )
    simulation.set_input("cash_isa_balance", 2038, np.array([7_000.0]))
    holder = simulation.get_holder("cash_isa_balance")
    for year in (2035, 2040):
        simulation.calculate("cash_isa_balance", year)
        assert holder.get_array(period(year)) is not None
    simulation.reset_calculations()
    for year in (2035, 2040):
        assert holder.get_array(period(year)) is None
    assert holder.get_array(period(DATA_YEAR))[0] == 3_000
    assert holder.get_array(period(2038))[0] == 7_000


AMOUNTS = st.integers(min_value=0, max_value=5_000_000).map(lambda pence: pence / 100)
LATER_YEARS = st.integers(min_value=DATA_YEAR + 1, max_value=LAST_YEAR)
STEPS = st.lists(
    st.one_of(
        st.tuples(
            st.just("calculate"),
            st.sampled_from(VARIABLES),
            st.integers(min_value=DATA_YEAR, max_value=LAST_YEAR),
        ),
        st.tuples(st.just("set"), st.sampled_from(VARIABLES), LATER_YEARS, AMOUNTS),
    ),
    min_size=1,
    max_size=8,
)
# What the data supply: each variable in 2025, and maybe in one later year.
DATA = st.fixed_dictionaries(
    {
        name: st.tuples(AMOUNTS, st.none() | st.tuples(LATER_YEARS, AMOUNTS))
        for name in VARIABLES
    }
)


@PROPERTY_SETTINGS
@given(data=DATA, steps=STEPS)
@example(
    data={name: (3_000.0, None) for name in VARIABLES},
    steps=[("calculate", name, 2035) for name in VARIABLES]
    + [("set", name, 2030, 10_000.0) for name in VARIABLES],
)
@example(
    data={name: (3_000.0, (2033, 5_000.0)) for name in VARIABLES},
    steps=[
        ("calculate", "private_pension_income", 2040),
        ("set", "private_pension_income", 2028, 10_000.0),
        ("calculate", "car_list_price", 2030),
        ("set", "car_list_price", 2027, 20_000.0),
        ("calculate", "cash_isa_balance", 2036),
        ("set", "cash_isa_balance", 2034, 100.0),
        ("set", "cash_isa_balance", 2035, 200.0),
    ],
)
def test_every_path_gives_what_a_new_simulation_gives(data, steps):
    # The same inputs and calculations, in the same order, on the default
    # branch and on a named branch, made before either: each calculation
    # gives the same value on both, and afterwards every input variable in
    # every year equals what a new simulation built from all the inputs
    # gives. Every supplied year keeps its value.
    columns = {}
    for name, (amount, later) in data.items():
        columns[f"{name}__{DATA_YEAR}"] = amount
        if later is not None:
            columns[f"{name}__{later[0]}"] = later[1]
    simulation = Simulation(dataset=_frame(**columns))
    named = simulation.get_branch("edited")
    for step in steps:
        if step[0] == "calculate":
            _, name, year = step
            default_value = simulation.calculate(name, year)[0]
            assert default_value == named.calculate(name, year)[0], (step, steps)
        else:
            _, name, year, amount = step
            for path in (simulation, named):
                path.set_input(name, year, np.array([amount]))
            columns[f"{name}__{year}"] = amount
    new = Simulation(dataset=_frame(**columns))
    for name in VARIABLES:
        for year in YEARS:
            values = [
                path.calculate(name, year)[0] for path in (simulation, named, new)
            ]
            assert values == [values[-1]] * 3, (name, year, steps)
    for column, amount in columns.items():
        name, year = column.rsplit("__", 1)
        for path in (simulation, named):
            assert path.calculate(name, int(year))[0] == np.float32(amount), column
