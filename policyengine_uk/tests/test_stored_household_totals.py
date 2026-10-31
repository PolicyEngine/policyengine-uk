"""A dataset that stores a household ISA total keeps it in every year (#2740).

cash_isa, stocks_and_shares_isa and household_lifetime_isa_balance sum person
balances, but a dataset can store the household total instead. Up to
PROJECTION_END_YEAR the dataset projection grows a stored total; after it,
Simulation grows the latest stored total by the index of its parts, the index
each variable's documentation projects it with, while the variable still sums
the parts STORED_HOUSEHOLD_TOTALS names and each part reads its inputs. A
dataset that stores only the person balances, or stores them for a later year
than the total, gets their sum, and so does a situation for a year it gives no
total for, and a reform that changes the sum or a part. An input frame is
data, so a total it stores grows too.

Invariants, for any non-negative amounts:

- a stored total stays positive in every year from 2025 to 2040 when it starts
  positive, and from PROJECTION_END_YEAR grows by its declared index;
- with person balances stored instead, the total equals their sum every year;
- the two forms give the same totals and means-test capital when they hold
  the same amounts;
- after any inputs and calculations, a total keeps every value the data or a
  caller supplied, and equals what a fresh calculation gives in other years;
- a grown total grows as Core grows an input with its parts' index;
- a reform that changes the sum or a part gets Core's sum, and a reform that
  declares the same variables again changes nothing.
"""

from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from policyengine_core.parameters import ParameterNode
from policyengine_core.periods import period
from policyengine_core.reforms import Reform
from policyengine_core.simulations import Simulation as CoreSimulation
from policyengine_core.simulations.simulation import _uprating_index_value

from policyengine_uk import Simulation
from policyengine_uk.data.dataset_schema import (
    UKMultiYearDataset,
    UKSingleYearDataset,
)
from policyengine_uk.data.economic_assumptions import (
    PROJECTION_END_YEAR,
    STORED_HOUSEHOLD_TOTALS,
    _uprating_index_map,
    stored_total_uprating,
)
from policyengine_uk.model_api import YEAR, Household, Person, Variable
from policyengine_uk.scenarios import no_economic_assumptions

pytestmark = pytest.mark.usefixtures("cloned_uk_tax_benefit_system")

DATA_YEAR = 2025
YEARS = range(DATA_YEAR, 2041)
CAPITAL_YEARS = (DATA_YEAR, PROJECTION_END_YEAR, PROJECTION_END_YEAR + 1, YEARS[-1])
# Each total, the person balance it sums, and the variable whose index its
# documentation says the model grows it with.
TOTALS = {
    "cash_isa": ("cash_isa_balance", "savings"),
    "stocks_and_shares_isa": ("stocks_and_shares_isa_balance", "corporate_wealth"),
    "household_lifetime_isa_balance": ("lifetime_isa_balance", "lifetime_isa_balance"),
}
MEANS_TEST_CAPITAL = (
    "uc_assessable_capital",
    "housing_benefit_assessable_capital",
    "pension_credit_assessable_capital",
    "income_support_assessable_capital",
    "jsa_income_assessable_capital",
    "esa_income_assessable_capital",
    "council_tax_reduction_assessable_capital",
)
CPI = "gov.economic_assumptions.indices.obr.consumer_price_index"
PROPERTY_SETTINGS = settings(
    max_examples=5,
    deadline=None,
    derandomize=True,
    database=None,
)


def _dataset(households, person_columns=(), household_columns=(), year=DATA_YEAR):
    """Two adults per household, with the named columns from ``households``.

    Each household is a dict of amounts. A person column ``name`` takes
    ``name`` split between the two adults by the household's ``share``.
    """
    people = []
    for index, household in enumerate(households):
        share = household.get("share", 1.0)
        for adult, age in ((0, 30), (1, 28)):
            person = {
                "person_id": 2 * index + adult + 1,
                "person_benunit_id": index + 1,
                "person_household_id": index + 1,
                "age": age,
            }
            for name in person_columns:
                first = round(household[name] * share, 2)
                person[name] = first if adult == 0 else household[name] - first
            people.append(person)
    count = len(households)
    return UKSingleYearDataset(
        person=pd.DataFrame(people),
        benunit=pd.DataFrame({"benunit_id": range(1, count + 1)}),
        household=pd.DataFrame(
            {
                "household_id": range(1, count + 1),
                "household_weight": [1.0] * count,
                "region": ["LONDON"] * count,
                "tenure_type": ["RENT_PRIVATELY"] * count,
                "council_tax": [1_500.0] * count,
                "rent": [12_000.0] * count,
                "savings": [1_000.0] * count,
                **{
                    name: [float(household[name]) for household in households]
                    for name in household_columns
                },
            }
        ),
        fiscal_year=year,
    )


