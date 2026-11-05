"""Explicit energy price provenance; unlabelled datasets retain flat amounts."""

import hashlib
import json
from types import SimpleNamespace

import h5py
import pandas as pd
import pytest

from policyengine_uk.data import UKMultiYearDataset, UKSingleYearDataset
from policyengine_uk.data.filter_dataset import filter_dataset


def single(basis=None, year=2024):
    return UKSingleYearDataset(
        person=pd.DataFrame(
            {
                "person_id": [1, 2],
                "person_benunit_id": [1, 2],
                "person_household_id": [1, 2],
                "months_since_last_birthday": [3, 8],
                "attends_private_school": [False, False],
            }
        ),
        benunit=pd.DataFrame({"benunit_id": [1, 2]}),
        household=pd.DataFrame(
            {"household_id": [1, 2], "domestic_energy_consumption": [100.0, 200.0]}
        ),
        fiscal_year=year,
        energy_price_basis=basis,
    )


@pytest.mark.parametrize("period_type", ["calendar_year", "fiscal_year"])
def test_constructor_preserves_the_declared_price_period(period_type):
    declaration = {"period_type": period_type, "period_value": 2024}
    dataset = UKSingleYearDataset(
        person=pd.DataFrame(
            {"person_id": [1], "person_benunit_id": [1], "person_household_id": [1]}
        ),
        benunit=pd.DataFrame({"benunit_id": [1]}),
        household=pd.DataFrame({"household_id": [1]}),
        fiscal_year=2024,
        energy_price_basis=declaration,
    )
    assert dataset.energy_price_basis == declaration
    declaration["period_value"] = 2026
    assert dataset.energy_price_basis == {
        "period_type": period_type,
        "period_value": 2024,
    }
    exposed = dataset.energy_price_basis
    exposed["period_value"] = 2030
    assert dataset.energy_price_basis["period_value"] == 2024


@pytest.mark.parametrize("year", [1, 9999])
def test_supported_integer_year_boundaries(year):
    declaration = {"period_type": "calendar_year", "period_value": year}
    assert single(declaration).energy_price_basis == declaration


@pytest.mark.parametrize(
    "declaration",
    [
        {},
        {"period_type": "calendar_year"},
        {"period_value": 2024},
        {"period_type": "month", "period_value": 2024},
        {"period_type": "calendar_year", "period_value": True},
        {"period_type": "calendar_year", "period_value": False},
        {"period_type": "calendar_year", "period_value": "2024"},
        {"period_type": "calendar_year", "period_value": 2024.0},
        {"period_type": "calendar_year", "period_value": 2024.5},
        {"period_type": "calendar_year", "period_value": 0},
        {"period_type": "calendar_year", "period_value": 10000},
        {"period_type": "calendar_year", "period_value": 2024, "legacy": True},
        "calendar_year:2024",
        ["calendar_year", 2024],
        2024,
    ],
)
def test_malformed_explicit_declarations_fail_clearly(declaration):
    with pytest.raises(ValueError, match="energy_price_basis"):
        single(declaration)


@pytest.mark.parametrize("period_type", ["calendar_year", "fiscal_year"])
def test_single_copy_and_h5_roundtrip_preserve_kind_and_values(tmp_path, period_type):
    declaration = {"period_type": period_type, "period_value": 2024}
    source = single(declaration)
    copied = source.copy()
    path = tmp_path / "arbitrary-name.h5"
    copied.save(path)
    with h5py.File(path, "r") as file:
        assert json.loads(file.attrs["energy_price_basis"]) == declaration
    loaded = UKSingleYearDataset(file_path=path)
    for item in (source, copied, loaded):
        assert item.energy_price_basis == declaration
        pd.testing.assert_frame_equal(item.household, source.household)
    copied.energy_price_basis = None
    assert source.energy_price_basis == declaration
    assert loaded.energy_price_basis == declaration


def test_unlabelled_file_remains_readable_and_can_be_labelled_explicitly(tmp_path):
    path = tmp_path / "fiscal-2099-producer-name-is-not-a-declaration.h5"
    source = single()
    source.save(path)
    before = hashlib.sha256(path.read_bytes()).hexdigest()
    with h5py.File(path, "r") as file:
        assert "energy_price_basis" not in file.attrs
    assert UKSingleYearDataset(file_path=path).energy_price_basis is None
    declaration = {"period_type": "calendar_year", "period_value": 2024}
    labelled = UKSingleYearDataset(file_path=path, energy_price_basis=declaration)
    assert labelled.energy_price_basis == declaration
    assert source.energy_price_basis is None
    assert hashlib.sha256(path.read_bytes()).hexdigest() == before


def test_stored_declaration_agrees_with_caller_or_fails_on_conflict(tmp_path):
    declaration = {"period_type": "calendar_year", "period_value": 2024}
    path = tmp_path / "labelled.h5"
    single(declaration).save(path)
    for caller in (None, declaration):
        assert (
            UKSingleYearDataset(
                file_path=path, energy_price_basis=caller
            ).energy_price_basis
            == declaration
        )
    for conflicting in (
        {"period_type": "fiscal_year", "period_value": 2024},
        {"period_type": "calendar_year", "period_value": 2025},
    ):
        with pytest.raises(ValueError, match="energy_price_basis"):
            UKSingleYearDataset(file_path=path, energy_price_basis=conflicting)


@pytest.mark.parametrize(
    "stored",
    ["not JSON", "[]", "2024", '{"period_type":"fiscal_year"}', 2024],
)
def test_malformed_persisted_declaration_fails_clearly(tmp_path, stored):
    path = tmp_path / "invalid.h5"
    single().save(path)
    with h5py.File(path, "a") as file:
        file.attrs["energy_price_basis"] = stored
    with pytest.raises(ValueError, match="energy_price_basis"):
        UKSingleYearDataset(file_path=path)


def test_multi_copy_and_h5_keep_each_year_declaration(tmp_path):
    declarations = {
        2024: {"period_type": "calendar_year", "period_value": 2024},
        2025: {"period_type": "fiscal_year", "period_value": 2025},
        2026: None,
    }
    source = UKMultiYearDataset(
        datasets=[single(basis, year) for year, basis in declarations.items()]
    )
    copied = source.copy()
    path = tmp_path / "several-years.h5"
    copied.save(path)
    loaded = UKMultiYearDataset(file_path=path)
    for year, declaration in declarations.items():
        for item in (source, copied, loaded):
            assert item[year].energy_price_basis == declaration
            pd.testing.assert_frame_equal(item[year].household, source[year].household)
    copied[2024].energy_price_basis = None
    assert source[2024].energy_price_basis == declarations[2024]
    assert loaded[2024].energy_price_basis == declarations[2024]


def test_filtered_household_preserves_the_observations_price_basis():
    declaration = {"period_type": "calendar_year", "period_value": 2024}
    source = single(declaration)
    simulation = SimpleNamespace(dataset=UKMultiYearDataset(datasets=[source]))
    filtered = filter_dataset(simulation, household_id=2, year=2024)
    assert filtered.energy_price_basis == declaration
    assert filtered.household["domestic_energy_consumption"].tolist() == [200.0]
    assert filtered.person.person_id.tolist() == [2]
    assert source.household.household_id.tolist() == [1, 2]
