"""Integer enum inputs: where the loader reads them as positions, and where it
refuses them (PolicyEngine/policyengine-uk#2602).

``Simulation.to_input_dataframe`` exports an enum as 0-based positions, and a
policyengine-core dataset can hold them too, so a DataFrame and a Core
dataset still give positions, and the loader checks each one. Every dataset
policyengine-uk-data builds, and every one policyengine-uk saves, holds
member names, so the loader refuses integers in a ``UKSingleYearDataset``, a
``UKMultiYearDataset`` and their saved files. There a survey code can't pass
as a position.

The issue's survey codes run from 1, while ``CouncilTaxBand`` positions run
from 0 (A) to 8 (I).
"""

import re
from types import SimpleNamespace

import h5py
import numpy as np
import pandas as pd
import pytest
from hypothesis import given, settings, strategies as st
from hypothesis.extra.numpy import arrays
from policyengine_core.enums import Enum

import policyengine_uk.simulation as simulation_module
from policyengine_uk import Simulation
from policyengine_uk.data import UKMultiYearDataset, UKSingleYearDataset
from policyengine_uk.data.input_dataframe import dataset_from_input_dataframe
from policyengine_uk.simulation import _pre_encode_enum_columns
from policyengine_uk.system import system

pytestmark = pytest.mark.usefixtures("cloned_uk_tax_benefit_system")

YEAR = 2025
BANDS = list("ABCDEFGHI")
# Loaders that read a dataset's tables, which hold names.
REFUSING = ["single", "multi", "single_h5", "multi_h5"]
# Loaders that read positions, as the exports that write them do; each names
# the column as its source does.
ACCEPTING = {
    "dataframe": f"council_tax_band__{YEAR}",
    "core_h5": "council_tax_band",
}


def issue_dataset(bands, year=YEAR) -> UKSingleYearDataset:
    """The issue's dataset: one person per household, each in a band."""
    count = len(bands)
    ids = np.arange(count)
    return UKSingleYearDataset(
        person=pd.DataFrame(
            {
                "person_id": ids,
                "person_benunit_id": ids,
                "person_household_id": ids,
                "age": [40] * count,
            }
        ),
        benunit=pd.DataFrame({"benunit_id": ids}),
        household=pd.DataFrame(
            {
                "household_id": ids,
                "household_weight": [1.0] * count,
                "council_tax_band": bands,
                "region": ["LONDON"] * count,
                "council_tax": [1500.0] * count,
                "rent": [0.0] * count,
                "tenure_type": ["RENT_PRIVATELY"] * count,
                "accommodation_type": ["FLAT"] * count,
            }
        ),
        fiscal_year=year,
    )


def columns(data: UKSingleYearDataset):
    for table in data.tables:
        for column in table.columns:
            yield column, table[column].to_numpy()


def source(path: str, bands, tmp_path):
    """The issue's dataset as the loader ``path`` reads it."""
    data = issue_dataset(bands)
    if path == "single":
        return data
    if path == "multi":
        return UKMultiYearDataset(datasets=[data])
    if path in ("single_h5", "multi_h5"):
        file = tmp_path / f"{path}.h5"
        (data if path == "single_h5" else UKMultiYearDataset(datasets=[data])).save(
            file
        )
        return str(file)
    if path == "dataframe":
        # One person per benefit unit and household, so each table's rows are
        # the people's.
        return pd.DataFrame(
            {f"{column}__{YEAR}": values for column, values in columns(data)}
        )
    # The policyengine-core time-period-array layout.
    file = tmp_path / "core.h5"
    with h5py.File(file, "w") as h5:
        for column, values in columns(data):
            if values.dtype == object:
                values = values.astype("S")
            h5.create_dataset(f"{column}/{YEAR}", data=values)
    return str(file)


def bands_of(simulation) -> list:
    return simulation.calculate("council_tax_band", YEAR).tolist()


# The issue's three cases, on each loader.