def _values(simulation, name, years=YEARS):
    return {year: simulation.calculate(name, year).astype(float) for year in years}


def _index_growth(simulation, index_name, year, base):
    """Growth from ``base`` to ``year`` by the index ``index_name``."""
    index = simulation.tax_benefit_system.parameters.get_child(index_name)
    return _uprating_index_value(index, period(year).start) / _uprating_index_value(
        index, period(base).start
    )


def _growth(simulation, name, year, base=PROJECTION_END_YEAR):
    """Growth from ``base`` to ``year`` by the index ``name`` declares."""
    index_name = simulation.tax_benefit_system.variables[name].uprating
    return _index_growth(simulation, index_name, year, base)


def _core_sum(simulation, name, year):
    """What Core calculates for ``name`` in ``year`` from its definition."""
    variable = simulation.tax_benefit_system.variables[name]
    population = simulation.get_variable_population(name)
    return CoreSimulation._run_formula(simulation, variable, population, period(year))


def _reform(*changes):
    """A reform that applies each change to the tax-benefit system."""

    class reform(Reform):
        def apply(self):
            for change in changes:
                change(self)

    return reform


def _redeclared(name, **attributes):
    """``name`` as a reform declares it in full, with ``attributes``."""
    from policyengine_uk.system import system

    baseline = system.variables[name]
    return type(
        name,
        (Variable,),
        {
            "value_type": baseline.value_type,
            "entity": Person if baseline.entity.key == "person" else Household,
            "definition_period": baseline.definition_period,
            "label": baseline.label,
            **attributes,
        },
    )


def _updated(name, **attributes):
    """``name`` as a reform updates it, keeping every other attribute."""
    return type(name, (Variable,), attributes)


def test_stored_household_totals_grow_past_the_projection_horizon():
    simulation = Simulation(
        dataset=_dataset(
            [
                {
                    "cash_isa": 3_000.0,
                    "stocks_and_shares_isa": 2_000.0,
                    "household_lifetime_isa_balance": 4_000.0,
                }
            ],
            household_columns=TOTALS,
        )
    )
    capital = _values(simulation, "uc_assessable_capital")
    savings = _values(simulation, "savings")
    for name, (_, projected_with) in TOTALS.items():
        totals = _values(simulation, name)
        for year in YEARS:
            if year <= PROJECTION_END_YEAR:
                continue
            growth = _growth(simulation, projected_with, year)
            assert growth > 1
            assert totals[year][0] == pytest.approx(
                totals[PROJECTION_END_YEAR][0] * growth, rel=1e-6
            )
    # Savings, the cash ISA and the stocks-and-shares ISA (through
    # share_like_capital) make up the capital, each grown alike.
    for year in YEARS:
        assert capital[year][0] == pytest.approx(6 * savings[year][0], rel=1e-5)


@pytest.mark.parametrize(
    "scenario", [None, no_economic_assumptions], ids=["current_law", "no_growth"]
)
def test_stored_totals_project_exactly_like_what_they_are_projected_with(scenario):
    # The dataset stores cash_isa equal to savings, stocks_and_shares_isa to
    # corporate_wealth, and household_lifetime_isa_balance to the one
    # lifetime_isa_balance in the household: Core projects the second of each
    # pair, Simulation the first. Without economic growth both stay flat.
    household = {
        "cash_isa": 1_000.0,
        "stocks_and_shares_isa": 2_345.67,
        "corporate_wealth": 2_345.67,
        "household_lifetime_isa_balance": 4_321.09,
        "lifetime_isa_balance": 4_321.09,
    }
    simulation = Simulation(
        scenario=scenario,
        dataset=_dataset(
            [household],
            person_columns=["lifetime_isa_balance"],
            household_columns=[
                "cash_isa",
                "stocks_and_shares_isa",
                "corporate_wealth",
                "household_lifetime_isa_balance",
            ],
        ),
    )
    for name, other in (
        ("cash_isa", "savings"),
        ("stocks_and_shares_isa", "corporate_wealth"),
        ("household_lifetime_isa_balance", "lifetime_isa_balance"),
    ):
        for year in YEARS:
            total = simulation.calculate(name, year)
            assert total.sum() == simulation.calculate(other, year).sum(), (name, year)
    # So the stocks-and-shares ISA stays within corporate_wealth.
    for year in YEARS:
        share_like = simulation.calculate("share_like_capital", year)
        assert share_like[0] == simulation.calculate("corporate_wealth", year)[0]


