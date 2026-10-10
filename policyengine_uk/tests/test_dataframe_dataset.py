"""``Simulation(dataset=<DataFrame>)`` loads a frame with one row per person.

The frame has a column for each input and period, named ``variable__period``,
which is the format ``Simulation.to_input_dataframe()`` exports. A benefit
unit or household value sits on the row of each member.

Before, the loader set every column as one value per person. It raised
``ValueError`` when a benefit unit or household had more than one person, and
gave single-person groups each other's values when their rows were not in
order of their identifiers. It also found the identifier columns by substring,
so ``household_id`` matched ``person_household_id``.

Invariants, for every frame of people in benefit units in households, in any
row order, whichever identifier columns name the groups:

1. People and groups: the simulation holds the frame's people in row order.
   Its benefit units and households are the distinct identifiers the frame
   names, in ascending order, and each person is in the ones their row names.
   This holds for identifiers that 32-bit floats cannot tell apart.
2. Values: every person variable has the value on that person's row, and
   every benefit unit and household variable has the value its members' rows
   hold. Projected back to people, each variable gives its column again.
3. Dataset: ``dataset`` holds a year for each whole-year period, with the
   same people, groups and values, and exact identifiers.
4. Row order: reordering the rows changes no person's, benefit unit's or
   household's values.
5. Round trip: the frame a simulation exports loads back to the same people,
   groups and inputs, and exports the same frame again.
6. Differential: a simulation built from a dataset and one built from the
   frame it exports give the same value for every variable of the model.
7. Exact names: a column is read only if the part of its name before ``__``
   is exactly a variable of the model.
8. The frame is not changed.

Intended exceptions, each a ``ValueError``: a column not named
``variable__period``; a repeated column; no ``person_id`` column; a repeated
person identifier; missing identifiers; identifier columns that differ between
periods; ``<group>_id`` and ``person_<group>_id`` columns that name different
groups for a person; identifiers of 2**24 or more held only as 32-bit floats,
which may each stand for more than one identifier (2**24 + 1 rounds to
2**24); and members of a group that give different values for one of its
variables.

Limit of the default export, which is not the loader's: ``to_input_dataframe()``
leaves out values a dataset supplies for a variable that has a formula, such
as ``state_pension_reported``. ``to_input_dataframe(include_computed_variables=
True)`` exports them, and must be taken before the simulation calculates
anything, since it also exports every calculated value.
"""

from dataclasses import dataclass
from typing import Dict

import numpy as np
import pandas as pd
import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from policyengine_uk import CountryTaxBenefitSystem, Microsimulation, Simulation
from policyengine_uk.data import UKMultiYearDataset, UKSingleYearDataset
from policyengine_uk.data.input_dataframe import (
    FLOAT32_EXACT_LIMIT,
    dataset_from_input_dataframe,
    split_column,
)
from policyengine_uk.scenarios import no_economic_assumptions

pytestmark = pytest.mark.usefixtures("cloned_uk_tax_benefit_system")

YEAR = 2025
GROUPS = ("benunit", "household")
PERSONAL_ALLOWANCE = "gov.hmrc.income_tax.allowances.personal_allowance.amount"
# Input variables of each entity and type. None has a formula, so the
# simulation returns each as it was given. Numbers are whole, so that the
# model's 32-bit floats hold them exactly.
VARIABLES = {
    "age": "person",
    "hours_worked": "person",
    "gender": "person",
    "is_disabled_for_benefits": "person",
    "benunit_reported_capital": "benunit",
    "would_claim_uc": "benunit",
    "council_tax": "household",
    "household_weight": "household",
    "region": "household",
}
GENDERS = ["MALE", "FEMALE"]
REGIONS = ["LONDON", "WALES", "SCOTLAND", "NORTH_EAST"]
# Starting points for identifiers: small ones, ones that straddle the largest
# whole number 32-bit floats count to, and ones of the size UK datasets use,
# where 32-bit floats are exact only at multiples of 64.
FIRST_IDS = [1, FLOAT32_EXACT_LIMIT - 2, 900_000_001]


@pytest.fixture(scope="module")
def tax_benefit_system():
    return CountryTaxBenefitSystem()


