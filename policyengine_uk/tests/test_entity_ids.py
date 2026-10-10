"""Entity identifiers read back from a simulation exactly as they were given.

A simulation built from data stores each identifier column as the values of a
variable: ``person_id``, ``person_benunit_id``, ``person_household_id``,
``benunit_id`` and ``household_id``. ``calculate``, ``to_input_dataframe`` and
``UKSingleYearDataset.from_simulation`` return those stored values, and
``Simulation.build_from_dataset`` rebuilds the entities from the last of them.
``person_benunit_id`` and ``person_household_id`` used to be stored as 32-bit
floats, which hold whole numbers exactly only up to 2**24, so larger
identifiers read back rounded and a rebuild merged the households that shared
a rounded value (PolicyEngine/policyengine-uk#2267).

Invariants, for identifiers that are whole numbers from -2**31 to 2**31 - 1
(the range of the 32-bit integers that store them):

1. ``calculate``, ``to_input_dataframe`` and
   ``UKSingleYearDataset.from_simulation`` return every identifier column
   exactly, as integers, whether the dataset holds it as integers or floats.
2. The stored memberships equal the populations' memberships: a person's
   ``person_household_id`` is the identifier of the household the populations
   place the person in, and likewise for benefit units.
3. The entity structure is the one the dataset's tables describe, whatever
   the size of the identifiers.
4. A simulation built from a policyengine-core dataset file, which is rebuilt
   from its own export, has that same structure and those same identifiers.
5. ``check_entity_ids`` passes exactly the arrays that the storing variable's
   dtype holds unchanged, and gives an ``EntityIdWarning`` for any other. So
   building a simulation warns when an identifier is outside the range or not
   a whole number, and stays silent otherwise (this module turns the warning
   into an error, so every test above checks that).
6. Identifiers outside the range still give the entity structure the tables
   describe: the populations take them as given.

The group tables are sorted by identifier, as ``build_from_ids`` numbers the
benefit units and households in that order, and every group has a member.
"""

import warnings

import h5py
import numpy as np
import pandas as pd
import pytest
from hypothesis import example, given, settings
from hypothesis import strategies as st

from policyengine_uk import Microsimulation
from policyengine_uk.data import UKMultiYearDataset, UKSingleYearDataset
from policyengine_uk.system import system
from policyengine_uk.utils.entity_ids import (
    ENTITY_ID_VARIABLES,
    EntityIdWarning,
    check_entity_ids,
)

pytestmark = [
    pytest.mark.usefixtures("cloned_uk_tax_benefit_system"),
    # An identifier the simulation cannot store exactly warns. Outside the
    # tests that expect it, the warning fails the test.
    pytest.mark.filterwarnings(
        "error::policyengine_uk.utils.entity_ids.EntityIdWarning"
    ),
]

YEAR = 2025
ID_MIN, ID_MAX = -(2**31), 2**31 - 1
# The first whole number a 32-bit float cannot hold is 2**24 + 1.
FLOAT32_EXACT_LIMIT = 2**24
# Three households that a 32-bit float stores as the same number, 900,000,000.
ISSUE_IDS = [900_000_001, 900_000_002, 900_000_003]

# The person table's column that holds each identifier once per person.
PERSON_LEVEL_COLUMN = {
    "person_id": "person_id",
    "person_benunit_id": "person_benunit_id",
    "person_household_id": "person_household_id",
    "benunit_id": "person_benunit_id",
    "household_id": "person_household_id",
}

identifiers = st.one_of(
    st.integers(ID_MIN, ID_MAX),
    st.integers(ID_MAX - 40, ID_MAX),
    st.integers(ID_MIN, ID_MIN + 40),
    st.integers(FLOAT32_EXACT_LIMIT - 20, FLOAT32_EXACT_LIMIT + 40),
    st.integers(900_000_000, 900_000_040),
    st.integers(0, 40),
)


def tables(person_ids, person_benunit_ids, person_household_ids, id_dtype="int64"):
    """Person, benefit unit and household tables for the given memberships.

    The household table holds the columns that extending a dataset to later
    years reads.
    """
    person = pd.DataFrame(
        {
            "person_id": person_ids,
            "person_benunit_id": person_benunit_ids,
            "person_household_id": person_household_ids,
        }
    ).astype(id_dtype)
    person["age"] = 40
    benunit = pd.DataFrame({"benunit_id": sorted(set(person_benunit_ids))})
    household = pd.DataFrame({"household_id": sorted(set(person_household_ids))})
    household = household.astype(id_dtype).assign(
        household_weight=1.0,
        region="LONDON",
        rent=0.0,
        tenure_type="OWNED_OUTRIGHT",
        council_tax=0.0,
    )
    return person, benunit.astype(id_dtype), household


