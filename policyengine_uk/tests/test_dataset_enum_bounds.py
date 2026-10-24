"""Integer enum inputs are zero-based positions, never survey source codes."""

from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest
from policyengine_core.enums import Enum

import policyengine_uk.simulation as simulation_module
from policyengine_uk import Simulation
from policyengine_uk.data import UKMultiYearDataset, UKSingleYearDataset
from policyengine_uk.simulation import _pre_encode_enum_columns
from policyengine_uk.system import system

pytestmark = pytest.mark.usefixtures("cloned_uk_tax_benefit_system")


class Band(Enum):
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    E = "E"
    F = "F"
    G = "G"
    H = "H"
    I = "I"


class WithUnknown(Enum):
    KNOWN = "Known"
    UNKNOWN = "Unknown"


def single(codes, year=2025):
    count = len(codes)
    ids = np.arange(1, count + 1)
    return UKSingleYearDataset(
        person=pd.DataFrame(
            {
                "person_id": ids,
                "person_benunit_id": ids,
                "person_household_id": ids,
                "age": 40,
            }
        ),
        benunit=pd.DataFrame({"benunit_id": ids}),
        household=pd.DataFrame(
            {"household_id": ids, "household_weight": 1.0, "council_tax_band": codes}
        ),
        fiscal_year=year,
    )


def enum_system(**extra):
    return SimpleNamespace(
        variables={
            "council_tax_band": SimpleNamespace(value_type=Enum, possible_values=Band),
            **{
                name: SimpleNamespace(value_type=Enum, possible_values=enum)
                for name, enum in extra.items()
            },
        }
    )


INVALID = [
    pytest.param(np.array([-1], dtype=np.int64), "-1", id="negative"),
    pytest.param(np.array([9], dtype=np.int64), "9", id="upper-bound"),
    pytest.param(np.array([10], dtype=np.int64), "10", id="above-bound"),
    pytest.param(
        np.array([np.iinfo(np.int64).min]),
        str(np.iinfo(np.int64).min),
        id="signed-minimum",
    ),
    pytest.param(
        np.array([np.iinfo(np.uint64).max], dtype=np.uint64),
        str(np.iinfo(np.uint64).max),
        id="unsigned-maximum",
    ),
    pytest.param(np.array([0, 8, 9], dtype=np.uint64), "9", id="mixed-valid-invalid"),
]


def assert_context(error, enum_name="Band", bad=None):
    message = str(error.value)
    assert "council_tax_band" in message
    assert enum_name in message
    if bad is not None:
        assert bad in message


@pytest.mark.parametrize("codes,bad", INVALID)
def test_preencoding_rejects_invalid_positions_with_context(codes, bad):
    dataset = single(codes.copy())
    before = dataset._household.copy(deep=True)
    with pytest.raises(ValueError) as error:
        _pre_encode_enum_columns(UKMultiYearDataset(datasets=[dataset]), enum_system())
    assert_context(error, bad=bad)
    pd.testing.assert_frame_equal(dataset._household, before)


@pytest.mark.parametrize("codes,bad", INVALID)
def test_decoding_rejects_invalid_positions_with_context(codes, bad):
    dataset = single(codes.copy())
    dataset._enum_columns = {"council_tax_band": Band}
    before = dataset._household.copy(deep=True)
    with pytest.raises(ValueError) as error:
        dataset.household
    assert_context(error, bad=bad)
    pd.testing.assert_frame_equal(dataset._household, before)


@pytest.mark.parametrize("dtype", [np.int8, np.int64, np.uint64])
@pytest.mark.parametrize("values,expected", [([0, 8], ["A", "I"]), ([], [])])
def test_valid_endpoints_and_empty_integer_arrays_are_preserved(
    dtype, values, expected
):
    dataset = single(np.array(values, dtype=dtype))
    original = dataset._household.copy(deep=True)
    _pre_encode_enum_columns(UKMultiYearDataset(datasets=[dataset]), enum_system())
    assert dataset.household.council_tax_band.tolist() == expected
    pd.testing.assert_frame_equal(dataset._household, original)


def test_in_range_integers_are_positions_not_one_based_source_codes():
    assert [
        item.name for item in system.variables["council_tax_band"].possible_values
    ] == list("ABCDEFGHI")
    dataset = single(np.array([1, 4, 8]))
    _pre_encode_enum_columns(UKMultiYearDataset(datasets=[dataset]), enum_system())
    assert dataset.household.council_tax_band.tolist() == ["B", "E", "I"]


@pytest.mark.parametrize("codes", [["A", "I"], [Band.A, Band.I]])
def test_names_and_enum_members_keep_their_meaning(codes):
    dataset = single(codes)
    _pre_encode_enum_columns(UKMultiYearDataset(datasets=[dataset]), enum_system())
    assert dataset.household.council_tax_band.tolist() == ["A", "I"]
    assert dataset._household.council_tax_band.tolist() == [0, 8]