@dataclass
class Population:
    """People in benefit units in households, one row per person."""

    person_ids: np.ndarray
    # Each person's benefit unit and household identifier.
    groups: Dict[str, np.ndarray]
    # Each variable's value on each person's row.
    values: Dict[str, np.ndarray]

    def reordered(self, order) -> "Population":
        order = np.asarray(order)
        return Population(
            person_ids=self.person_ids[order],
            groups={group: ids[order] for group, ids in self.groups.items()},
            values={name: values[order] for name, values in self.values.items()},
        )

    def by_id(self, variable: str) -> dict:
        """The value of ``variable`` for each member of its entity."""
        entity = VARIABLES[variable]
        ids = self.person_ids if entity == "person" else self.groups[entity]
        return dict(zip(ids.tolist(), self.values[variable].tolist()))


def frame(population: Population, ids: str = "both", year: int = YEAR) -> pd.DataFrame:
    """The input frame of ``population``.

    ``ids`` chooses the columns that name each person's groups: ``"both"``,
    ``"own"`` (``benunit_id`` and ``household_id``), ``"person"``
    (``person_benunit_id`` and ``person_household_id``) or ``"exported"``,
    which holds the ``person_`` columns as the 32-bit floats the model stores
    and exports.
    """
    columns = {f"person_id__{year}": population.person_ids}
    for group in GROUPS:
        group_ids = population.groups[group]
        if ids in ("both", "person", "exported"):
            columns[f"person_{group}_id__{year}"] = (
                group_ids.astype(np.float32) if ids == "exported" else group_ids
            )
        if ids in ("both", "own", "exported"):
            columns[f"{group}_id__{year}"] = group_ids
    for variable, values in population.values.items():
        columns[f"{variable}__{year}"] = values
    return pd.DataFrame(columns)


@st.composite
def distinct_ids(draw, count: int) -> np.ndarray:
    """``count`` distinct identifiers near one starting point, in any order."""
    first = draw(st.sampled_from(FIRST_IDS))
    offsets = draw(
        st.lists(st.integers(0, 40), min_size=count, max_size=count, unique=True)
    )
    return first + np.array(offsets, dtype=np.int64)


@st.composite
def populations(draw) -> Population:
    # The number of people in each benefit unit of each household.
    households = draw(
        st.lists(
            st.lists(st.integers(1, 3), min_size=1, max_size=2),
            min_size=1,
            max_size=4,
        )
    )
    benunit_count = sum(len(benunits) for benunits in households)
    person_count = sum(sum(benunits) for benunits in households)
    household_ids = draw(distinct_ids(len(households)))
    benunit_ids = draw(distinct_ids(benunit_count))

    def per(count, strategy) -> list:
        return draw(st.lists(strategy, min_size=count, max_size=count))

    by_entity = {
        "person": {
            "age": per(person_count, st.integers(0, 90)),
            "hours_worked": per(person_count, st.integers(0, 3_000)),
            "gender": per(person_count, st.sampled_from(GENDERS)),
            "is_disabled_for_benefits": per(person_count, st.booleans()),
        },
        "benunit": {
            "benunit_reported_capital": per(benunit_count, st.integers(0, 90_000)),
            "would_claim_uc": per(benunit_count, st.booleans()),
        },
        "household": {
            "council_tax": per(len(households), st.integers(0, 5_000)),
            "household_weight": per(len(households), st.integers(0, 2_000)),
            "region": per(len(households), st.sampled_from(REGIONS)),
        },
    }
    index = {"person": [], "benunit": [], "household": []}
    for household, benunits in enumerate(households):
        for size in benunits:
            benunit = len(set(index["benunit"]))
            for _ in range(size):
                index["person"].append(len(index["person"]))
                index["benunit"].append(benunit)
                index["household"].append(household)
    population = Population(
        person_ids=draw(distinct_ids(person_count)),
        groups={
            "benunit": benunit_ids[index["benunit"]],
            "household": household_ids[index["household"]],
        },
        values={
            name: np.array(values)[index[entity]]
            for entity, variables in by_entity.items()
            for name, values in variables.items()
        },
    )
    return population.reordered(draw(st.permutations(range(person_count))))


def ids(simulation, entity) -> list:
    return np.asarray(simulation.populations[entity].ids).tolist()


def group_of_each_person(simulation, group) -> list:
    population = simulation.populations[group]
    return np.asarray(population.ids)[population.members_entity_id].tolist()


def calculated_by_id(simulation, variable, period=YEAR) -> dict:
    entity = simulation.tax_benefit_system.get_variable(variable).entity.key
    values = np.asarray(simulation.calculate(variable, period))
    return dict(zip(ids(simulation, entity), values.tolist()))