@st.composite
def memberships(draw):
    """Up to four households of one to three benefit units of one to three
    people, with distinct identifiers of any size and people in any order."""
    sizes = draw(
        st.lists(
            st.lists(st.integers(1, 3), min_size=1, max_size=3),
            min_size=1,
            max_size=4,
        )
    )
    benunit_household = [h for h, units in enumerate(sizes) for _ in units]
    benunit_sizes = [size for units in sizes for size in units]
    person_benunit = [b for b, size in enumerate(benunit_sizes) for _ in range(size)]

    def distinct(count):
        return draw(st.lists(identifiers, min_size=count, max_size=count, unique=True))

    household_ids = distinct(len(sizes))
    benunit_ids = distinct(len(benunit_sizes))
    person_ids = distinct(len(person_benunit))
    order = draw(st.permutations(range(len(person_benunit))))
    return (
        [person_ids[i] for i in order],
        [benunit_ids[person_benunit[i]] for i in order],
        [household_ids[benunit_household[person_benunit[i]]] for i in order],
    )


def simulate(person, benunit, household, years=(YEAR,)):
    """A simulation of the tables as given, with no uprating to other years."""
    return Microsimulation(
        dataset=UKMultiYearDataset(
            datasets=[
                UKSingleYearDataset(
                    person=person.copy(),
                    benunit=benunit.copy(),
                    household=household.copy(),
                    fiscal_year=year,
                )
                for year in years
            ]
        )
    )


def write_core_dataset_file(path, person, benunit, household):
    """Save the tables as policyengine-core stores a dataset: one array per
    variable and period, with text as bytes."""
    with h5py.File(path, "w") as file:
        for table in (person, benunit, household):
            for column in table.columns:
                values = table[column].to_numpy()
                if values.dtype.kind == "O":
                    values = values.astype("S")
                file.create_dataset(f"{column}/{YEAR}", data=values)
    return str(path)


def whole(values) -> list[int]:
    return [int(value) for value in values]


def expected_identifiers(person, benunit, household) -> dict[str, list[int]]:
    return {
        "person_id": whole(person.person_id),
        "person_benunit_id": whole(person.person_benunit_id),
        "person_household_id": whole(person.person_household_id),
        "benunit_id": whole(benunit.benunit_id),
        "household_id": whole(household.household_id),
    }


def stored(sim, variable: str, year: int = YEAR) -> list[int]:
    """The variable's stored values, which must be integers."""
    values = np.asarray(sim.calculate(variable, year))
    assert values.dtype.kind == "i", (variable, values.dtype)
    return values.tolist()


def rows_in_group_table(group_ids, person_group_ids) -> list[int]:
    """The row of each person's group in the group table."""
    row = {int(identifier): index for index, identifier in enumerate(group_ids)}
    return [row[int(identifier)] for identifier in person_group_ids]


def assert_structure_matches_tables(sim, person, benunit, household):
    """Invariant 3: the populations hold the tables' memberships."""
    assert sim.populations["person"].ids.tolist() == whole(person.person_id)
    for entity, group_ids, person_group_ids in (
        ("benunit", benunit.benunit_id, person.person_benunit_id),
        ("household", household.household_id, person.person_household_id),
    ):
        population = sim.populations[entity]
        assert population.ids.tolist() == whole(group_ids)
        assert population.members_entity_id.tolist() == rows_in_group_table(
            group_ids, person_group_ids
        )


def assert_stored_memberships_match_populations(sim, year: int = YEAR):
    """Invariant 2: the stored memberships are the populations' memberships."""
    for entity in ("benunit", "household"):
        population = sim.populations[entity]
        from_populations = population.ids[population.members_entity_id].tolist()
        assert stored(sim, f"person_{entity}_id", year) == from_populations
        assert stored(sim, f"{entity}_id", year) == population.ids.tolist()


def assert_identifiers_read_back(sim, person, benunit, household, years=(YEAR,)):
    """Invariant 1, for each way of reading the stored identifiers."""
    expected = expected_identifiers(person, benunit, household)
    frame = sim.to_input_dataframe()
    for year in years:
        for variable in ENTITY_ID_VARIABLES:
            assert stored(sim, variable, year) == expected[variable], variable

        # One row per person, so a group's identifier repeats for each member.
        for variable in ENTITY_ID_VARIABLES:
            column = frame[f"{variable}__{year}"]
            assert column.dtype.kind == "i", (variable, column.dtype)
            assert column.tolist() == expected[PERSON_LEVEL_COLUMN[variable]], variable

        export = UKSingleYearDataset.from_simulation(sim, fiscal_year=year)
        for table, variables in (
            (export.person, ENTITY_ID_VARIABLES[:3]),
            (export.benunit, ("benunit_id",)),
            (export.household, ("household_id",)),
        ):
            for variable in variables:
                assert table[variable].dtype.kind == "i", (variable, table.dtypes)
                assert table[variable].tolist() == expected[variable], variable


