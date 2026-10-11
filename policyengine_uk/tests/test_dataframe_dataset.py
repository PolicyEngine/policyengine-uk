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
   This holds for identifiers that 32-bit floats cannot tell apart, and for
   columns that mix integer and float identifiers: a frame either loads its
   people and groups exactly or is refused.
2. Values: every person variable has the value on that person's row, and
   every benefit unit and household variable has the value its members' rows
   hold. Projected back to people, each variable gives its column again.
3. Dataset: ``dataset`` holds a year for each whole-year period the frame
   gives values for (identifier columns add none), with the same people,
   groups and values, and exact identifiers.
4. Row order: reordering the rows changes no person's, benefit unit's or
   household's values.
5. Round trip: the frame a simulation exports loads back to the same people,
   groups and inputs, and exports the same frame again; so does that frame
   saved as CSV, which holds the exported 32-bit identifiers as 64-bit floats.
6. Differential: a simulation built from a dataset and one built from the
   frame it exports give the same value for every variable of the model.
7. Exact names: a column is read only if the part of its name before ``__``
   is exactly a variable of the model.
8. The frame is not changed.
9. Previous loader (differential): for every frame the previous loader read
   correctly (each benefit unit and household of one person, rows in order of
   identifier), both give every input the same value in every period they
   set. This includes a variable given for months and for the year, whose
   columns are set in the frame's order, as the previous loader set them.

Intended exceptions, each a ``ValueError``: a column not named
``variable__period``; a repeated column; no ``person_id`` column; a repeated
person identifier; missing identifiers; identifiers that are not whole numbers;
identifier columns that differ between periods; ``<group>_id`` and
``person_<group>_id`` columns that name different groups for a person; an
identifier that does not fit in 64 bits; an identifier read from a float
that may stand for more than one whole number
(2**24 or more for 32-bit floats: 2**24 + 1 rounds to 2**24), unless the
group's own integer identifier is given beside it; and members of a group that
give different values for one of its variables.

