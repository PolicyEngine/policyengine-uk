from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace

import numpy as np
import pytest
from hypothesis import example, given, settings
from hypothesis import strategies as st

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


def _current_law_system():
    """A stand-in system with current law's parameters: the URL cache is used
    only by simulations whose dataset uprating inputs are current law's."""
    from policyengine_uk.tax_benefit_system import system

    return SimpleNamespace(capital_gains_projection=None, parameters=system.parameters)


def test_dataset_source_routes_gcs_urls_to_materialized_file(monkeypatch):
    captured = {}
    simulation = Simulation.__new__(Simulation)
    simulation.tax_benefit_system = _current_law_system()
    url = "gs://policyengine-uk-data-private/enhanced_frs_2023_24.h5@1.55.10"

    def fake_materialize_gcs_dataset_url(dataset_url):
        captured["url"] = dataset_url
        return "/tmp/enhanced_frs_2023_24.h5"

    def fake_build_from_file(dataset_file, *, cache_key=None):
        captured["dataset_file"] = dataset_file
        captured["cache_key"] = cache_key

    monkeypatch.setattr(
        simulation_module,
        "materialize_gcs_dataset_url",
        fake_materialize_gcs_dataset_url,
    )
    monkeypatch.setattr(simulation, "build_from_file", fake_build_from_file)

    Simulation.build_from_dataset_source(simulation, url)

    assert captured == {
        "url": url,
        "dataset_file": "/tmp/enhanced_frs_2023_24.h5",
        "cache_key": url,
    }


def test_dataset_source_reuses_cached_gcs_dataset_before_materializing(monkeypatch):
    captured = {}
    cached_dataset = object()
    simulation = Simulation.__new__(Simulation)
    simulation.tax_benefit_system = _current_law_system()
    url = "gs://policyengine-uk-data-private/enhanced_frs_2023_24.h5@1.55.10"

    def fake_materialize_gcs_dataset_url(dataset_url):
        raise AssertionError("Cached gs:// datasets should not be materialized.")

    def fake_build_from_file(dataset_file, *, cache_key=None):
        raise AssertionError("Cached gs:// datasets should not be read from disk.")

    def fake_build_from_multi_year_dataset(dataset):
        captured["dataset"] = dataset

    simulation_module._url_dataset_cache.pop(url, None)
    simulation_module._url_dataset_cache[url] = cached_dataset
    monkeypatch.setattr(
        simulation_module,
        "materialize_gcs_dataset_url",
        fake_materialize_gcs_dataset_url,
    )
    monkeypatch.setattr(simulation, "build_from_file", fake_build_from_file)
    monkeypatch.setattr(
        simulation,
        "build_from_multi_year_dataset",
        fake_build_from_multi_year_dataset,
    )

    try:
        Simulation.build_from_dataset_source(simulation, url)

        assert captured["dataset"] is cached_dataset
        assert simulation.dataset is cached_dataset
    finally:
        simulation_module._url_dataset_cache.pop(url, None)


def test_dataset_source_rejects_unsupported_remote_urls():
    simulation = Simulation.__new__(Simulation)

    with pytest.raises(ValueError, match="Only HuggingFace, Google Cloud Storage"):
        Simulation.build_from_dataset_source(
            simulation,
            "s3://policyengine-uk-data-private/enhanced_frs_2023_24.h5",
        )


@pytest.mark.usefixtures("cloned_uk_tax_benefit_system")
def test_build_from_file_loads_local_multi_year_dataset(tmp_path):
    """Files written by either UK schema dispatch without validator stubs."""
    from policyengine_uk.data import UKMultiYearDataset, UKSingleYearDataset
    from policyengine_uk.data.economic_assumptions import extend_single_year_dataset

    single = _single_person_dataset()
    multi = extend_single_year_dataset(
        single, _current_law_system().parameters, end_year=2028
    )
    multi_path = str(tmp_path / "multi.h5")
    multi.save(multi_path)

    assert UKMultiYearDataset.validate_file_path(multi_path, True)
    assert not UKSingleYearDataset.validate_file_path(multi_path, False)
    with pytest.raises(ValueError, match="Dataset 'time_period' not found in the file"):
        UKSingleYearDataset.validate_file_path(multi_path)
    simulation = Simulation(dataset=Path(multi_path))
    assert simulation.dataset.years == multi.years
    for year in multi.years:
        np.testing.assert_allclose(
            simulation.calculate("employment_income_before_lsr", year),
            multi[year].person.employment_income,
            rtol=1e-6,
        )

    # Keep the existing single-year save/load route covered alongside the fix.
    single_path = str(tmp_path / "single.h5")
    single.save(single_path)
    assert UKSingleYearDataset.validate_file_path(single_path)
    assert not UKMultiYearDataset.validate_file_path(single_path)
    with pytest.raises(ValueError, match="No yearly data found for 'person'"):
        UKMultiYearDataset.validate_file_path(single_path, True)
    single_simulation = Simulation(dataset=single_path)
    np.testing.assert_array_equal(
        single_simulation.calculate("employment_income_before_lsr", 2025),
        single.person.employment_income,
    )