def assert_holds(simulation, population: Population, year: int = YEAR) -> None:
    """Invariants 1 to 3 for ``simulation``, built from ``population``."""
    # 1. People and groups.
    assert ids(simulation, "person") == population.person_ids.tolist()
    for group in GROUPS:
        assert ids(simulation, group) == sorted(set(population.groups[group].tolist()))
        assert (
            group_of_each_person(simulation, group) == population.groups[group].tolist()
        )
    # 2. Values.
    for variable in population.values:
        assert calculated_by_id(simulation, variable, year) == population.by_id(
            variable
        )
        on_rows = np.asarray(simulation.calculate(variable, year, map_to="person"))
        assert on_rows.tolist() == population.values[variable].tolist()
    # 3. Dataset.
    assert isinstance(simulation.dataset, UKMultiYearDataset)
    assert_tables_hold(simulation.dataset[year], population)


def assert_tables_hold(tables: UKSingleYearDataset, population: Population) -> None:
    person = tables.person
    assert person.person_id.tolist() == population.person_ids.tolist()
    for group in GROUPS:
        assert (
            person[f"person_{group}_id"].tolist() == population.groups[group].tolist()
        )
        table = getattr(tables, group)
        assert table[f"{group}_id"].tolist() == sorted(
            set(population.groups[group].tolist())
        )
    for variable, entity in VARIABLES.items():
        table = getattr(tables, entity)
        assert dict(
            zip(table[f"{entity}_id"].tolist(), table[variable].tolist())
        ) == population.by_id(variable)


# The issue's reproduction and the cases the old loader got wrong.


def test_a_household_and_benefit_unit_of_two_people_build():
    frame_ = pd.DataFrame(
        {
            "person_id__2025": [1, 2],
            "person_benunit_id__2025": [1, 1],
            "person_household_id__2025": [1, 1],
            "benunit_id__2025": [1, 1],
            "household_id__2025": [1, 1],
            "age__2025": [40, 38],
            "council_tax__2025": [1_500.0, 1_500.0],
        }
    )

    simulation = Simulation(dataset=frame_)

    assert ids(simulation, "benunit") == [1]
    assert ids(simulation, "household") == [1]
    assert simulation.calculate("council_tax", 2025).tolist() == [1_500.0]
    assert simulation.calculate("age", 2025).tolist() == [40, 38]
    assert simulation.calculate("household_id", 2025).tolist() == [1]
    assert simulation.calculate("benunit_id", 2025).tolist() == [1]


def test_groups_get_their_own_values_when_rows_are_not_in_identifier_order():
    # The old loader built this frame, and gave household 10 the council tax
    # of household 30.
    frame_ = pd.DataFrame(
        {
            "person_id__2025": [1, 2, 3],
            "person_benunit_id__2025": [30, 10, 20],
            "person_household_id__2025": [30, 10, 20],
            "benunit_id__2025": [30, 10, 20],
            "household_id__2025": [30, 10, 20],
            "council_tax__2025": [3_000.0, 1_000.0, 2_000.0],
            "benunit_reported_capital__2025": [300.0, 100.0, 200.0],
        }
    )

    simulation = Simulation(dataset=frame_)

    assert calculated_by_id(simulation, "council_tax") == {
        10: 1_000.0,
        20: 2_000.0,
        30: 3_000.0,
    }
    assert calculated_by_id(simulation, "benunit_reported_capital") == {
        10: 100.0,
        20: 200.0,
        30: 300.0,
    }
    assert simulation.calculate("council_tax", 2025, map_to="person").tolist() == [
        3_000.0,
        1_000.0,
        2_000.0,
    ]


def test_a_frame_without_group_columns_gives_each_person_their_own():
    # The frame in docs/book/usage/simulations.md.
    frame_ = pd.DataFrame(
        {
            "person_id__2025": [1, 2, 3],
            "age__2025": [25, 45, 65],
            "employment_income__2025": [20_000, 40_000, 0],
        }
    )

    simulation = Simulation(dataset=frame_)

    assert ids(simulation, "benunit") == [1, 2, 3]
    assert ids(simulation, "household") == [1, 2, 3]
    assert group_of_each_person(simulation, "household") == [1, 2, 3]
    income_tax = simulation.calculate("income_tax", 2025)
    assert income_tax[1] > income_tax[0] > income_tax[2] == 0