Limit of the default export, which is not the loader's: ``to_input_dataframe()``
leaves out values a dataset supplies for a variable that has a formula, such
as ``state_pension_reported``. ``to_input_dataframe(include_computed_variables=
True)`` exports them, and must be taken before the simulation calculates
anything, since it also exports every calculated value.
"""

import io
import warnings
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
    IDENTIFIER_VARIABLES,
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
    # The dataset holds whole years only, so a January value is not taken
    # for the year.
    assert "ebr_energy_bills_credit_eligible" not in simulation.dataset[2025].household


@pytest.mark.parametrize(
    "order, february",
    [(["2025-01", "2025"], 1_000 / 11), (["2025", "2025-01"], 100)],
    ids=["month then year", "year then month"],
)
def test_a_months_and_its_years_values_are_set_in_column_order(order, february):
    # A year's value spreads over the months not yet set. Given first, the
    # January value stays and the year's other 1,000 is split over eleven
    # months; given after the year, it replaces January's twelfth. Setting
    # each column in turn, as the previous loader did, gives the same.
    given = {"2025-01": [200.0], "2025": [1_200.0]}
    frame_ = pd.DataFrame(
        {
            "person_id__2025": [1],
            **{f"ni_class_1_employee__{period}": given[period] for period in order},
        }
    )

    simulation = Simulation(dataset=frame_)

    def month(number):
        return simulation.calculate("ni_class_1_employee", f"2025-{number:02d}")

    assert month(1).tolist() == [200.0]
    assert month(2).tolist() == pytest.approx([february])
    assert month(12).tolist() == pytest.approx([february])
    # The year's value stays in the dataset, which holds whole years.
    assert simulation.dataset[2025].person.ni_class_1_employee.tolist() == [1_200.0]


def test_the_data_year_is_the_first_year_the_frame_gives_data_for():
    # The State Pension formulas take the data year from the dataset. An
    # identifier column named for an earlier year must not become it, or the
    # reported pension, given for 2027, would be read for 2025 and be zero.
    frame_ = pd.DataFrame(
        {
            "person_id__2025": [1],
            "benunit_id__2025": [1],
            "household_id__2025": [1],
            "person_benunit_id__2025": [1],
            "person_household_id__2025": [1],
            "age__2027": [70],
            "state_pension_reported__2027": [9_000.0],
            "state_pension_type__2027": ["BASIC"],
        }
    )

    simulation = Simulation(dataset=frame_)
    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.setattr(
            Simulation, "build_from_dataframe", legacy_build_from_dataframe
        )
        previous = Simulation(dataset=frame_)

    assert simulation.dataset.years == [2027]
    pension = simulation.calculate("state_pension", 2027).tolist()
    assert pension[0] > 0
    assert pension == previous.calculate("state_pension", 2027).tolist()


@pytest.mark.parametrize("identifier_year, data_year", [(2025, 2027), (2027, 2025)])
def test_identifiers_hold_in_the_years_their_columns_name(identifier_year, data_year):
    # The dataset's years are those with data, where it holds the
    # identifiers too. A year only an identifier column names is not one of
    # them, but the identifiers are set for it, as the previous loader set
    # them: inputs carry forward, not back, so they would otherwise be zero
    # in a year before the data.
    frame_ = pd.DataFrame(
        {
            f"person_id__{identifier_year}": [5, 6, 7],
            f"benunit_id__{identifier_year}": [50, 50, 70],
            f"household_id__{identifier_year}": [500, 500, 500],
            f"age__{data_year}": [40, 38, 70],
        }
    )

    simulation = Simulation(dataset=frame_)

    assert simulation.dataset.years == [data_year]
    for year in (identifier_year, data_year):
        assert simulation.calculate("person_id", year).tolist() == [5, 6, 7]
        assert simulation.calculate("benunit_id", year).tolist() == [50, 70]
        assert simulation.calculate("household_id", year).tolist() == [500]
        assert simulation.calculate("person_benunit_id", year).tolist() == [50, 50, 70]
        assert simulation.calculate("person_household_id", year).tolist() == [500] * 3
    exported = simulation.to_input_dataframe()
    assert exported[f"person_id__{identifier_year}"].tolist() == [5, 6, 7]


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
    # 8. The frame is not changed. From policyengine-core 3.33 the default
    # export holds an enum input as the stored EnumArray, which pandas 3
    # keeps until a copy makes it a plain array, and assert_frame_equal
    # compares array classes; so compare a copy, which still shows any
    # change the loader made to the values.
    pd.testing.assert_frame_equal(exported.copy(), before)
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


def without_corporate_wealth() -> UKSingleYearDataset:
    """``dataset()`` without corporate wealth. In seven households, that
    wealth carries the corporate tax of a whole population, which makes most
    of their incomes negative."""
    data = dataset()
    data.household = data.household.drop(columns="corporate_wealth")
    return data


@pytest.mark.parametrize("budget", ["nhs", "education", "other_public_spending"])
def test_spending_on_a_small_frame_goes_to_the_deciles_it_holds(budget):
    # With a dataset, each income decile's share of extra spending goes to
    # its households. Seven households leave some deciles empty; those shares
    # go to nobody, rather than raising KeyError. A household with negative
    # income is in decile -1, which gets nothing.
    reform = {f"gov.contrib.policyengine.budget.{budget}": 1}
    variable = f"{budget}_budget_change"
    original = Microsimulation(dataset=without_corporate_wealth(), reform=reform)
    reloaded = Microsimulation(
        dataset=Simulation(dataset=without_corporate_wealth()).to_input_dataframe(),
        reform=reform,
    )

    def values(simulation, name) -> np.ndarray:
        return np.asarray(simulation.calculate(name, YEAR, unweighted=True))

    change = values(reloaded, variable)
    weights = values(reloaded, "household_weight")
    deciles = values(reloaded, "pre_budget_change_ons_household_income_decile")
    occupied = set(deciles.tolist()) - {-1}

    assert change.tolist() == values(original, variable).tolist()
    assert 1 < len(occupied) < 10
    assert np.isfinite(change).all()
    assert ((change > 0) == np.isin(deciles, list(occupied))).all()
    assert 0 < (change * weights).sum() < 1e9
    for decile in occupied:
        assert len(set(change[deciles == decile].tolist())) == 1


@pytest.mark.parametrize("budget", ["nhs", "education", "other_public_spending"])
def test_spending_skips_a_decile_whose_households_have_no_weight(budget):
    # The deciles are given as inputs here, so that one holds only a
    # household of zero weight: its share has nobody to go to, and dividing
    # it by that weight must not give an infinite or missing amount.
    frame_ = pd.DataFrame(
        {
            "person_id__2025": [1, 2, 3],
            "household_weight__2025": [0.0, 2.0, 2.0],
            "pre_budget_change_ons_household_income_decile__2025": [1, 2, 2],
        }
    )

    simulation = Simulation(
        dataset=frame_, reform={f"gov.contrib.policyengine.budget.{budget}": 1}
    )
    change = np.asarray(simulation.calculate(f"{budget}_budget_change", YEAR))

    assert np.isfinite(change).all()
    assert change[0] == 0
    assert change[1] == change[2] > 0
    # Decile 2's share is under the whole budget, split over its weight of 4.
    assert change[1] * 4 < 1e9


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


@pytest.mark.parametrize(
    "column", ["person_id__2025", "benunit_id__2025", "household_id__2025"]
)
def test_mixed_identifiers_that_32_bit_floats_round_are_refused(column):
    # In an object column each identifier keeps its own type, and
    # np.float32(2**24) compares equal to 2**24 + 1, so read together they
    # would be one person or group.
    mixed = pd.Series(
        [np.float32(FLOAT32_EXACT_LIMIT), FLOAT32_EXACT_LIMIT + 1], dtype=object
    )
    frame_ = pd.DataFrame({"person_id__2025": [1, 2], "age__2025": [25, 45]})
    frame_[column] = mixed
    refused(frame_, f"'{column}' holds identifiers of 16,777,216 or more as 32-bit")


@pytest.mark.parametrize(
    "values",
    [
        [1.5, 2.0],
        ["a", "b"],
        [True, False],
        pd.Series([1, "2"], dtype=object),
        pd.Series([1, 2.5], dtype=object),
        pd.Series([1, np.float32(2.5)], dtype=object),
    ],
    ids=[
        "fraction",
        "text",
        "booleans",
        "mixed text",
        "mixed fraction",
        "mixed float32",
    ],
)
def test_identifiers_that_are_not_whole_numbers_are_refused(values):
    refused(couple(**{"household_id__2025": values}), "which is not a whole number")


def test_whole_number_floats_are_identifiers():
    frame_ = couple(
        **{
            "household_id__2025": [7.0, 7.0],
            "person_household_id__2025": pd.Series([np.float32(7), 7], dtype=object),
        }
    )

    simulation = Simulation(dataset=frame_)

    assert ids(simulation, "household") == [7]
    assert simulation.dataset[2025].household.household_id.dtype == np.int64


@pytest.mark.parametrize(
    "values",
    [
        pd.Series([1, 2**63], dtype=object),
        np.array([1, 2**63], dtype=np.uint64),
    ],
    ids=["python int", "uint64"],
)
def test_identifiers_too_large_for_64_bits_are_refused(values):
    refused(
        pd.DataFrame({"person_id__2025": values}),
        "'person_id__2025' holds identifiers too large for 64-bit integers",
    )


def test_an_exported_frame_saved_as_csv_loads_back():
    # The exported person_ columns hold 32-bit floats: 906,000,001 is
    # 906,000,000. CSV gives them back as 64-bit floats, which still name the
    # groups the exact benunit_id and household_id columns give.
    original = Simulation(dataset=dataset())
    exported = original.to_input_dataframe()
    from_csv = pd.read_csv(io.StringIO(exported.to_csv(index=False)))
    assert from_csv["person_benunit_id__2025"].dtype == np.float64
    assert from_csv["person_benunit_id__2025"].iloc[0] == 906_000_000

    reloaded = Simulation(dataset=from_csv)

    for entity in ("person", "benunit", "household"):
        assert ids(reloaded, entity) == ids(original, entity)
    for group in GROUPS:
        assert group_of_each_person(reloaded, group) == group_of_each_person(
            original, group
        )
    for variable in ("council_tax", "employment_income", "region", "income_tax"):
        assert (
            reloaded.calculate(variable, YEAR).tolist()
            == original.calculate(variable, YEAR).tolist()
        )


def warned(frame_: pd.DataFrame, tax_benefit_system) -> list:
    """The rounding warnings loading ``frame_`` gives."""
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        dataset_from_input_dataframe(frame_, tax_benefit_system, YEAR)
    return [
        str(each.message) for each in caught if "may share one" in str(each.message)
    ]


def test_large_float_person_columns_alone_give_a_warning(tax_benefit_system):
    # 64-bit floats hold these identifiers exactly, but if they were saved
    # from the model's 32-bit person_household_id, neighbouring households
    # were rounded to one before the frame was made, which no check can see.
    large = pd.DataFrame(
        {
            "person_id__2025": [1, 2],
            "person_household_id__2025": [900_000_000.0, 900_000_064.0],
        }
    )
    messages = warned(large, tax_benefit_system)
    assert len(messages) == 1
    assert "'person_household_id__2025'" in messages[0]
    assert "'household_id' column" in messages[0]

    with_own = large.assign(household_id__2025=[900_000_001, 900_000_064])
    small = large.assign(person_household_id__2025=[1.0, 2.0])
    integers = large.assign(person_household_id__2025=[900_000_001, 900_000_064])
    for frame_ in (with_own, small, integers):
        assert warned(frame_, tax_benefit_system) == []


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


def test_exact_floats_that_share_a_32_bit_float_must_still_agree():
    # 900,000,001 and 900,000,002 are the same 32-bit float, but these 64-bit
    # floats hold them exactly, and neither is that 32-bit float (900,000,000)
    # as the model exports it or as CSV writes it. So they name the other
    # household, not a rounded copy of the person's own.
    refused(
        couple(
            **{
                "household_id__2025": [900_000_001, 900_000_002],
                "person_household_id__2025": [900_000_002.0, 900_000_001.0],
            }
        ),
        "put the person in row 0 in different groups",
    )


def test_object_person_columns_are_checked_value_by_value():
    # Each value of a mixed column is read at its own precision: the 32-bit
    # float agrees with household 900,000,001 as its rounded copy, and the
    # other values must name the person's household too.
    households = {"household_id__2025": [900_000_001, 900_000_002]}
    agreeing = pd.Series([np.float32(900_000_001), 900_000_002], dtype=object)
    simulation = Simulation(
        dataset=couple(**households, **{"person_household_id__2025": agreeing})
    )
    assert group_of_each_person(simulation, "household") == [
        900_000_001,
        900_000_002,
    ]

    for wrong in (np.float32(900_000_128), 900_000_128.0, 900_000_001, "a"):
        named = pd.Series([np.float32(900_000_001), wrong], dtype=object)
        refused(
            couple(**households, **{"person_household_id__2025": named}),
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

    tables, *_ = dataset_from_input_dataframe(frame_, tax_benefit_system, YEAR)

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
    # Saved as CSV, the rounded person_ columns come back as 64-bit floats.
    from_csv = pd.read_csv(io.StringIO(exported.to_csv(index=False)))
    assert_holds(Simulation(dataset=from_csv), population)


@TABLE_SETTINGS
@given(population=populations(), id_columns=id_columns, data=st.data())
def test_tables_hold_the_frame_in_any_row_order(
    tax_benefit_system, population, id_columns, data
):
    order = data.draw(st.permutations(range(len(population.person_ids))))
    reordered = population.reordered(order)

    tables, other_inputs, _ = dataset_from_input_dataframe(
        frame(population, id_columns), tax_benefit_system, YEAR
    )
    reordered_tables, *_ = dataset_from_input_dataframe(
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

    tables, *_ = dataset_from_input_dataframe(frame_, tax_benefit_system, YEAR)
    plain, *_ = dataset_from_input_dataframe(
        frame(population), tax_benefit_system, YEAR
    )

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
        tables, *_ = dataset_from_input_dataframe(frame_, tax_benefit_system, YEAR)
        assert_tables_hold(tables[YEAR], population)
    else:
        with pytest.raises(ValueError, match="as 32-bit floats"):
            dataset_from_input_dataframe(frame_, tax_benefit_system, YEAR)


# Each way an identifier can be written in an object column.
REPRESENTATIONS = {
    "int": int,
    "int32": np.int32,
    "int64": np.int64,
    "float64": float,
    "float32": np.float32,
}


@TABLE_SETTINGS
@given(
    population=populations(),
    id_columns=st.sampled_from(["both", "own", "person"]),
    data=st.data(),
)
def test_identifiers_of_mixed_types_never_merge_people_or_groups(
    tax_benefit_system, population, id_columns, data
):
    # 1. Each identifier is written as a Python or NumPy integer or float, in
    # object columns. The frame loads its people and groups exactly, or is
    # refused, just when an identifier it reads them from is a 32-bit float
    # that may stand for more than one whole number.
    frame_ = frame(population, id_columns)
    people = len(population.person_ids)
    group_source = "" if id_columns in ("both", "own") else "person_"
    sources = {"person_id"} | {f"{group_source}{group}_id" for group in GROUPS}
    ambiguous = False
    for column in list(frame_.columns):
        variable, _ = split_column(column)
        if variable not in IDENTIFIER_VARIABLES:
            continue
        kinds = data.draw(
            st.lists(
                st.sampled_from(sorted(REPRESENTATIONS)),
                min_size=people,
                max_size=people,
            )
        )
        written = [
            REPRESENTATIONS[kind](value)
            for kind, value in zip(kinds, frame_[column].tolist())
        ]
        frame_[column] = pd.Series(written, dtype=object)
        ambiguous |= variable in sources and any(
            kind == "float32" and abs(value) >= FLOAT32_EXACT_LIMIT
            for kind, value in zip(kinds, written)
        )

    if ambiguous:
        with pytest.raises(ValueError, match="as 32-bit floats"):
            dataset_from_input_dataframe(frame_, tax_benefit_system, YEAR)
    else:
        tables, *_ = dataset_from_input_dataframe(frame_, tax_benefit_system, YEAR)
        assert_tables_hold(tables[YEAR], population)


def legacy_build_from_dataframe(self, df: pd.DataFrame) -> None:
    """``Simulation.build_from_dataframe`` before #2266, unchanged."""

    def get_first_array(variable_name: str) -> pd.Series:
        columns = df.columns[df.columns.str.contains(variable_name + "__")]
        return df[columns[0]]

    self.build_from_ids(
        *map(
            get_first_array,
            [
                "person_id",
                "person_benunit_id",
                "person_household_id",
                "benunit_id",
                "household_id",
            ],
        )
    )
    for column in df:
        variable, time_period = column.split("__")
        if variable not in self.tax_benefit_system.variables:
            continue
        self.set_input(variable, time_period, df[column])