@pytest.mark.parametrize(
    "index", [None, CPI, "parts"], ids=["no_index", "cpi", "parts_index"]
)
def test_a_grown_total_grows_as_core_grows_its_part(index):
    # The data store a total and the balance it sums for the same year, so
    # the total takes precedence and grows by the balance's index, while Core
    # grows the balance itself. A reform can give the balance another index,
    # or none, when Core carries the balance flat and the total stays flat.
    part = "cash_isa_balance"
    reform = None
    if index != "parts":
        reform = _reform(
            lambda system: system.replace_variable(
                _redeclared(part, uprating=index, default_value=0)
            )
        )
    simulation = Simulation(
        reform=reform,
        dataset=_dataset(
            [{"cash_isa": 1_000.0, part: 1_000.0, "share": 0.3}],
            person_columns=[part],
            household_columns=["cash_isa"],
        ),
    )
    if index != "parts":
        assert simulation.tax_benefit_system.variables[part].uprating == index
    for year in YEARS:
        balances = simulation.calculate(part, year)
        assert simulation.calculate("cash_isa", year)[0] == pytest.approx(
            balances.sum(), rel=1e-6
        ), year
    later = simulation.calculate("cash_isa", YEARS[-1])[0]
    horizon = simulation.calculate("cash_isa", PROJECTION_END_YEAR)[0]
    if index is None:
        assert later == horizon
    else:
        assert later > horizon


def test_person_balances_still_sum_without_a_stored_total():
    simulation = Simulation(
        dataset=_dataset(
            [
                {
                    "cash_isa_balance": 3_000.0,
                    "stocks_and_shares_isa_balance": 2_000.0,
                    "lifetime_isa_balance": 4_000.0,
                    "share": 0.25,
                }
            ],
            person_columns=[part for part, _ in TOTALS.values()],
        )
    )
    for name, (part, _) in TOTALS.items():
        for year in YEARS:
            balances = simulation.calculate(part, year)
            assert balances[0] > 0 and balances[1] > 0
            assert simulation.calculate(name, year)[0] == pytest.approx(
                balances.sum(), rel=1e-6
            )


def test_a_stored_zero_total_takes_precedence_over_same_year_balances():
    # A total of zero is an observation, as in the years the data hold: it
    # stays zero beside positive balances stored for the same year, in a
    # household on its own and beside one with a positive total.
    zero = {"cash_isa": 0.0, "cash_isa_balance": 1_000.0, "share": 0.5}
    positive = {"cash_isa": 2_000.0, "cash_isa_balance": 500.0, "share": 0.5}
    for households in ([zero], [zero, positive]):
        simulation = Simulation(
            dataset=_dataset(
                households,
                person_columns=["cash_isa_balance"],
                household_columns=["cash_isa"],
            )
        )
        for year in CAPITAL_YEARS:
            totals = simulation.calculate("cash_isa", year)
            assert totals[0] == 0, year
            assert simulation.calculate("cash_isa_balance", year)[:2].sum() > 0
            if len(households) == 2:
                savings = simulation.calculate("savings", year)[1]
                assert totals[1] == pytest.approx(2 * savings, rel=1e-6), year


def test_a_situation_total_is_used_only_for_the_year_it_is_given_for():
    simulation = Simulation(
        situation={
            "people": {
                "adult": {
                    "age": {DATA_YEAR: 40},
                    "cash_isa_balance": {DATA_YEAR: 3_000},
                }
            },
            "benunits": {"benunit": {"members": ["adult"]}},
            "households": {
                "household": {
                    "members": ["adult"],
                    "cash_isa": {DATA_YEAR: 7_000},
                }
            },
        }
    )
    assert simulation.calculate("cash_isa", DATA_YEAR)[0] == 7_000
    for year in (DATA_YEAR + 1, PROJECTION_END_YEAR + 1):
        balance = simulation.calculate("cash_isa_balance", year)[0]
        assert balance > 3_000
        assert simulation.calculate("cash_isa", year)[0] == balance


def test_a_total_set_on_a_branch_replaces_the_one_a_later_year_grew_from():
    # Like savings, which Core uprates, a grown total depends on which years
    # hold a total, so a total set on a branch for a year in between reaches
    # a later year the branch has already calculated.
    simulation = Simulation(
        dataset=_dataset([{"cash_isa": 3_000.0}], household_columns=["cash_isa"])
    )
    branch = simulation.get_branch("edited")
    between, later = PROJECTION_END_YEAR + 1, PROJECTION_END_YEAR + 3
    for name in ("cash_isa", "savings"):
        assert branch.calculate(name, later)[0] > 0
        branch.set_input(name, between, np.array([10_000.0]))
    growth = _growth(simulation, "savings", later, base=between)
    for name in ("cash_isa", "savings"):
        assert branch.calculate(name, later)[0] == pytest.approx(
            10_000 * growth, rel=1e-6
        )
    assert simulation.calculate("cash_isa", later)[0] == pytest.approx(
        3 * simulation.calculate("savings", later)[0], rel=1e-6
    )


