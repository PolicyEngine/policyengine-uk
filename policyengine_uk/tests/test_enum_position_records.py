"""The loader's records of the enum columns it encoded
(PolicyEngine/policyengine-uk#2602).

A record says how the loader encoded a column, never that the column's
values are still positions of its enum: each load checks a recorded column's
integers against the enum it recorded, and replacing a table drops the
records of the columns it held.
"""

import re

import h5py
import numpy as np
import pytest
from policyengine_core.enums import Enum

import policyengine_uk.simulation as simulation_module
from policyengine_uk import Simulation
from policyengine_uk.data import UKMultiYearDataset, UKSingleYearDataset
from policyengine_uk.simulation import _pre_encode_enum_columns
from policyengine_uk.system import system
from policyengine_uk.tests.test_enum_integer_inputs import (
    ACCEPTING,
    YEAR,
    Order,
    bands_of,
    columns,
    enum_system,
    issue_dataset,
    person_dataset,
    source,
)

pytestmark = pytest.mark.usefixtures("cloned_uk_tax_benefit_system")


def loaded(bands) -> tuple:
    """Load the issue's dataset as the loader does, and return the year and
    the multi-year dataset holding it."""
    data = issue_dataset(np.array(bands))
    years = UKMultiYearDataset(datasets=[data])
    _pre_encode_enum_columns(years, system)
    return data, years


def refusal(values: str) -> str:
    return re.escape(f"Column 'council_tax_band' holds integers ({values}), but")


def lacks(enum: str, values: str) -> str:
    return re.escape(
        f"Column 'council_tax_band' holds positions that enum {enum} lacks: "
        f"{values}. The model"
    )


# Replacing a table drops the records of the columns it held.


@pytest.mark.parametrize("value", [1, -1, 9])
def test_an_enum_column_dropped_and_put_back_as_integers_is_refused(value):
    data, years = loaded(["A"])
    data.household = data.household.drop(columns=["council_tax_band"])
    # The view of a table without a recorded column is the table itself.
    data.household["council_tax_band"] = [value]
    with pytest.raises(ValueError, match=refusal(str(value))):
        _pre_encode_enum_columns(years, system)


def test_a_simulation_refuses_a_dropped_column_put_back_as_integers():
    data, years = loaded(["A"])
    data.household = data.household.drop(columns=["council_tax_band"])
    data.household["council_tax_band"] = [1]
    with pytest.raises(ValueError, match=refusal("1")):
        Simulation(dataset=years)


def test_a_table_set_from_its_own_positions_is_refused():
    # The setter can't tell the loader's positions from a caller's codes.
    data, years = loaded(["E"])
    data.household = data._household.copy()
    with pytest.raises(ValueError, match=refusal("4")):
        _pre_encode_enum_columns(years, system)


def test_replacing_one_table_keeps_the_records_of_the_others():
    data, years = loaded(["E"])
    data.person = data.person.assign(age=41)
    _pre_encode_enum_columns(years, system)
    assert data.household.council_tax_band.tolist() == ["E"]
    assert data._household.council_tax_band.tolist() == [4]


# Each load checks a recorded column against the enum it recorded.


@pytest.mark.parametrize("value", [-1, 9, 2**40])
def test_a_recorded_column_changed_after_loading_is_refused_by_name(value):
    data, years = loaded(["A", "E"])
    data.tables[2]["council_tax_band"] = np.array([0, value], dtype=np.int64)
    with pytest.raises(ValueError, match=lacks("CouncilTaxBand", str(value))):
        data.household
    with pytest.raises(ValueError, match=lacks("CouncilTaxBand", str(value))):
        _pre_encode_enum_columns(years, system)
    with pytest.raises(ValueError, match=lacks("CouncilTaxBand", str(value))):
        Simulation(dataset=years)


class Shrunk(Enum):
    Z = "z"
    X = "x"