MONTHS = [f"{YEAR}-{month:02d}" for month in range(1, 13)]
# Monthly inputs: one whose yearly value is divided between the months not
# yet set, and one whose yearly value is given to each of them.
MONTHLY_VARIABLES = {
    "ni_class_1_employee": st.integers(0, 400).map(float),
    "ebr_energy_bills_credit_eligible": st.booleans(),
}


@st.composite
def frames_the_previous_loader_read(draw) -> pd.DataFrame:
    """Frames of single-person benefit units and households, with rows in
    order of identifier, and monthly inputs given for some months and perhaps
    the year, in any column order."""
    people = draw(st.integers(1, 4))
    person_ids = np.array(
        sorted(draw(st.sets(st.integers(1, 60), min_size=people, max_size=people)))
    )
    columns = {
        f"person_id__{YEAR}": person_ids,
        f"person_benunit_id__{YEAR}": person_ids + 100,
        f"person_household_id__{YEAR}": person_ids + 200,
        f"benunit_id__{YEAR}": person_ids + 100,
        f"household_id__{YEAR}": person_ids + 200,
    }

    def given(strategy) -> list:
        return draw(st.lists(strategy, min_size=people, max_size=people))

    inputs = {
        f"age__{YEAR}": given(st.integers(0, 90)),
        f"council_tax__{YEAR}": given(st.integers(0, 5_000).map(float)),
        f"would_claim_uc__{YEAR}": given(st.booleans()),
        f"region__{YEAR}": given(st.sampled_from(REGIONS)),
        f"age__{YEAR + 1}": given(st.integers(0, 90)),
    }
    for variable, strategy in MONTHLY_VARIABLES.items():
        months = draw(st.lists(st.sampled_from(MONTHS), max_size=4, unique=True))
        periods = months + ([str(YEAR)] if draw(st.booleans()) else [])
        for period in periods:
            inputs[f"{variable}__{period}"] = given(strategy)
    order = draw(st.permutations(sorted(inputs)))
    columns.update({column: inputs[column] for column in order})
    return pd.DataFrame(columns)


@SIMULATION_SETTINGS
@given(frame_=frames_the_previous_loader_read())
def test_frames_the_previous_loader_read_give_the_same_inputs(frame_):
    # 9. Differential against the previous loader, on the frames it read
    # correctly.
    current = Simulation(dataset=frame_)
    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.setattr(
            Simulation, "build_from_dataframe", legacy_build_from_dataframe
        )
        previous = Simulation(dataset=frame_)

    for column in frame_.columns:
        variable, period = split_column(column)
        periods = [period]
        if variable in MONTHLY_VARIABLES and f"{variable}__{YEAR}" in frame_:
            # The yearly value set every month.
            periods = MONTHS
        for each in periods:
            ours = np.asarray(current.calculate(variable, each))
            theirs = np.asarray(previous.calculate(variable, each))
            assert ours.tolist() == theirs.tolist(), (variable, each)