# Exact column names.


def test_split_column():
    assert split_column("age__2025") == ("age", "2025")
    assert split_column("person_household_id__2025") == ("person_household_id", "2025")
    assert split_column("fuel_duty__2025-01") == ("fuel_duty", "2025-01")


@pytest.mark.parametrize("column", ["age", "age__", "__2025", "age_2025", 0])
def test_a_column_not_named_for_a_variable_and_period_is_refused(column):
    with pytest.raises(ValueError, match="is not named 'variable__period'"):
        split_column(column)


def test_identifier_columns_are_matched_by_exact_name():
    # Every decoy contains an identifier's name. The old loader took the
    # first column containing "household_id__" for the households, and so on.
    frame_ = pd.DataFrame(
        {
            "previous_person_id__2025": [7, 7, 7],
            "previous_benunit_id__2025": [5, 5, 5],
            "previous_household_id__2025": [9, 9, 9],
            "previous_person_benunit_id__2025": [5, 5, 5],
            "previous_person_household_id__2025": [9, 9, 9],
            "person_id__2025": [1, 2, 3],
            "person_benunit_id__2025": [11, 11, 12],
            "person_household_id__2025": [21, 21, 22],
            "benunit_id__2025": [11, 11, 12],
            "household_id__2025": [21, 21, 22],
            "council_tax__2025": [1_000.0, 1_000.0, 2_000.0],
            "previous_council_tax__2025": [1.0, 2.0, 3.0],
        }
    )

    simulation = Simulation(dataset=frame_)

    assert ids(simulation, "person") == [1, 2, 3]
    assert ids(simulation, "benunit") == [11, 12]
    assert ids(simulation, "household") == [21, 22]
    assert group_of_each_person(simulation, "household") == [21, 21, 22]
    assert calculated_by_id(simulation, "council_tax") == {21: 1_000.0, 22: 2_000.0}


def test_rounded_person_columns_do_not_merge_households():
    # A frame as to_input_dataframe() exports it: person_household_id comes
    # before household_id and holds 32-bit floats, in which these three
    # households are the same number. The old loader took the households from
    # the first column containing "household_id__", and so built one.
    households = np.array([900_000_001, 900_000_001, 900_000_002, 900_000_003])
    benunits = np.array([906_000_001, 906_000_002, 906_000_003, 906_000_004])
    frame_ = pd.DataFrame(
        {
            "person_id__2025": [1, 2, 3, 4],
            "person_benunit_id__2025": benunits.astype(np.float32),
            "person_household_id__2025": households.astype(np.float32),
            "benunit_id__2025": benunits,
            "household_id__2025": households,
            "council_tax__2025": [1_000.0, 1_000.0, 2_000.0, 3_000.0],
        }
    )
    assert frame_["person_household_id__2025"].nunique() == 1

    simulation = Simulation(dataset=frame_)

    assert ids(simulation, "household") == [900_000_001, 900_000_002, 900_000_003]
    assert group_of_each_person(simulation, "household") == households.tolist()
    assert group_of_each_person(simulation, "benunit") == benunits.tolist()
    assert calculated_by_id(simulation, "council_tax") == {
        900_000_001: 1_000.0,
        900_000_002: 2_000.0,
        900_000_003: 3_000.0,
    }
    tables = simulation.dataset[2025]
    assert tables.person.person_household_id.tolist() == households.tolist()
    assert tables.person.person_benunit_id.tolist() == benunits.tolist()


# Periods.


def test_each_year_of_a_frame_is_loaded():
    frame_ = pd.DataFrame(
        {
            "person_id__2025": [1, 2],
            "household_id__2025": [1, 1],
            "benunit_id__2025": [1, 1],
            "age__2025": [40, 38],
            "council_tax__2025": [1_500.0, 1_500.0],
            "council_tax__2026": [1_600.0, 1_600.0],
            "hours_worked__2027": [1_000.0, 0.0],
        }
    )

    simulation = Simulation(dataset=frame_)

    assert simulation.dataset.years == [2025, 2026, 2027]
    assert simulation.calculate("council_tax", 2025).tolist() == [1_500.0]
    assert simulation.calculate("council_tax", 2026).tolist() == [1_600.0]
    assert simulation.calculate("hours_worked", 2027).tolist() == [1_000.0, 0.0]
    for year in (2025, 2026, 2027):
        tables = simulation.dataset[year]
        assert tables.person.person_household_id.tolist() == [1, 1]
        assert tables.household.household_id.tolist() == [1]
    assert simulation.dataset[2026].household.council_tax.tolist() == [1_600.0]
    assert "council_tax" not in simulation.dataset[2027].household