@pytest.mark.parametrize("variable", ENTITY_ID_VARIABLES)
def test_identifier_variables_are_stored_as_integers(variable):
    """All five identifier variables share one integer store, so a membership
    column can hold any identifier its group's own column can."""
    definition = system.variables[variable]
    assert definition.value_type is int
    assert definition.dtype == system.variables["household_id"].dtype
    assert np.iinfo(definition.dtype).min <= ID_MIN
    assert np.iinfo(definition.dtype).max >= ID_MAX


@given(members=memberships(), id_dtype=st.sampled_from(["int64", "float64"]))
@example(members=(ISSUE_IDS, ISSUE_IDS, ISSUE_IDS), id_dtype="int64")
@example(
    members=(
        [ID_MAX, ID_MAX - 1, ID_MIN, ID_MIN + 1],
        [ID_MAX, ID_MAX, ID_MIN, ID_MAX - 1],
        [ID_MAX, ID_MAX, ID_MIN, ID_MAX],
    ),
    id_dtype="float64",
)
@example(
    members=(
        [1, 2, 3],
        [FLOAT32_EXACT_LIMIT + 1, FLOAT32_EXACT_LIMIT, FLOAT32_EXACT_LIMIT + 1],
        [FLOAT32_EXACT_LIMIT + 1, FLOAT32_EXACT_LIMIT, FLOAT32_EXACT_LIMIT + 1],
    ),
    id_dtype="int64",
)
@settings(max_examples=30, deadline=None)
def test_identifiers_in_range_read_back_exactly(members, id_dtype):
    """Invariants 1 to 3 for a simulation built from entity tables."""
    person, benunit, household = tables(*members, id_dtype=id_dtype)
    sim = simulate(person, benunit, household)
    assert_structure_matches_tables(sim, person, benunit, household)
    assert_stored_memberships_match_populations(sim)
    assert_identifiers_read_back(sim, person, benunit, household)


@given(members=memberships(), id_dtype=st.sampled_from(["int64", "float64"]))
@example(members=(ISSUE_IDS, ISSUE_IDS, ISSUE_IDS), id_dtype="float64")
@settings(max_examples=10, deadline=None)
def test_core_dataset_file_builds_the_tables_structure(
    members, id_dtype, tmp_path_factory
):
    """Invariant 4. ``build_from_dataset`` builds the entities, exports them
    with ``UKSingleYearDataset.from_simulation`` and rebuilds from the export,
    so a rounded membership column changed who lives with whom."""
    person, benunit, household = tables(*members, id_dtype=id_dtype)
    path = write_core_dataset_file(
        tmp_path_factory.mktemp("core_dataset") / "dataset.h5",
        person,
        benunit,
        household,
    )
    sim = Microsimulation(dataset=path)
    assert_structure_matches_tables(sim, person, benunit, household)
    assert_stored_memberships_match_populations(sim)
    expected = expected_identifiers(person, benunit, household)
    for variable in ENTITY_ID_VARIABLES:
        assert stored(sim, variable) == expected[variable], variable


@pytest.fixture(scope="module")
def issue_tables():
    return tables(ISSUE_IDS, ISSUE_IDS, ISSUE_IDS)


@pytest.fixture(scope="module")
def issue_simulation(cloned_uk_tax_benefit_system, issue_tables):
    """The reproduction in the issue: a single-year dataset, which the
    simulation extends to later years."""
    person, benunit, household = issue_tables
    return Microsimulation(
        dataset=UKSingleYearDataset(
            person=person.copy(),
            benunit=benunit.copy(),
            household=household.copy(),
            fiscal_year=YEAR,
        )
    )


def test_issue_reproduction_reads_back_in_every_year(issue_simulation, issue_tables):
    years = issue_simulation.dataset.years
    assert len(years) > 1
    assert_identifiers_read_back(issue_simulation, *issue_tables, years=years)
    for year in years:
        assert_stored_memberships_match_populations(issue_simulation, year)