def test_real_unknown_member_and_non_enum_columns_remain_valid():
    dataset = single(np.array([0, 8]))
    dataset._person["sample_status"] = np.array([0, 1], dtype=np.uint64)
    original_ids = dataset._person.person_id.copy()
    _pre_encode_enum_columns(
        UKMultiYearDataset(datasets=[dataset]), enum_system(sample_status=WithUnknown)
    )
    assert dataset.person.sample_status.tolist() == ["KNOWN", "UNKNOWN"]
    pd.testing.assert_series_equal(dataset._person.person_id, original_ids)


@pytest.mark.parametrize(
    "codes", [np.array([True]), np.array([1.5]), np.array([np.nan]), np.array(["1"])]
)
def test_existing_non_integer_invalid_inputs_are_not_coerced(codes):
    with pytest.raises(ValueError):
        _pre_encode_enum_columns(
            UKMultiYearDataset(datasets=[single(codes)]), enum_system()
        )


def test_integer_preflight_precedes_other_enum_column_conversion():
    dataset = single(np.array([-1]))
    dataset._person["first_enum"] = ["A"]
    before = [frame.copy(deep=True) for frame in dataset.tables]
    with pytest.raises(ValueError):
        _pre_encode_enum_columns(
            UKMultiYearDataset(datasets=[dataset]), enum_system(first_enum=Band)
        )
    for actual, expected in zip(dataset.tables, before):
        pd.testing.assert_frame_equal(actual, expected)
    assert dataset._enum_columns == {}


def test_all_years_are_preflighted_before_earlier_year_conversion():
    earlier = single(["A"])
    later = single(np.array([9], dtype=np.uint64), year=2026)
    original = earlier._household.copy(deep=True)
    with pytest.raises(ValueError):
        _pre_encode_enum_columns(
            UKMultiYearDataset(datasets=[earlier, later]), enum_system()
        )
    pd.testing.assert_frame_equal(earlier._household, original)
    assert earlier._enum_columns == {}


@pytest.mark.parametrize("preencoded", [False, True])
def test_public_multiyear_ingestion_rejects_invalid_later_year(preencoded):
    earlier = single(np.array([0]))
    later = single(np.array([9]), year=2026)
    if preencoded:
        earlier._enum_columns = {
            "council_tax_band": system.variables["council_tax_band"].possible_values
        }
    with pytest.raises(ValueError) as error:
        Simulation(dataset=UKMultiYearDataset(datasets=[earlier, later]))
    assert_context(error, "CouncilTaxBand", "9")


@pytest.mark.parametrize("single_year", [False, True])
def test_public_ingestion_and_decoded_round_trip_preserve_valid_positions(
    monkeypatch, single_year
):
    dataset = single(np.array([0, 8], dtype=np.uint64))
    if single_year:
        monkeypatch.setattr(
            Simulation,
            "_extend_dataset_with_cgt_provenance",
            lambda self, value: UKMultiYearDataset(datasets=[value]),
        )
        source = dataset
    else:
        source = UKMultiYearDataset(datasets=[dataset])
    simulation = Simulation(dataset=source)
    assert simulation.calculate("council_tax_band", 2025).tolist() == ["A", "I"]
    assert simulation.dataset[2025].household.council_tax_band.tolist() == ["A", "I"]
    assert simulation.dataset[2025]._household.council_tax_band.tolist() == [0, 8]


def test_invalid_file_input_does_not_publish_a_cache_entry(tmp_path, monkeypatch):
    simulation = Simulation(
        dataset=UKMultiYearDataset(datasets=[single(np.array([0]))])
    )
    invalid = single(np.array([-1]))
    invalid._household["region"] = "LONDON"
    invalid._household["tenure_type"] = "OWNED_OUTRIGHT"
    invalid._household["council_tax"] = 0.0
    invalid._household["rent"] = 0.0
    path = str(tmp_path / "invalid.h5")
    invalid.save(path)
    key = "unit-test-invalid-enum"
    monkeypatch.setattr(simulation, "_dataset_cache_key", lambda value: value)
    monkeypatch.setattr(simulation_module, "_url_dataset_cache", {})
    with pytest.raises(ValueError) as error:
        simulation.build_from_file(path, cache_key=key)
    assert_context(error, "CouncilTaxBand", "-1")
    assert key not in simulation_module._url_dataset_cache


def test_cached_preencoded_input_is_not_trusted_without_validation(monkeypatch):
    simulation = Simulation(
        dataset=UKMultiYearDataset(datasets=[single(np.array([0]))])
    )
    invalid = single(np.array([-1]))
    invalid._enum_columns = {
        "council_tax_band": system.variables["council_tax_band"].possible_values
    }
    cached = UKMultiYearDataset(datasets=[invalid])
    key = "gs://synthetic-enum-test/input.h5"
    monkeypatch.setattr(simulation, "_dataset_cache_key", lambda value: value)
    monkeypatch.setattr(simulation_module, "_url_dataset_cache", {key: cached})
    monkeypatch.setattr(
        simulation_module,
        "materialize_gcs_dataset_url",
        lambda value: pytest.fail("a cache hit must not download"),
    )
    with pytest.raises(ValueError) as error:
        simulation.build_from_dataset_source(key)
    assert_context(error, "CouncilTaxBand", "-1")
    assert simulation_module._url_dataset_cache[key] is cached