def _one_person_frame(**columns):
    return pd.DataFrame(
        {
            "person_id__2025": [1],
            "person_benunit_id__2025": [1],
            "person_household_id__2025": [1],
            **{name: [amount] for name, amount in columns.items()},
        }
    )


@pytest.mark.parametrize("branch", [None, "edited"], ids=["default", "named"])
def test_a_total_set_for_another_year_replaces_a_grown_total_already_calculated(
    branch,
):
    # The data supply a total for 2025 only. A simulation that has grown it
    # to 2035, then gets a total for 2030, grows that one instead; and one
    # that has grown the 2030 total to 2037, then gets a total for 2036,
    # grows that. The supplied totals keep their values.
    simulation = Simulation(dataset=_one_person_frame(cash_isa__2025=3_000.0))
    target = simulation if branch is None else simulation.get_branch(branch)
    assert target.calculate("cash_isa", 2035)[0] == pytest.approx(
        3_000 * _growth(simulation, "savings", 2035, base=2025), rel=1e-6
    )
    target.set_input("cash_isa", 2030, np.array([10_000.0]))
    assert target.calculate("cash_isa", 2035)[0] == pytest.approx(
        10_000 * _growth(simulation, "savings", 2035, base=2030), rel=1e-6
    )
    assert target.calculate("cash_isa", 2037)[0] == pytest.approx(
        10_000 * _growth(simulation, "savings", 2037, base=2030), rel=1e-6
    )
    target.set_input("cash_isa", 2036, np.array([20_000.0]))
    assert target.calculate("cash_isa", 2037)[0] == pytest.approx(
        20_000 * _growth(simulation, "savings", 2037, base=2036), rel=1e-6
    )
    for year, amount in ((2025, 3_000), (2030, 10_000), (2036, 20_000)):
        assert target.calculate("cash_isa", year)[0] == amount


@pytest.mark.parametrize("branch", [None, "balances"], ids=["default", "named"])
def test_balances_set_after_a_grown_total_replace_it(branch):
    # A grown total reads none of the person balances, so a balance set for a
    # later year than the stored total must still reach a year the
    # simulation has already calculated.
    simulation = Simulation(
        dataset=_dataset([{"cash_isa": 3_000.0}], household_columns=["cash_isa"])
    )
    target = simulation if branch is None else simulation.get_branch(branch)
    between, later = PROJECTION_END_YEAR + 1, PROJECTION_END_YEAR + 3
    grown = target.calculate("cash_isa", later)[0]
    assert grown > 3_000
    target.set_input("cash_isa_balance", between, np.array([600.0, 400.0]))
    growth = _growth(simulation, "cash_isa_balance", later, base=between)
    assert target.calculate("cash_isa", later)[0] == pytest.approx(
        1_000 * growth, rel=1e-6
    )
    if branch is not None:
        assert simulation.calculate("cash_isa", later)[0] == pytest.approx(
            grown, rel=1e-6
        )


def test_a_grown_total_records_what_it_depends_on():
    # Inside a calculation, an input set on a branch reaches the values the
    # branch holds only through Core's records of what each depends on. A
    # grown total depends on the total and on its parts in every other year.
    simulation = Simulation(
        dataset=_dataset([{"cash_isa": 3_000.0}], household_columns=["cash_isa"])
    )
    branch = simulation.get_branch("recorded")
    later = PROJECTION_END_YEAR + 3
    branch.calculate("cash_isa", later)
    grown = branch.get_holder("cash_isa")._stored_sequence_number(
        period(later), "recorded"
    )
    history = branch._get_store_history()
    for name in ("cash_isa", "cash_isa_balance"):
        since = history.earliest_dependency(name, period(later - 1))
        assert since is not None and since <= grown, name


def test_resets_drop_grown_totals_and_keep_supplied_ones():
    # A stored total counts as an input by name, but the simulation
    # calculates it for the years the data do not hold. Resetting the
    # calculations deletes those years and keeps every supplied one.
    simulation = Simulation(
        dataset=_dataset([{"cash_isa": 3_000.0}], household_columns=["cash_isa"])
    )
    holder = simulation.get_holder("cash_isa")
    supplied = {year: holder.get_array(period(year)) for year in YEARS}
    assert all(supplied[year] is not None for year in range(DATA_YEAR, 2033))
    later = PROJECTION_END_YEAR + 3
    simulation.calculate("cash_isa", later)
    assert holder.get_array(period(later)) is not None
    simulation.reset_calculations()
    assert holder.get_array(period(later)) is None
    for year in range(DATA_YEAR, PROJECTION_END_YEAR + 1):
        assert holder.get_array(period(year)) == pytest.approx(supplied[year])
    assert holder.get_array(period(DATA_YEAR))[0] == 3_000