def test_issue_reproduction_keeps_three_households(issue_simulation):
    assert stored(issue_simulation, "person_household_id") == ISSUE_IDS
    assert stored(issue_simulation, "person_benunit_id") == ISSUE_IDS
    assert stored(issue_simulation, "household_count_people") == [1, 1, 1]


def test_core_dataset_file_keeps_households_apart(tmp_path):
    """A policyengine-core dataset file with float identifiers, as an older
    UK dataset has. Before the fix its three one-person households loaded as
    one household of three and two empty households."""
    person, benunit, household = tables(
        ISSUE_IDS, ISSUE_IDS, ISSUE_IDS, id_dtype="float64"
    )
    path = write_core_dataset_file(tmp_path / "dataset.h5", person, benunit, household)
    sim = Microsimulation(dataset=path)
    assert sim.populations["household"].members_entity_id.tolist() == [0, 1, 2]
    assert sim.populations["benunit"].members_entity_id.tolist() == [0, 1, 2]
    assert stored(sim, "household_count_people") == [1, 1, 1]
    assert stored(sim, "person_household_id") == ISSUE_IDS


def test_exported_frame_rebuilds_the_same_households(issue_simulation):
    """A frame from ``to_input_dataframe`` rebuilds the households it came
    from. Each household here has one person: a frame with a larger household
    does not load yet (PolicyEngine/policyengine-uk#2266)."""
    rebuilt = Microsimulation(dataset=issue_simulation.to_input_dataframe())
    assert rebuilt.populations["household"].ids.tolist() == ISSUE_IDS
    assert rebuilt.populations["household"].members_entity_id.tolist() == [0, 1, 2]
    assert rebuilt.populations["benunit"].members_entity_id.tolist() == [0, 1, 2]
    assert stored(rebuilt, "person_household_id") == ISSUE_IDS
    assert stored(rebuilt, "household_count_people") == [1, 1, 1]


def test_float32_identifier_columns_load_when_they_are_whole():
    """A 32-bit float column is exact below 2**24, and loads as integers."""
    ids = [FLOAT32_EXACT_LIMIT - 2, FLOAT32_EXACT_LIMIT - 1, FLOAT32_EXACT_LIMIT]
    person, benunit, household = tables(ids, ids, ids, id_dtype="float32")
    sim = simulate(person, benunit, household)
    assert_identifiers_read_back(sim, person, benunit, household)


def storable_values(variable: str):
    """Arrays of the kinds an identifier column can have, in and out of the
    storing variable's range, including floats that are not whole numbers."""
    limits = np.iinfo(system.variables[variable].dtype)
    near_limits = st.one_of(
        st.integers(limits.min - 3, limits.min + 3),
        st.integers(limits.max - 3, limits.max + 3),
        st.integers(-(2**24) - 3, 2**24 + 3),
    )

    def integers(dtype):
        bounds = np.iinfo(dtype)
        return st.lists(
            st.one_of(
                st.integers(bounds.min, bounds.max),
                near_limits.map(lambda value: min(max(value, bounds.min), bounds.max)),
            ),
            max_size=6,
        ).map(lambda values: np.array(values, dtype=dtype))

    def floats(dtype):
        return st.lists(
            st.one_of(
                near_limits.map(float),
                st.floats(allow_nan=True, allow_infinity=True, width=32),
                st.floats(min_value=-(2.0**33), max_value=2.0**33),
            ),
            max_size=6,
        ).map(lambda values: np.array(values, dtype=dtype))

    return st.one_of(
        integers(np.int64),
        integers(np.int32),
        integers(np.uint32),
        integers(np.uint64),
        floats(np.float64),
        floats(np.float32),
    )


def held_unchanged(values: np.ndarray, dtype) -> bool:
    """Whether policyengine-core's cast to the variable's dtype
    (``Holder._to_array``) keeps every value."""
    with warnings.catch_warnings():
        # NumPy warns when a float is outside the integer range.
        warnings.simplefilter("ignore", RuntimeWarning)
        cast = values.astype(dtype)
    # Python compares integers with floats exactly; NaN equals nothing.
    return cast.tolist() == values.tolist()


@pytest.mark.parametrize("variable", ENTITY_ID_VARIABLES)
@given(data=st.data())
@settings(max_examples=300, deadline=None)
def test_check_warns_exactly_when_the_store_changes_a_value(variable, data):
    """Invariant 5, against the cast that stores the values."""
    definition = system.variables[variable]
    values = data.draw(storable_values(variable))
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        exact = check_entity_ids(definition, values)
    ours = [w for w in caught if issubclass(w.category, EntityIdWarning)]
    assert exact == held_unchanged(values, definition.dtype), values
    assert len(ours) == (0 if exact else 1)
    assert all(variable in str(w.message) for w in ours)