def test_a_shrunk_enum_keeps_the_members_it_retains():
    data = person_dataset(np.array(["X", "Z"]))
    years = UKMultiYearDataset(datasets=[data])
    _pre_encode_enum_columns(years, enum_system(Order))
    assert data._person.code.tolist() == [0, 2]
    # Position 2 (Z) reaches past Shrunk's two members, but names a member
    # Shrunk keeps.
    simulation_module._check_enum_columns(years, enum_system(Shrunk))
    assert data.copy().person.code.tolist() == ["X", "Z"]
    _pre_encode_enum_columns(years, enum_system(Shrunk))
    assert data._person.code.tolist() == [1, 0]
    assert data.person.code.tolist() == ["X", "Z"]


def test_a_shrunk_enum_refuses_a_member_it_drops():
    data = person_dataset(np.array(["Y"]))
    years = UKMultiYearDataset(datasets=[data])
    _pre_encode_enum_columns(years, enum_system(Order))
    with pytest.raises(ValueError, match=re.escape("Invalid value(s) ['Y'] for enum")):
        _pre_encode_enum_columns(years, enum_system(Shrunk))
    assert data._person.code.tolist() == [1]
    assert data._enum_columns == {"code": Order}


def test_a_recorded_column_is_checked_against_its_recorded_enum():
    data = person_dataset(np.array(["X", "Z"]))
    years = UKMultiYearDataset(datasets=[data])
    _pre_encode_enum_columns(years, enum_system(Order))
    data.tables[0]["code"] = np.array([0, 3], dtype=np.int16)
    message = re.escape("Column 'code' holds positions that enum Order lacks: 3.")
    with pytest.raises(ValueError, match=message):
        simulation_module._check_enum_columns(years, enum_system(Shrunk))
    with pytest.raises(ValueError, match=message):
        _pre_encode_enum_columns(years, enum_system(Shrunk))


# The positional loaders check integers at the width they arrive in, before
# anything narrows them to int16, where 65536 and 2**40 would read as A.


@pytest.mark.parametrize("path", list(ACCEPTING))
@pytest.mark.parametrize("wide", [65536, 2**40])
def test_wide_integers_are_refused_before_anything_narrows_them(path, wide, tmp_path):
    assert np.array([wide]).astype(np.int16).tolist() == [0]
    with pytest.raises(ValueError) as error:
        Simulation(dataset=source(path, np.array([0, wide], dtype=np.int64), tmp_path))
    assert str(error.value).startswith(
        f"Column '{ACCEPTING[path]}' holds positions that enum CouncilTaxBand "
        f"lacks: {wide}. The model"
    )


@pytest.mark.parametrize("wide", [65536, 2**40])
def test_a_wide_scalar_in_a_core_file_is_refused(wide, tmp_path):
    file = tmp_path / "core.h5"
    with h5py.File(file, "w") as h5:
        for column, values in columns(issue_dataset(np.array(["A"]))):
            if column == "council_tax_band":
                values = np.int64(wide)
            elif values.dtype == object:
                values = values.astype("S")
            h5.create_dataset(f"{column}/{YEAR}", data=values)
    with pytest.raises(ValueError, match=lacks("CouncilTaxBand", str(wide))):
        Simulation(dataset=str(file))


# The loader encodes into the dataset's own tables.


def test_frames_another_dataset_shares_keep_their_names():
    data = issue_dataset(np.array(["A", "E"]))
    person, benunit, household = data.tables
    first = UKSingleYearDataset(
        person=person, benunit=benunit, household=household, fiscal_year=YEAR
    )
    _pre_encode_enum_columns(UKMultiYearDataset(datasets=[first]), system)
    assert first._household.council_tax_band.tolist() == [0, 4]
    assert household.council_tax_band.tolist() == ["A", "E"]
    second = UKSingleYearDataset(
        person=person, benunit=benunit, household=household, fiscal_year=YEAR
    )
    simulation = Simulation(dataset=UKMultiYearDataset(datasets=[second]))
    assert bands_of(simulation) == ["A", "E"]
    assert household.council_tax_band.tolist() == ["A", "E"]