@pytest.mark.parametrize("path", REFUSING + list(ACCEPTING))
def test_a_name_the_enum_lacks_is_refused_on_every_path(path, tmp_path):
    with pytest.raises(ValueError) as error:
        Simulation(dataset=source(path, np.array(["A", "10"]), tmp_path))
    assert str(error.value).startswith(
        "Invalid value(s) ['10'] for enum CouncilTaxBand. Valid values are: "
    )


@pytest.mark.parametrize("path", REFUSING)
@pytest.mark.parametrize("codes", [[1, 4, 8], [1, 4, 9, 10]])
def test_integers_are_refused_where_datasets_hold_names(path, codes, tmp_path):
    with pytest.raises(ValueError) as error:
        Simulation(dataset=source(path, np.array(codes), tmp_path))
    shown = ", ".join(map(str, codes))
    assert str(error.value) == (
        f"Column 'council_tax_band' holds integers ({shown}), but a dataset's "
        "enum CouncilTaxBand column takes member names, such as 'A', 'B', 'C', "
        "'D', 'E', 'F', 'G', 'H', 'I'. Map source codes to names before loading."
    )


@pytest.mark.parametrize("path", ACCEPTING)
def test_in_range_codes_read_as_positions_where_exports_write_them(path, tmp_path):
    # Nothing tells a 1-based code that falls in range from a position: each
    # band reads one too high, as the loader's docstrings warn.
    simulation = Simulation(dataset=source(path, np.array([1, 4, 8]), tmp_path))
    assert bands_of(simulation) == ["B", "E", "I"]


@pytest.mark.parametrize("path,column", ACCEPTING.items())
def test_codes_past_the_last_position_are_refused_by_name(path, column, tmp_path):
    with pytest.raises(ValueError) as error:
        Simulation(dataset=source(path, np.array([1, 4, 9, 10]), tmp_path))
    assert str(error.value) == (
        f"Column '{column}' holds positions that enum CouncilTaxBand lacks: "
        "9, 10. The model reads an integer as a 0-based position, from "
        "0 (A) to 8 (I). Map source codes to member names, such as 'A', 'B', 'C', "
        "'D', 'E', 'F', 'G', 'H', 'I', before loading."
    )


@pytest.mark.parametrize("path", REFUSING + list(ACCEPTING))
def test_names_load_on_every_path(path, tmp_path):
    simulation = Simulation(dataset=source(path, np.array(["A", "E", "I"]), tmp_path))
    assert bands_of(simulation) == ["A", "E", "I"]


# Missing values keep the errors they gave before. A NumPy integer array
# can't hold NaN, so a column with a missing value arrives as floats or
# objects. A single-year dataset's projection refuses it
# (UKSingleYearDataset.validate); elsewhere Core's encoder does.

MISSING = {
    "float NaN": np.array([1.0, np.nan]),
    "object NaN": np.array(["A", np.nan], dtype=object),
    "None": np.array(["A", None], dtype=object),
}


@pytest.mark.parametrize("path", ["single", "multi", "dataframe", "core_h5"])
@pytest.mark.parametrize("case", MISSING)
def test_missing_values_keep_their_errors(path, case, tmp_path):
    if path == "single":
        message = re.escape("Column 'council_tax_band' contains NaN values.")
    elif case == "float NaN":
        message = re.escape("Unsupported array dtype: float64")
    else:
        # pandas 3 reads None in a string column as NaN.
        message = r"Invalid value\(s\) \['(nan|None)'\] for enum CouncilTaxBand\."
    with pytest.raises(ValueError, match=message):
        Simulation(dataset=source(path, MISSING[case], tmp_path))


# The loader checks each column once.


def counting_checks(monkeypatch) -> list:
    """Record each column the loader checks or refuses."""
    calls = []
    for name in ("check_enum_positions", "refuse_enum_integers"):
        original = getattr(simulation_module, name)

        def counted(values, possible_values, column, original=original):
            calls.append(column)
            return original(values, possible_values, column)

        monkeypatch.setattr(simulation_module, name, counted)
    return calls