def test_person_balances_stored_after_the_total_are_summed_instead():
    # A total and balances that a dataset stores for the same year: the total
    # takes precedence, and grows. Balances stored for later years than the
    # total are the newer observation, so their sum stands.
    def year(columns, person_columns=(), share=0.25, year=DATA_YEAR):
        return _dataset(
            [{**columns, "share": share}],
            person_columns=person_columns,
            household_columns=[name for name in columns if name == "cash_isa"],
            year=year,
        )

    simulation = Simulation(
        dataset=UKMultiYearDataset(
            datasets=[
                year(
                    {"cash_isa": 5_000.0, "cash_isa_balance": 400.0},
                    ["cash_isa_balance"],
                ),
                year({"cash_isa_balance": 600.0}, ["cash_isa_balance"], year=2026),
                year({"cash_isa_balance": 800.0}, ["cash_isa_balance"], year=2027),
            ]
        )
    )
    assert simulation.calculate("cash_isa", DATA_YEAR)[0] == 5_000
    assert simulation.calculate("cash_isa", 2026)[0] == pytest.approx(600)
    assert simulation.calculate("cash_isa", 2027)[0] == pytest.approx(800)
    balances = simulation.calculate("cash_isa_balance", 2028)
    assert balances.sum() > 800
    assert simulation.calculate("cash_isa", 2028)[0] == pytest.approx(
        balances.sum(), rel=1e-6
    )

    same_year = Simulation(
        dataset=UKMultiYearDataset(
            datasets=[
                year(
                    {"cash_isa": 5_000.0, "cash_isa_balance": 400.0},
                    ["cash_isa_balance"],
                ),
            ]
        )
    )
    growth = _growth(same_year, "savings", 2026, base=DATA_YEAR)
    assert same_year.calculate("cash_isa", 2026)[0] == pytest.approx(
        5_000 * growth, rel=1e-6
    )


def test_a_total_stored_in_an_input_frame_grows_like_savings():
    # An input frame is data: a total it stores grows into later years, as a
    # total in a situation does not.
    frame = pd.DataFrame(
        {
            "person_id__2025": [1, 2],
            "person_benunit_id__2025": [1, 1],
            "person_household_id__2025": [1, 1],
            "age__2025": [30, 28],
            "savings__2025": [1_000.0, 1_000.0],
            "cash_isa__2025": [3_000.0, 3_000.0],
        }
    )
    simulation = Simulation(dataset=frame)
    for year in (DATA_YEAR + 1, PROJECTION_END_YEAR + 1):
        savings = simulation.calculate("savings", year)[0]
        assert savings > 1_000
        assert simulation.calculate("cash_isa", year)[0] == pytest.approx(
            3 * savings, rel=1e-6
        )


def _twice_savings(household, period, parameters):
    return 2 * household("savings", period)


def _a_fixed_balance(person, period, parameters):
    return person.filled_array(123.0)


def _add_parameters(system):
    system.parameters.add_child(
        "stored_totals_test",
        ParameterNode(
            "stored_totals_test",
            data={
                "parts": {"values": {"2000-01-01": ["cash_isa_balance"]}},
                "extra": {"values": {"2000-01-01": 100}},
            },
        ),
    )


class other_isa_holdings(Variable):
    value_type = float
    entity = Person
    label = "other ISA holdings"
    definition_period = YEAR