@pytest.mark.usefixtures("cloned_uk_tax_benefit_system")
@settings(max_examples=8, deadline=None)
@example(years={2025})
@given(years=st.sets(st.integers(2020, 2035), min_size=1, max_size=4))
def test_saved_datasets_have_exactly_one_schema_and_load(years):
    """Both layouts, including a multi-year layout with just one year."""
    from policyengine_uk.data import UKMultiYearDataset, UKSingleYearDataset

    singles = []
    for year in sorted(years):
        single = _single_person_dataset()
        single.time_period = str(year)
        single.person["employment_income"] = float(year * 10)
        singles.append(single)

    with TemporaryDirectory() as directory:
        for index, dataset in enumerate(
            [*singles, UKMultiYearDataset(datasets=singles)]
        ):
            path = str(Path(directory) / f"dataset-{index}.h5")
            dataset.save(path)
            single_valid = UKSingleYearDataset.validate_file_path(path, False)
            multi_valid = UKMultiYearDataset.validate_file_path(path, False)
            assert single_valid != multi_valid
            assert multi_valid == isinstance(dataset, UKMultiYearDataset)
            simulation = Simulation(dataset=path)
            expected = (
                dataset.datasets if multi_valid else {int(dataset.time_period): dataset}
            )
            for year, original in expected.items():
                np.testing.assert_array_equal(
                    simulation.calculate("employment_income_before_lsr", year),
                    original.person.employment_income,
                )


def _single_person_dataset():
    """A one-person dataset built from frames, as the multi-year tests do."""
    import pandas as pd

    from policyengine_uk.data.dataset_schema import UKSingleYearDataset

    person = pd.DataFrame(
        {
            "person_id": [1],
            "person_benunit_id": [1],
            "person_household_id": [1],
            "employment_income": [30_000.0],
            "age": [40],
        }
    )
    benunit = pd.DataFrame({"benunit_id": [1]})
    household = pd.DataFrame(
        {
            "household_id": [1],
            "household_weight": [1_000.0],
            "region": ["LONDON"],
            "tenure_type": ["RENT_PRIVATELY"],
            "rent": [12_000.0],
            "council_tax": [1_500.0],
        }
    )
    return UKSingleYearDataset(
        person=person, benunit=benunit, household=household, fiscal_year=2025
    )


def _save_read_only(dataset, path: Path) -> str:
    """Save a dataset and make the file read-only, as a cached download is."""
    dataset.save(str(path))
    path.chmod(0o444)
    return str(path)


def test_single_year_dataset_loads_from_a_read_only_file(tmp_path):
    """Reading a dataset needs no write access.

    huggingface_hub 1.32.0 stores cached downloads as read-only blobs, and
    opening the file in the default append mode refused them, so every
    dataset-backed simulation in CI failed with a PermissionError.
    """
    from policyengine_uk.data.dataset_schema import UKSingleYearDataset

    path = _save_read_only(_single_person_dataset(), tmp_path / "single.h5")

    loaded = UKSingleYearDataset(path)

    assert loaded.time_period == "2025"
    assert float(loaded.person["employment_income"].iloc[0]) == 30_000


def test_multi_year_dataset_loads_from_a_read_only_file(tmp_path):
    from policyengine_uk.data.dataset_schema import UKMultiYearDataset

    dataset = UKMultiYearDataset(datasets=[_single_person_dataset()])
    path = _save_read_only(dataset, tmp_path / "multi.h5")

    loaded = UKMultiYearDataset(path)

    assert loaded.years == [2025]
    assert float(loaded[2025].person["employment_income"].iloc[0]) == 30_000


def test_simulation_builds_from_a_read_only_dataset_file(monkeypatch, tmp_path):
    """The path a cached single-year download takes through Simulation.

    Extending a single year to later years needs a real dataset's columns, so
    that step is stubbed; the file open under test happens before it.
    """
    from policyengine_uk.data.dataset_schema import UKMultiYearDataset

    monkeypatch.setattr(
        simulation_module,
        "extend_single_year_dataset",
        lambda dataset, parameters: UKMultiYearDataset(datasets=[dataset]),
    )
    path = _save_read_only(_single_person_dataset(), tmp_path / "single.h5")

    simulation = Simulation(dataset=path)

    assert float(simulation.calculate("employment_income", 2025)[0]) == 30_000