def test_a_loaded_dataset_loads_again_without_another_check(monkeypatch):
    simulation = Simulation(dataset=issue_dataset(np.array(["A", "E", "I"])))
    calls = counting_checks(monkeypatch)
    again = Simulation(dataset=simulation.dataset)
    assert bands_of(again) == ["A", "E", "I"]
    assert simulation.dataset[YEAR].household.council_tax_band.tolist() == [
        "A",
        "E",
        "I",
    ]
    assert calls == []


def test_an_exported_frame_gives_back_its_bands():
    simulation = Simulation(dataset=issue_dataset(np.array(["A", "E", "I"])))
    exported = simulation.to_input_dataframe()
    assert exported[f"council_tax_band__{YEAR}"].dtype.kind == "i"
    reloaded = Simulation(dataset=exported)
    assert bands_of(reloaded) == ["A", "E", "I"]
    # The loaded dataset saves names, which a dataset file needs.
    assert reloaded.dataset[YEAR].household.council_tax_band.tolist() == [
        "A",
        "E",
        "I",
    ]


def test_a_replaced_table_is_checked_again():
    data = Simulation(dataset=issue_dataset(np.array(["A", "E", "I"]))).dataset[YEAR]
    household = data.household.copy()
    household["council_tax_band"] = [1, 4, 8]
    data.household = household
    with pytest.raises(ValueError, match="holds integers \\(1, 4, 8\\)"):
        Simulation(dataset=data)


def test_every_year_is_checked_before_any_table_changes():
    names = issue_dataset(np.array(["A", "E"]))
    codes = issue_dataset(np.array([1, 4]), year=YEAR + 1)
    before = names._household.copy()
    with pytest.raises(ValueError, match="holds integers \\(1, 4\\)"):
        _pre_encode_enum_columns(UKMultiYearDataset(datasets=[names, codes]), system)
    pd.testing.assert_frame_equal(names._household, before)
    assert names._enum_columns == {}


class Order(Enum):
    X = "x"
    Y = "y"
    Z = "z"


class Reordered(Enum):
    Z = "z"
    Y = "y"
    X = "x"


def enum_system(possible_values) -> SimpleNamespace:
    """A model with one person-level enum variable, ``code``."""
    return SimpleNamespace(
        variables={
            "code": SimpleNamespace(
                entity=SimpleNamespace(key="person"),
                value_type=Enum,
                possible_values=possible_values,
            )
        }
    )


def person_dataset(values, year=YEAR) -> UKSingleYearDataset:
    ids = np.arange(len(values))
    return UKSingleYearDataset(
        person=pd.DataFrame({"person_id": ids, "code": values}),
        benunit=pd.DataFrame({"benunit_id": ids}),
        household=pd.DataFrame({"household_id": ids}),
        fiscal_year=year,
    )


def test_positions_recorded_under_a_redeclared_enum_keep_their_names():
    # A structural reform can declare the enum again in another order.
    data = person_dataset(np.array(["X", "Z"]))
    _pre_encode_enum_columns(UKMultiYearDataset(datasets=[data]), enum_system(Order))
    assert data._person.code.tolist() == [0, 2]
    _pre_encode_enum_columns(
        UKMultiYearDataset(datasets=[data]), enum_system(Reordered)
    )
    assert data._person.code.tolist() == [2, 0]
    assert data.person.code.tolist() == ["X", "Z"]


def test_a_year_recorded_under_a_redeclared_enum_projects_its_names():
    data = person_dataset(np.array(["X", "Z"]))
    _pre_encode_enum_columns(UKMultiYearDataset(datasets=[data]), enum_system(Order))
    # The single-year loaders check before projecting; a recorded column
    # passes, and the projection's copy reads it by its recorded enum.
    simulation_module._refuse_unchecked_enum_integers(data, enum_system(Reordered))
    assert data.copy().person.code.tolist() == ["X", "Z"]