# Changes to what cash_isa sums, and to stocks_and_shares_isa_balance, the
# part stocks_and_shares_isa sums. Each pair runs in one simulation.
SUM_CHANGES = {
    "a_formula": lambda system: system.update_variable(
        _updated("cash_isa", formula=_twice_savings)
    ),
    "a_parameter_list": lambda system: system.update_variable(
        _updated("cash_isa", adds="stored_totals_test.parts")
    ),
    "a_parameter_among_the_parts": lambda system: system.update_variable(
        _updated("cash_isa", adds=["cash_isa_balance", "stored_totals_test.extra"])
    ),
    "a_part_with_no_index": lambda system: system.update_variable(
        _updated("cash_isa", adds=["cash_isa_balance", "other_isa_holdings"])
    ),
    "a_subtraction": lambda system: system.update_variable(
        _updated("cash_isa", subtracts=["other_isa_holdings"])
    ),
    "an_extra_part": lambda system: system.update_variable(
        _updated("cash_isa", adds=["cash_isa_balance", "stocks_and_shares_isa_balance"])
    ),
    "the_part_twice": lambda system: system.update_variable(
        _updated("cash_isa", adds=["cash_isa_balance", "cash_isa_balance"])
    ),
    "another_part": lambda system: system.update_variable(
        _updated("cash_isa", adds=["stocks_and_shares_isa_balance"])
    ),
}
PART = "stocks_and_shares_isa_balance"
PART_CHANGES = {
    "a_formula": lambda system: system.replace_variable(
        _redeclared(PART, formula=_a_fixed_balance)
    ),
    "a_sum": lambda system: system.replace_variable(
        _redeclared(PART, adds=["cash_isa_balance"])
    ),
    "a_subtraction": lambda system: system.replace_variable(
        _redeclared(PART, subtracts=["cash_isa_balance"])
    ),
    "a_mask": lambda system: system.update_variable(
        _updated(PART, defined_for="is_child")
    ),
    "neutralization": lambda system: system.neutralize_variable(PART),
}
CHANGE_PAIRS = [
    (sum_change, list(PART_CHANGES)[index % len(PART_CHANGES)])
    for index, sum_change in enumerate(SUM_CHANGES)
]


@pytest.mark.parametrize(
    "sum_change, part_change",
    CHANGE_PAIRS,
    ids=[f"sum_{total}-part_{part}" for total, part in CHANGE_PAIRS],
)
def test_core_sums_a_total_whose_sum_or_part_a_reform_changes(sum_change, part_change):
    # A stored total stands for the sum of exactly the parts
    # STORED_HOUSEHOLD_TOTALS names, each a plain input. A reform that sums
    # anything else, or that calculates, masks or neutralizes a part, gets
    # Core's own calculation in each year the data hold no total, as on data
    # that store no total. Years the data hold keep the stored total.
    reform = _reform(
        _add_parameters,
        lambda system: system.add_variable(other_isa_holdings),
        SUM_CHANGES[sum_change],
        PART_CHANGES[part_change],
    )
    household = {
        "cash_isa": 5_000.0,
        "stocks_and_shares_isa": 7_000.0,
        "cash_isa_balance": 400.0,
        "stocks_and_shares_isa_balance": 1_000.0,
        "share": 0.25,
    }
    simulation = Simulation(
        reform=reform,
        dataset=_dataset(
            [household],
            person_columns=["cash_isa_balance", "stocks_and_shares_isa_balance"],
            household_columns=["cash_isa", "stocks_and_shares_isa"],
        ),
    )
    for name in ("cash_isa", "stocks_and_shares_isa"):
        stored = simulation.calculate(name, PROJECTION_END_YEAR)[0]
        assert stored > household[name]
        assert stored == simulation.baseline.calculate(name, PROJECTION_END_YEAR)[0]
        for year in (PROJECTION_END_YEAR + 1, YEARS[-1]):
            total = simulation.calculate(name, year)[0]
            assert total == pytest.approx(
                _core_sum(simulation, name, year)[0], rel=1e-6, abs=1e-6
            ), (name, year)
            grown = stored * _growth(simulation, "savings", year)
            assert total != pytest.approx(grown, rel=1e-3), (name, year)


def test_a_part_formula_takes_over_from_the_year_it_starts():
    # Until its formula starts, the part reads its inputs, so the stored
    # total stands; a part with no index holds it flat, as Core holds the
    # part. From the formula's first year, Core sums the parts.
    reform = _reform(
        lambda system: system.replace_variable(
            _redeclared(
                "cash_isa_balance",
                default_value=0,
                formula_2034=_a_fixed_balance,
            )
        )
    )
    simulation = Simulation(
        reform=reform,
        dataset=_dataset([{"cash_isa": 3_000.0}], household_columns=["cash_isa"]),
    )
    horizon = simulation.calculate("cash_isa", PROJECTION_END_YEAR)[0]
    assert horizon > 3_000
    assert simulation.calculate("cash_isa", 2033)[0] == horizon
    for year in (2034, YEARS[-1]):
        assert simulation.calculate("cash_isa", year)[0] == pytest.approx(246)