def test_check_leaves_other_kinds_of_identifier_to_the_store():
    """Text and other non-numeric identifiers are not checked here;
    policyengine-core reports those it cannot store."""
    definition = system.variables["person_id"]
    assert check_entity_ids(definition, np.array(["a", "b"]))
    assert check_entity_ids(definition, np.array([True, False]))
    assert check_entity_ids(definition, np.array([], dtype=np.float64))


OUT_OF_RANGE_IDS = [ID_MAX - 1, ID_MAX, ID_MAX + 1]
MEMBERSHIP_VARIABLES = {
    "person": {"person_id"},
    "benunit": {"person_benunit_id", "benunit_id"},
    "household": {"person_household_id", "household_id"},
}


def warned_variables(build):
    """Run ``build`` and return it with the variables it warned about."""
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        result = build()
    messages = [
        str(w.message) for w in caught if issubclass(w.category, EntityIdWarning)
    ]
    return result, {message.split()[0] for message in messages}


@pytest.mark.parametrize("entity", ["person", "benunit", "household"])
@pytest.mark.parametrize("id_dtype", ["int64", "float64"])
def test_identifier_above_the_range_warns_and_keeps_the_structure(entity, id_dtype):
    """Invariants 5 and 6 for an identifier one above the range, whichever
    entity it names. Only the columns that hold it warn."""
    ids = {name: [1, 2, 3] for name in ("person", "benunit", "household")}
    ids[entity] = OUT_OF_RANGE_IDS
    person, benunit, household = tables(
        ids["person"], ids["benunit"], ids["household"], id_dtype=id_dtype
    )
    sim, warned = warned_variables(lambda: simulate(person, benunit, household))
    assert warned == MEMBERSHIP_VARIABLES[entity]
    assert_structure_matches_tables(sim, person, benunit, household)


def test_identifier_below_the_range_warns_and_keeps_the_structure():
    ids = [ID_MIN - 1, ID_MIN, ID_MIN + 1]
    person, benunit, household = tables(ids, ids, ids)
    sim, warned = warned_variables(lambda: simulate(person, benunit, household))
    assert warned == set(ENTITY_ID_VARIABLES)
    assert_structure_matches_tables(sim, person, benunit, household)


def test_identifier_that_is_not_a_whole_number_warns():
    person, benunit, household = tables([1, 2, 3], [1, 2, 3], [1, 2, 3], "float64")
    person["person_household_id"] = [1.0, 2.5, 3.0]
    with pytest.warns(EntityIdWarning, match="person_household_id should hold whole"):
        simulate(person, benunit, household)


def test_single_year_dataset_warns_about_an_identifier_out_of_range():
    person, benunit, household = tables(
        OUT_OF_RANGE_IDS, OUT_OF_RANGE_IDS, OUT_OF_RANGE_IDS
    )
    dataset = UKSingleYearDataset(
        person=person.copy(),
        benunit=benunit.copy(),
        household=household.copy(),
        fiscal_year=YEAR,
    )
    sim, warned = warned_variables(lambda: Microsimulation(dataset=dataset))
    assert warned == set(ENTITY_ID_VARIABLES)
    assert_structure_matches_tables(sim, person, benunit, household)


def test_core_dataset_file_warns_about_an_identifier_out_of_range(tmp_path):
    """The rebuild from the export reads the stored identifiers, which differ
    from the given ones, but each household keeps its one person."""
    person, benunit, household = tables(
        OUT_OF_RANGE_IDS, OUT_OF_RANGE_IDS, OUT_OF_RANGE_IDS
    )
    path = write_core_dataset_file(tmp_path / "dataset.h5", person, benunit, household)
    sim, warned = warned_variables(lambda: Microsimulation(dataset=path))
    assert warned == set(ENTITY_ID_VARIABLES)
    for entity in ("benunit", "household"):
        members = sim.populations[entity].members_entity_id
        assert np.bincount(members, minlength=3).tolist() == [1, 1, 1]


def test_frame_warns_about_an_identifier_out_of_range():
    frame = pd.DataFrame(
        {f"{variable}__{YEAR}": OUT_OF_RANGE_IDS for variable in ENTITY_ID_VARIABLES}
    ).assign(**{f"age__{YEAR}": 40})
    sim, warned = warned_variables(lambda: Microsimulation(dataset=frame))
    assert warned == set(ENTITY_ID_VARIABLES)
    assert sim.populations["household"].ids.tolist() == OUT_OF_RANGE_IDS
    assert sim.populations["household"].members_entity_id.tolist() == [0, 1, 2]