def test_a_value_for_a_month_is_set_on_its_group():
    # ebr_energy_bills_credit_eligible is a monthly household input.
    frame_ = pd.DataFrame(
        {
            "person_id__2025": [1, 2, 3],
            "household_id__2025": [20, 10, 20],
            "ebr_energy_bills_credit_eligible__2025-01": [True, False, True],
            "ebr_energy_bills_credit_eligible__2025-02": [False, True, False],
        }
    )

    simulation = Simulation(dataset=frame_)

    assert simulation.dataset.years == [2025]
    assert calculated_by_id(
        simulation, "ebr_energy_bills_credit_eligible", "2025-01"
    ) == {10: False, 20: True}
    assert calculated_by_id(
        simulation, "ebr_energy_bills_credit_eligible", "2025-02"
    ) == {10: True, 20: False}


def test_a_frame_that_names_no_whole_year_is_held_in_the_default_input_year():
    frame_ = pd.DataFrame(
        {
            "person_id__2025-01": [1, 2],
            "household_id__2025-01": [1, 1],
            "ebr_energy_bills_credit_eligible__2025-01": [True, True],
        }
    )

    simulation = Simulation(dataset=frame_)

    assert simulation.dataset.years == [Simulation.default_input_period]
    assert ids(simulation, "household") == [1]
    assert calculated_by_id(
        simulation, "ebr_energy_bills_credit_eligible", "2025-01"
    ) == {1: True}


# The dataset a frame-built simulation holds.


def test_a_frame_is_loaded_like_the_multi_year_dataset_it_describes():
    # A scenario that freezes uprated inputs at the first year applies to a
    # frame as it does to a multi-year dataset.
    frame_ = pd.DataFrame(
        {
            "person_id__2025": [1],
            "employment_income__2025": [30_000.0],
            "employment_income__2026": [35_000.0],
            "age__2025": [40],
            "age__2026": [41],
        }
    )
    before = frame_.copy()

    simulation = Simulation(dataset=frame_)
    frozen = Simulation(dataset=frame_, scenario=no_economic_assumptions)

    assert simulation.calculate("employment_income", 2026).tolist() == [35_000.0]
    assert frozen.calculate("employment_income", 2026).tolist() == [30_000.0]
    assert frozen.calculate("age", 2026).tolist() == [41]
    assert simulation.dataset[2026].person.employment_income.tolist() == [35_000.0]
    pd.testing.assert_frame_equal(frame_, before)


def dataset(state_pension: bool = False) -> UKSingleYearDataset:
    """Seven households of one or two benefit units, with children, people
    in work and pensioners, and identifiers of the size UK datasets use.

    Every column but ``state_pension_reported`` is an input that the default
    export keeps.
    """
    sizes = [[1, 1], [1], [2, 2], [1], [1, 1], [2], [2, 3]]
    ages = [34, 31, 6, 71, 68, 2, 45, 16]
    people, benunits, households = [], [], []
    for index, units in enumerate(sizes):
        household_id = 900_000_001 + index
        households.append(
            {
                "household_id": household_id,
                "household_weight": 100.0 * (index + 1),
                "region": REGIONS[index % len(REGIONS)],
                "rent": 6_000.0 * (index % 3),
                "tenure_type": ["OWNED_OUTRIGHT", "RENT_PRIVATELY"][index % 2],
                "council_tax": 1_000.0 + 100 * index,
                "corporate_wealth": 10_000.0 * index,
                "food_and_non_alcoholic_beverages_consumption": 3_000.0 + index,
            }
        )
        for size in units:
            benunit_id = 906_000_001 + len(benunits)
            benunits.append({"benunit_id": benunit_id, "would_claim_uc": True})
            for position in range(size):
                age = ages[len(people) % len(ages)] if position < 2 else 4
                working = 18 <= age < 66
                person = {
                    "person_id": 967_000_001 + len(people),
                    "person_benunit_id": benunit_id,
                    "person_household_id": household_id,
                    "age": age,
                    "employment_income": 9_000.0 * (1 + len(people) % 5) * working,
                    "gender": GENDERS[len(people) % 2],
                }
                if state_pension:
                    person["state_pension_reported"] = 9_500.0 * (age >= 66)
                people.append(person)
    return UKSingleYearDataset(
        person=pd.DataFrame(people),
        benunit=pd.DataFrame(benunits),
        household=pd.DataFrame(households),
        fiscal_year=YEAR,
    )