@pytest.mark.parametrize("method", ["replace", "update"])
def test_reforms_that_declare_a_total_and_its_part_again_change_nothing(method):
    from policyengine_uk.system import system as baseline_system

    def declare_again(system):
        for total, parts in STORED_HOUSEHOLD_TOTALS.items():
            for name in (total, *parts):
                if method == "replace":
                    system.replace_variable(type(baseline_system.variables[name]))
                else:
                    system.update_variable(_updated(name))

    households = [
        {
            "cash_isa": 3_000.0,
            "stocks_and_shares_isa": 2_000.0,
            "household_lifetime_isa_balance": 900.0,
            "lifetime_isa_balance": 900.0,
            "share": 0.5,
        },
        {
            "cash_isa": 0.0,
            "stocks_and_shares_isa": 8_000.0,
            "household_lifetime_isa_balance": 0.0,
            "lifetime_isa_balance": 0.0,
            "share": 1.0,
        },
    ]
    data = dict(
        households=households,
        person_columns=["lifetime_isa_balance"],
        household_columns=TOTALS,
    )
    baseline = Simulation(dataset=_dataset(**data))
    reformed = Simulation(reform=_reform(declare_again), dataset=_dataset(**data))
    for name in TOTALS:
        for year in YEARS:
            assert (
                reformed.calculate(name, year) == baseline.calculate(name, year)
            ).all(), (name, year)
    for year in CAPITAL_YEARS:
        assert (
            reformed.calculate("uc_assessable_capital", year)
            == baseline.calculate("uc_assessable_capital", year)
        ).all(), year


class other_gdp_holdings(Variable):
    value_type = float
    entity = Person
    label = "other holdings that grow with GDP per capita"
    definition_period = YEAR
    uprating = "gov.economic_assumptions.indices.obr.per_capita.gdp"


def test_a_total_of_several_parts_grows_only_by_an_index_they_share(monkeypatch):
    # A total can stand for several parts. It grows by their index when they
    # share one; parts that grow by different indices give it none, so Core
    # sums them.
    import policyengine_uk.simulation as uk_simulation

    parts = {
        "cash_isa": ["cash_isa_balance", "other_isa_holdings"],
        "stocks_and_shares_isa": [
            "stocks_and_shares_isa_balance",
            "other_gdp_holdings",
        ],
    }
    monkeypatch.setattr(
        uk_simulation,
        "STORED_HOUSEHOLD_TOTALS",
        {
            **STORED_HOUSEHOLD_TOTALS,
            **{name: frozenset(names) for name, names in parts.items()},
        },
    )
    reform = _reform(
        lambda system: system.add_variable(other_isa_holdings),
        lambda system: system.add_variable(other_gdp_holdings),
        *(
            lambda system, name=name, names=names: system.update_variable(
                _updated(name, adds=names)
            )
            for name, names in parts.items()
        ),
    )
    simulation = Simulation(
        reform=reform,
        dataset=_dataset(
            [{"cash_isa": 5_000.0, "stocks_and_shares_isa": 7_000.0}],
            household_columns=parts,
        ),
    )
    later = PROJECTION_END_YEAR + 1
    assert simulation.calculate("cash_isa", later)[0] == 0
    assert simulation.calculate("stocks_and_shares_isa", later)[0] == pytest.approx(
        7_000 * _growth(simulation, "savings", later, base=DATA_YEAR), rel=1e-6
    )


def test_parts_with_different_indices_give_a_total_no_index():
    variables = {
        "total": SimpleNamespace(adds=["first", "second"]),
        "first": SimpleNamespace(uprating="gov.economic_assumptions.indices.a"),
        "second": SimpleNamespace(uprating=None),
    }
    with pytest.raises(ValueError, match="different uprating indices"):
        stored_total_uprating(SimpleNamespace(variables=variables), "total")


def test_stored_totals_name_the_parts_their_variables_sum():
    # A stored total grows only while its variable sums exactly these parts,
    # so the two must not drift apart.
    from policyengine_uk.system import system

    for name, parts in STORED_HOUSEHOLD_TOTALS.items():
        adds = system.variables[name].adds
        assert isinstance(adds, list) and len(adds) == len(parts), name
        assert set(adds) == parts, name
        for part in parts:
            assert system.variables[part].is_input_variable(), part


def test_stored_totals_grow_by_the_index_they_are_projected_with():
    from policyengine_uk.system import system

    for name, (part, projected_with) in TOTALS.items():
        assert STORED_HOUSEHOLD_TOTALS[name] == {part}
        index = system.variables[projected_with].uprating
        assert index is not None
        assert stored_total_uprating(system, name) == index


def test_every_projected_household_sum_of_uprated_inputs_is_a_stored_total():
    # A total listed for dataset projection whose parts Core uprates must keep
    # a stored value past PROJECTION_END_YEAR too.
    from policyengine_uk.system import system

    listed = {name for names in _uprating_index_map().values() for name in names}
    sums_of_uprated_inputs = {
        name
        for name in listed
        if isinstance(system.variables[name].adds, list)
        and not system.variables[name].formulas
        and all(
            system.variables[part].is_input_variable()
            and system.variables[part].uprating is not None
            for part in system.variables[name].adds
        )
    }
    assert sums_of_uprated_inputs == set(STORED_HOUSEHOLD_TOTALS)