def test_every_enum_of_the_model_reads_its_positions_from_a_frame():
    for name, variable in system.variables.items():
        if variable.value_type != Enum:
            continue
        members = [member.name for member in variable.possible_values]
        count = len(members)
        frame = pd.DataFrame(
            {
                f"person_id__{YEAR}": np.arange(count),
                f"{name}__{YEAR}": np.arange(count, dtype=np.int16),
            }
        )
        dataset, _, _ = dataset_from_input_dataframe(frame, system, YEAR)
        _pre_encode_enum_columns(dataset, system)
        table = getattr(dataset[YEAR], variable.entity.key)
        assert table[name].tolist() == members, name
        frame[f"{name}__{YEAR}"] = count
        with pytest.raises(ValueError, match=f"lacks: {count}\\. The model"):
            dataset_from_input_dataframe(frame, system, YEAR)


# Properties, for any enum and any integer array.

DTYPES = [
    np.int8,
    np.int16,
    np.int32,
    np.int64,
    np.uint8,
    np.uint16,
    np.uint32,
    np.uint64,
]


@st.composite
def enums_and_integers(draw):
    """An enum of 1 to 300 members, and integers of any dtype, mostly near
    its positions."""
    names = draw(
        st.lists(
            st.from_regex(r"[A-Z][A-Z0-9_]{0,5}", fullmatch=True),
            min_size=1,
            max_size=300,
            unique=True,
        )
    )
    possible_values = Enum("Drawn", [(name, name.lower()) for name in names])
    dtype = np.dtype(draw(st.sampled_from(DTYPES)))
    limits = np.iinfo(dtype)
    near = st.integers(-2, len(names) + 2).filter(
        lambda value: limits.min <= value <= limits.max
    )
    values = draw(
        arrays(
            dtype,
            st.integers(1, 30),
            elements=st.one_of(near, near, near, st.integers(limits.min, limits.max)),
        )
    )
    return possible_values, values


def frame_dataset(values, possible_values):
    """Load a frame with one enum column, ``code``, as Simulation does."""
    model = enum_system(possible_values)
    frame = pd.DataFrame(
        {f"person_id__{YEAR}": np.arange(len(values)), f"code__{YEAR}": values}
    )
    dataset, _, _ = dataset_from_input_dataframe(frame, model, YEAR)
    _pre_encode_enum_columns(dataset, model)
    return dataset[YEAR].person.code.tolist()


@settings(max_examples=300, deadline=None)
@given(enums_and_integers())
def test_positions_load_as_their_names_or_are_refused_by_name(drawn):
    possible_values, values = drawn
    members = [member.name for member in possible_values]
    out_of_range = sorted({int(v) for v in values if not 0 <= v < len(members)})
    if out_of_range:
        with pytest.raises(ValueError) as error:
            frame_dataset(values, possible_values)
        message = str(error.value)
        shown = ", ".join(map(str, out_of_range[:10]))
        assert message.startswith(
            f"Column 'code__{YEAR}' holds positions that enum Drawn lacks: {shown}"
        )
        return
    names = [members[value] for value in values]
    assert frame_dataset(values, possible_values) == names
    # Passing the names gives the same names.
    assert frame_dataset(np.array(names, dtype=object), possible_values) == names
    # Differential: Core's decoder reads the positions the same way.
    assert possible_values.encode(values).decode_to_str().tolist() == names


@settings(max_examples=300, deadline=None)
@given(enums_and_integers())
def test_dataset_tables_refuse_every_integer_and_load_names(drawn):
    possible_values, values = drawn
    model = enum_system(possible_values)
    data = person_dataset(values)
    before = data._person.copy()
    with pytest.raises(ValueError) as error:
        _pre_encode_enum_columns(UKMultiYearDataset(datasets=[data]), model)
    shown = ", ".join(map(str, sorted({int(v) for v in values})[:10]))
    assert str(error.value).startswith(f"Column 'code' holds integers ({shown}")
    assert "enum Drawn column takes member names" in str(error.value)
    pd.testing.assert_frame_equal(data._person, before)
    # In range, the names load as the members the positions would name.
    in_range = values[(values >= 0) & (values < len(possible_values))]
    members = [member.name for member in possible_values]
    names = np.array([members[value] for value in in_range], dtype=object)
    data = person_dataset(names)
    _pre_encode_enum_columns(UKMultiYearDataset(datasets=[data]), model)
    assert data.person.code.tolist() == names.tolist()