def differing_variables(left, right, years) -> list:
    """Each variable and year for which two simulations disagree."""
    differing = []
    for variable in left.tax_benefit_system.variables:
        for year in years:
            ours = np.asarray(left.calculate(variable, year))
            theirs = np.asarray(right.calculate(variable, year))
            if not np.array_equal(ours, theirs, equal_nan=ours.dtype.kind == "f"):
                differing.append((variable, year))
    return differing


@pytest.mark.parametrize(
    "state_pension, include_computed_variables",
    [(False, False), (True, True)],
    ids=["default export", "export of every stored value"],
)
def test_an_exported_frame_gives_the_results_of_its_dataset(
    state_pension, include_computed_variables
):
    original = Simulation(dataset=dataset(state_pension))
    exported = original.to_input_dataframe(
        include_computed_variables=include_computed_variables
    )
    before = exported.copy()

    reloaded = Simulation(dataset=exported)

    for entity in ("person", "benunit", "household"):
        assert ids(reloaded, entity) == ids(original, entity)
    for group in GROUPS:
        assert group_of_each_person(reloaded, group) == group_of_each_person(
            original, group
        )
    assert reloaded.dataset.years == original.dataset.years
    # 6. Differential, over every variable of the model, in the data year and
    # a later one.
    assert differing_variables(original, reloaded, [YEAR, YEAR + 2]) == []
    pd.testing.assert_frame_equal(exported, before)
    if state_pension:
        # The State Pension formulas read the data year from the dataset.
        assert original.calculate("state_pension", YEAR + 2).sum() > 0


def test_a_reform_on_an_exported_frame_gives_the_results_of_its_dataset():
    # The reformed simulation and its baseline are each built from the frame.
    reform = {PERSONAL_ALLOWANCE: 20_000}
    original = Microsimulation(dataset=dataset(), reform=reform)
    reloaded = Microsimulation(
        dataset=Simulation(dataset=dataset()).to_input_dataframe(), reform=reform
    )

    def values(simulation, variable) -> np.ndarray:
        return np.asarray(simulation.calculate(variable, 2026))

    for variable in ("income_tax", "household_net_income", "universal_credit"):
        for ours, theirs in (
            (original, reloaded),
            (original.baseline, reloaded.baseline),
        ):
            assert values(ours, variable).tolist() == values(theirs, variable).tolist()
        # Weighted totals use the household weights the frame carries.
        assert reloaded.calculate(variable, 2026).sum() == pytest.approx(
            original.calculate(variable, 2026).sum()
        )
    assert (
        values(reloaded, "income_tax").sum()
        < values(reloaded.baseline, "income_tax").sum()
    )


# Refusals.


def refused(frame_: pd.DataFrame, match: str) -> None:
    before = frame_.copy()
    with pytest.raises(ValueError, match=match):
        Simulation(dataset=frame_)
    pd.testing.assert_frame_equal(frame_, before)


def couple(**columns) -> pd.DataFrame:
    """Two people in one benefit unit and household, with other columns."""
    return pd.DataFrame(
        {
            "person_id__2025": [1, 2],
            "benunit_id__2025": [1, 1],
            "household_id__2025": [1, 1],
            **columns,
        }
    )


def test_a_frame_without_person_id_is_refused():
    refused(pd.DataFrame({"age__2025": [40, 38]}), "needs a person_id column")


def test_a_frame_with_a_column_that_names_no_period_is_refused():
    refused(couple(age=[40, 38]), "'age' is not named 'variable__period'")


def test_a_frame_with_a_repeated_column_is_refused():
    frame_ = pd.concat([couple(), pd.DataFrame({"person_id__2025": [1, 2]})], axis=1)
    refused(frame_, "'person_id__2025' appears more than once")


def test_missing_identifiers_are_refused():
    frame_ = couple()
    frame_["household_id__2025"] = [1.0, np.nan]
    refused(frame_, "'household_id__2025' has missing identifiers")


