from pathlib import Path

import pytest

import policyengine_uk.simulation as simulation_module
from policyengine_uk import Simulation


class _StopDatasetLoad(Exception):
    pass


@pytest.mark.parametrize(
    "dataset_source_factory",
    [str, lambda dataset_path: dataset_path],
    ids=["str", "pathlike"],
)
def test_simulation_routes_local_dataset_path_to_file_loader(
    monkeypatch, tmp_path, dataset_source_factory
):
    captured = {}
    dataset_path = tmp_path / "dataset.h5"

    def fake_build_from_file(self, dataset_file, *, cache_key=None):
        captured["dataset_file"] = dataset_file
        captured["cache_key"] = cache_key
        raise _StopDatasetLoad

    monkeypatch.setattr(Simulation, "build_from_file", fake_build_from_file)

    with pytest.raises(_StopDatasetLoad):
        Simulation(dataset=dataset_source_factory(dataset_path))

    assert captured == {
        "dataset_file": str(dataset_path),
        "cache_key": None,
    }


def test_dataset_source_routes_huggingface_urls_to_url_loader(monkeypatch):
    captured = {}
    simulation = Simulation.__new__(Simulation)
    url = "hf://policyengine/policyengine-uk-data/enhanced_frs_2022_23.h5"

    def fake_build_from_url(dataset_url):
        captured["url"] = dataset_url

    def fake_build_from_file(dataset_file, *, cache_key=None):
        raise AssertionError("HuggingFace URLs should not be treated as local files.")

    monkeypatch.setattr(simulation, "build_from_url", fake_build_from_url)
    monkeypatch.setattr(simulation, "build_from_file", fake_build_from_file)

    Simulation.build_from_dataset_source(simulation, url)

    assert captured == {"url": url}


def test_dataset_source_rejects_unsupported_remote_urls():
    simulation = Simulation.__new__(Simulation)

    with pytest.raises(ValueError, match="Only HuggingFace dataset URLs"):
        Simulation.build_from_dataset_source(
            simulation,
            "gs://policyengine-uk-data-private/enhanced_frs_2023_24.h5",
        )


def test_build_from_file_loads_local_multi_year_dataset(monkeypatch, tmp_path):
    cache_key = "hf://policyengine/policyengine-uk-data/enhanced_frs_2022_23.h5"
    dataset_path = tmp_path / "dataset.h5"
    built = {}

    class FakeMultiYearDataset:
        @staticmethod
        def validate_file_path(file_path, raise_exception=False):
            built["validated_file_path"] = file_path
            built["raise_exception"] = raise_exception
            return True

        def __init__(self, file_path):
            self.file_path = file_path

    def fake_build_from_multi_year_dataset(dataset):
        built["dataset"] = dataset

    simulation_module._url_dataset_cache.pop(cache_key, None)
    monkeypatch.setattr(simulation_module, "UKMultiYearDataset", FakeMultiYearDataset)
    monkeypatch.setattr(
        simulation_module, "_pre_encode_enum_columns", lambda dataset, tbs: None
    )

    simulation = Simulation.__new__(Simulation)
    simulation.tax_benefit_system = object()
    monkeypatch.setattr(
        simulation,
        "build_from_multi_year_dataset",
        fake_build_from_multi_year_dataset,
    )

    try:
        Simulation.build_from_file(simulation, Path(dataset_path), cache_key=cache_key)

        assert built["validated_file_path"] == str(dataset_path)
        assert built["raise_exception"] is False
        assert built["dataset"].file_path == str(dataset_path)
        assert simulation.dataset is built["dataset"]
        assert simulation_module._url_dataset_cache[cache_key] is built["dataset"]
    finally:
        simulation_module._url_dataset_cache.pop(cache_key, None)