AMOUNTS = st.integers(min_value=0, max_value=200_000_000).map(lambda p: p / 100)
HOUSEHOLDS = st.lists(
    st.fixed_dictionaries(
        {
            "cash_isa": AMOUNTS,
            "stocks_and_shares_isa": AMOUNTS,
            "household_lifetime_isa_balance": AMOUNTS,
            "share": st.sampled_from([0.0, 0.3, 0.5, 1.0]),
        }
    ),
    min_size=1,
    max_size=6,
)


@PROPERTY_SETTINGS
@given(households=HOUSEHOLDS)
def test_stored_totals_and_person_balances_agree_in_every_year(households):
    # The totals-only dataset stores the three household totals; it also
    # stores the Lifetime ISA balances, which the means tests read from the
    # person. The balances-only dataset stores the same amounts per person.
    households = [
        {**household, **{part: household[name] for name, (part, _) in TOTALS.items()}}
        for household in households
    ]
    totals_only = Simulation(
        dataset=_dataset(
            households,
            person_columns=["lifetime_isa_balance"],
            household_columns=TOTALS,
        )
    )
    balances_only = Simulation(
        dataset=_dataset(
            households, person_columns=[part for part, _ in TOTALS.values()]
        )
    )
    members = balances_only.calculate("person_household_id", DATA_YEAR)
    for name, (part, projected_with) in TOTALS.items():
        stored = np.array([household[name] for household in households])
        totals = _values(totals_only, name)
        summed = _values(balances_only, name)
        for year in YEARS:
            assert ((totals[year] > 0) == (stored > 0)).all(), (name, year)
            balances = balances_only.calculate(part, year)
            sums = np.bincount(members - 1, weights=balances, minlength=len(stored))
            assert summed[year] == pytest.approx(sums, rel=1e-6, abs=1e-6)
            assert totals[year] == pytest.approx(summed[year], rel=1e-6, abs=1e-6)
            if year > PROJECTION_END_YEAR:
                growth = _growth(totals_only, projected_with, year)
                assert totals[year] == pytest.approx(
                    totals[PROJECTION_END_YEAR] * growth, rel=1e-6
                )
    # Capital reads the totals compared above in every year; these years
    # cover the data year, both sides of the horizon and the last year.
    for name in MEANS_TEST_CAPITAL:
        for year in CAPITAL_YEARS:
            assert totals_only.calculate(name, year) == pytest.approx(
                balances_only.calculate(name, year), rel=1e-5, abs=1e-3
            ), (name, year)


INPUT_YEARS = st.integers(min_value=DATA_YEAR + 1, max_value=YEARS[-1])
STEPS = st.lists(
    st.one_of(
        st.tuples(st.just("calculate"), INPUT_YEARS),
        st.tuples(st.just("cash_isa"), INPUT_YEARS, AMOUNTS),
        st.tuples(st.just("cash_isa_balance"), INPUT_YEARS, AMOUNTS),
    ),
    min_size=1,
    max_size=8,
)


@PROPERTY_SETTINGS
@given(steps=STEPS, on_branch=st.booleans())
def test_a_total_after_any_inputs_equals_a_fresh_calculation(steps, on_branch):
    # Totals or balances set for any year, between calculations of any year:
    # each calculated total equals what the same simulation gives with every
    # calculated value dropped, and every supplied total keeps its value.
    simulation = Simulation(
        dataset=_dataset([{"cash_isa": 3_000.0}], household_columns=["cash_isa"])
    )
    target = simulation.get_branch("edited") if on_branch else simulation
    supplied = {
        year: target.calculate("cash_isa", year)[0] for year in range(DATA_YEAR, 2033)
    }
    for step in [*steps, ("calculate", YEARS[-1])]:
        name, year = step[:2]
        if name == "calculate":
            fresh = target.clone()
            fresh.drop_computed_arrays()
            calculated = target.calculate("cash_isa", year)[0]
            assert calculated == fresh.calculate("cash_isa", year)[0], (step, steps)
        elif name == "cash_isa":
            target.set_input(name, year, np.array([step[2]]))
            supplied[year] = np.float32(step[2])
        else:
            target.set_input(name, year, np.array([step[2], 0.0]))
    for year, amount in supplied.items():
        assert target.calculate("cash_isa", year)[0] == amount, (year, steps)