def test_a_repeated_person_identifier_is_refused():
    # Without group columns each person is a group of their own, so the two
    # rows would otherwise be one household.
    refused(
        pd.DataFrame({"person_id__2025": [1, 1], "age__2025": [30, 40]}),
        "'person_id__2025' repeats 1",
    )


@pytest.mark.parametrize(
    "column",
    ["person_id__2025", "person_household_id__2025", "person_benunit_id__2025"],
)
def test_identifiers_that_32_bit_floats_round_are_refused(column):
    # 2**24 + 1 rounds to 2**24, so as 32-bit floats these two identifiers are
    # one number: the smallest case that would merge two people or groups.
    frame_ = pd.DataFrame(
        {
            "person_id__2025": [1, 2],
            column: np.array([FLOAT32_EXACT_LIMIT + 1, FLOAT32_EXACT_LIMIT], "float32"),
        }
    )
    assert frame_[column].nunique() == 1
    refused(frame_, f"'{column}' holds identifiers of 16,777,216 or more")


def test_rounded_person_columns_are_checked_at_their_own_precision():
    # 900,000,001 and 900,000,030 are the same 32-bit float, so a rounded
    # person_household_id agrees with either; 900,000,128 is a different one.
    exact = np.array([900_000_001, 900_000_030])
    agreeing = couple(
        **{
            "household_id__2025": exact,
            "person_household_id__2025": exact[::-1].astype(np.float32),
        }
    )
    simulation = Simulation(dataset=agreeing)
    assert group_of_each_person(simulation, "household") == exact.tolist()

    refused(
        couple(
            **{
                "household_id__2025": exact,
                "person_household_id__2025": np.array(
                    [900_000_001, 900_000_128], "float32"
                ),
            }
        ),
        "put the person in row 1 in different groups",
    )


def test_integer_group_columns_must_agree_exactly():
    # Integer columns hold identifiers exactly (as they will once #2267 makes
    # the person_ variables integers), so they must name the same group.
    refused(
        couple(
            **{
                "household_id__2025": [900_000_001, 900_000_001],
                "person_household_id__2025": [900_000_001, 900_000_002],
            }
        ),
        "'household_id__2025' and 'person_household_id__2025' put the person in "
        "row 1 in different groups",
    )


def test_identifiers_that_differ_between_periods_are_refused():
    refused(
        couple(**{"household_id__2026": [1, 2]}),
        "'household_id__2025' and 'household_id__2026' differ",
    )


@pytest.mark.parametrize("group", GROUPS)
def test_group_columns_that_name_different_groups_are_refused(group):
    refused(
        couple(**{f"person_{group}_id__2025": [1, 2]}),
        f"'{group}_id__2025' and 'person_{group}_id__2025' put the person in "
        "row 1 in different groups",
    )


@pytest.mark.parametrize(
    "column, values, entity",
    [
        ("council_tax__2025", [1_500.0, 900.0], "household"),
        ("would_claim_uc__2025", [True, False], "benunit"),
        ("region__2025", ["LONDON", "WALES"], "household"),
        ("council_tax__2025", [1_500.0, np.nan], "household"),
        ("ebr_energy_bills_credit_eligible__2025-01", [True, False], "household"),
    ],
)
def test_members_that_give_different_values_for_their_group_are_refused(
    column, values, entity
):
    refused(
        couple(**{column: values}),
        f"'{column}' gives {entity} 1 more than one value",
    )


def test_members_may_all_leave_a_group_value_missing(tax_benefit_system):
    frame_ = couple(**{"council_tax__2025": [np.nan, np.nan]})

    tables, _ = dataset_from_input_dataframe(frame_, tax_benefit_system, YEAR)

    assert tables[YEAR].household.council_tax.isna().tolist() == [True]


# Properties.

SIMULATION_SETTINGS = settings(
    max_examples=25,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)
ROUND_TRIP_SETTINGS = settings(SIMULATION_SETTINGS, max_examples=15)
TABLE_SETTINGS = settings(
    max_examples=200,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)
id_columns = st.sampled_from(["both", "own", "person", "exported"])


@SIMULATION_SETTINGS
@given(population=populations(), id_columns=id_columns)
def test_a_frame_builds_its_people_groups_and_values(population, id_columns):
    frame_ = frame(population, id_columns)
    before = frame_.copy()

    simulation = Simulation(dataset=frame_)

    # 1 to 3.
    assert_holds(simulation, population)
    # 8. The frame is not changed.
    pd.testing.assert_frame_equal(frame_, before)


