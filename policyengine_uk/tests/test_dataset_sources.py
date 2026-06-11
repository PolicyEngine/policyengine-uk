from pathlib import Path

import pytest

from policyengine_uk.data import dataset_sources
from policyengine_uk.data.dataset_sources import materialize_gcs_dataset_url


class FakeBlob:
    def __init__(self, name, generation, metadata=None, contents=b"dataset"):
        self.name = name
        self.generation = str(generation)
        self.metadata = metadata
        self.contents = contents
        self.download_count = 0
        self.reload_count = 0

    def reload(self):
        self.reload_count += 1

    def download_to_filename(self, filename):
        self.download_count += 1
        Path(filename).write_bytes(self.contents)


class FakeBucket:
    def __init__(self, blobs, current_generations):
        self.blobs = blobs
        self.current_generations = current_generations

    def blob(self, file_path, generation=None):
        if generation is None:
            generation = self.current_generations[file_path]
        return self.blobs[(file_path, str(generation))]


class FakeStorageClient:
    def __init__(self, blobs, current_generations):
        self.blobs = blobs
        self.current_generations = current_generations
        self.list_calls = []

    def bucket(self, bucket_name):
        return FakeBucket(
            self.blobs[bucket_name], self.current_generations[bucket_name]
        )

    def list_blobs(self, bucket_name, prefix, versions):
        self.list_calls.append((bucket_name, prefix, versions))
        return [
            blob
            for (name, _generation), blob in self.blobs[bucket_name].items()
            if name.startswith(prefix)
        ]


def fake_client(*blobs, current_generation):
    file_path = blobs[0].name
    return FakeStorageClient(
        blobs={"bucket": {(blob.name, blob.generation): blob for blob in blobs}},
        current_generations={"bucket": {file_path: str(current_generation)}},
    )


def test_materialize_gcs_dataset_url_uses_numeric_generation(monkeypatch, tmp_path):
    old_blob = FakeBlob(
        "data/file.h5",
        123,
        metadata={"version": "1.55.10"},
        contents=b"old",
    )
    current_blob = FakeBlob(
        "data/file.h5",
        456,
        metadata={"version": "1.56.0"},
        contents=b"current",
    )
    client = fake_client(old_blob, current_blob, current_generation=456)
    monkeypatch.setattr(dataset_sources, "_get_storage_client", lambda: client)

    path = materialize_gcs_dataset_url(
        "gs://bucket/data/file.h5@123",
        cache_dir=tmp_path,
    )

    assert Path(path).read_bytes() == b"old"
    assert old_blob.download_count == 1
    assert client.list_calls == []


def test_materialize_gcs_dataset_url_uses_latest_matching_metadata_version(
    monkeypatch,
    tmp_path,
):
    old_matching_blob = FakeBlob(
        "data/file.h5",
        111,
        metadata={"version": "1.55.10"},
        contents=b"old match",
    )
    new_matching_blob = FakeBlob(
        "data/file.h5",
        333,
        metadata={"version": "1.55.10"},
        contents=b"new match",
    )
    current_blob = FakeBlob(
        "data/file.h5",
        444,
        metadata={"version": "1.56.0"},
        contents=b"current",
    )
    client = fake_client(
        old_matching_blob,
        new_matching_blob,
        current_blob,
        current_generation=444,
    )
    monkeypatch.setattr(dataset_sources, "_get_storage_client", lambda: client)

    path = materialize_gcs_dataset_url(
        "gs://bucket/data/file.h5@1.55.10",
        cache_dir=tmp_path,
    )

    assert Path(path).read_bytes() == b"new match"
    assert new_matching_blob.download_count == 1
    assert client.list_calls == [("bucket", "data/file.h5", True)]


def test_materialize_gcs_dataset_url_uses_current_blob_when_metadata_matches(
    monkeypatch,
    tmp_path,
):
    current_blob = FakeBlob(
        "data/file.h5",
        444,
        metadata={"version": "1.55.10"},
        contents=b"current",
    )
    client = fake_client(current_blob, current_generation=444)
    monkeypatch.setattr(dataset_sources, "_get_storage_client", lambda: client)

    path = materialize_gcs_dataset_url(
        "gs://bucket/data/file.h5@1.55.10",
        cache_dir=tmp_path,
    )

    assert Path(path).read_bytes() == b"current"
    assert current_blob.download_count == 1
    assert client.list_calls == []


def test_materialize_gcs_dataset_url_errors_for_missing_metadata_version(
    monkeypatch,
    tmp_path,
):
    current_blob = FakeBlob(
        "data/file.h5",
        444,
        metadata={"version": "1.56.0"},
    )
    client = fake_client(current_blob, current_generation=444)
    monkeypatch.setattr(dataset_sources, "_get_storage_client", lambda: client)

    with pytest.raises(ValueError, match="metadata version '1.55.10'"):
        materialize_gcs_dataset_url(
            "gs://bucket/data/file.h5@1.55.10",
            cache_dir=tmp_path,
        )


def test_materialize_gcs_dataset_url_reuses_cached_file(monkeypatch, tmp_path):
    current_blob = FakeBlob(
        "data/file.h5",
        444,
        metadata={"version": "1.55.10"},
        contents=b"current",
    )
    client = fake_client(current_blob, current_generation=444)
    monkeypatch.setattr(dataset_sources, "_get_storage_client", lambda: client)

    dataset_url = "gs://bucket/data/file.h5@1.55.10"
    first_path = materialize_gcs_dataset_url(dataset_url, cache_dir=tmp_path)
    second_path = materialize_gcs_dataset_url(dataset_url, cache_dir=tmp_path)

    assert first_path == second_path
    assert Path(second_path).read_bytes() == b"current"
    assert current_blob.download_count == 1