@ROUND_TRIP_SETTINGS
@given(population=populations(), id_columns=id_columns)
def test_an_exported_frame_loads_back_and_exports_itself(population, id_columns):
    simulation = Simulation(dataset=frame(population, id_columns))
    exported = simulation.to_input_dataframe()

    reloaded = Simulation(dataset=exported)

    # 5. Round trip: the same people, groups and inputs, including for
    # identifiers the exported person_ columns hold rounded.
    assert_holds(reloaded, population)
    pd.testing.assert_frame_equal(reloaded.to_input_dataframe(), exported)
    for group in GROUPS:
        exact = population.groups[group]
        assert exported[f"{group}_id__{YEAR}"].tolist() == exact.tolist()
        assert (
            exported[f"person_{group}_id__{YEAR}"].tolist()
            == exact.astype(np.float32).tolist()
        )


@TABLE_SETTINGS
@given(population=populations(), id_columns=id_columns, data=st.data())
def test_tables_hold_the_frame_in_any_row_order(
    tax_benefit_system, population, id_columns, data
):
    order = data.draw(st.permutations(range(len(population.person_ids))))
    reordered = population.reordered(order)

    tables, other_inputs = dataset_from_input_dataframe(
        frame(population, id_columns), tax_benefit_system, YEAR
    )
    reordered_tables, _ = dataset_from_input_dataframe(
        frame(reordered, id_columns), tax_benefit_system, YEAR
    )

    # 3. Dataset.
    assert other_inputs == []
    assert tables.years == [YEAR]
    assert_tables_hold(tables[YEAR], population)
    # 4. Row order: the same benefit units and households, and the same
    # people once in the same order.
    assert_tables_hold(reordered_tables[YEAR], reordered)
    for group in GROUPS:
        pd.testing.assert_frame_equal(
            getattr(reordered_tables[YEAR], group), getattr(tables[YEAR], group)
        )
    pd.testing.assert_frame_equal(
        reordered_tables[YEAR].person.sort_values("person_id", ignore_index=True),
        tables[YEAR].person.sort_values("person_id", ignore_index=True),
    )


@TABLE_SETTINGS
@given(population=populations(), data=st.data())
def test_columns_that_name_no_variable_are_left_out(
    tax_benefit_system, population, data
):
    # 7. Exact names: a column whose name only contains a variable's name
    # changes nothing, wherever it sits and whatever it holds.
    frame_ = frame(population)
    people = len(population.person_ids)
    decoys = data.draw(
        st.lists(
            st.sampled_from(sorted(VARIABLES) + ["person_id", "household_id"]),
            min_size=1,
            max_size=4,
            unique=True,
        )
    )
    for variable in decoys:
        prefixed = data.draw(st.booleans())
        name = f"previous_{variable}" if prefixed else f"{variable}_previous"
        assert name not in tax_benefit_system.variables
        position = data.draw(st.integers(0, len(frame_.columns)))
        values = data.draw(
            st.lists(st.integers(0, 5), min_size=people, max_size=people)
        )
        frame_.insert(position, f"{name}__{YEAR}", values)

    tables, _ = dataset_from_input_dataframe(frame_, tax_benefit_system, YEAR)
    plain, _ = dataset_from_input_dataframe(frame(population), tax_benefit_system, YEAR)

    for entity in ("person", "benunit", "household"):
        pd.testing.assert_frame_equal(
            getattr(tables[YEAR], entity), getattr(plain[YEAR], entity)
        )


@TABLE_SETTINGS
@given(population=populations())
def test_rounded_identifiers_alone_never_merge_groups(tax_benefit_system, population):
    # A frame that names the groups only in 32-bit float columns either holds
    # every identifier exactly, and builds the same groups, or is refused.
    frame_ = frame(population, "exported").drop(
        columns=[f"{group}_id__{YEAR}" for group in GROUPS]
    )
    exact = all(
        (np.abs(population.groups[group]) < FLOAT32_EXACT_LIMIT).all()
        for group in GROUPS
    )

    if exact:
        tables, _ = dataset_from_input_dataframe(frame_, tax_benefit_system, YEAR)
        assert_tables_hold(tables[YEAR], population)
    else:
        with pytest.raises(ValueError, match="as 32-bit floats"):
            dataset_from_input_dataframe(frame_, tax_benefit_system, YEAR)
