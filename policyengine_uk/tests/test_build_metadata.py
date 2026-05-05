import importlib.util
from pathlib import Path
import sys
from unittest.mock import patch

import pytest

BUILD_METADATA_PATH = Path(__file__).resolve().parents[1] / "build_metadata.py"
SPEC = importlib.util.spec_from_file_location(
    "policyengine_uk_build_metadata_under_test",
    BUILD_METADATA_PATH,
)
build_metadata = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = build_metadata
SPEC.loader.exec_module(build_metadata)

get_data_build_fingerprint = build_metadata.get_data_build_fingerprint
get_data_build_metadata = build_metadata.get_data_build_metadata
get_runtime_metadata = build_metadata.get_runtime_metadata


def test_data_build_fingerprint_is_stable_within_process():
    get_data_build_fingerprint.cache_clear()

    first = get_data_build_fingerprint()
    second = get_data_build_fingerprint()

    assert first.startswith("sha256:")
    assert first == second


def test_get_runtime_metadata_includes_required_bundle_fields(monkeypatch):
    get_data_build_fingerprint.cache_clear()

    monkeypatch.setattr(build_metadata, "_get_package_version", lambda: "2.74.0")
    monkeypatch.setattr(build_metadata, "_get_git_sha", lambda: "deadbeef")
    monkeypatch.setattr(
        build_metadata,
        "get_data_build_fingerprint",
        lambda: "sha256:fingerprint",
    )
    monkeypatch.setattr(
        build_metadata,
        "get_core_runtime_metadata",
        lambda: {
            "name": "policyengine-core",
            "version": "3.26.0",
            "git_sha": "coredeadbeef",
        },
    )

    metadata = get_runtime_metadata()

    assert metadata["name"] == "policyengine-uk"
    assert metadata["version"] == "2.74.0"
    assert metadata["git_sha"] == "deadbeef"
    assert metadata["data_build_fingerprint"] == "sha256:fingerprint"
    assert metadata["core"] == {
        "name": "policyengine-core",
        "version": "3.26.0",
        "git_sha": "coredeadbeef",
    }


def test_get_data_build_metadata_uses_runtime_metadata():
    with patch(
        f"{SPEC.name}.get_runtime_metadata",
        return_value={"name": "policyengine-uk"},
    ):
        assert get_data_build_metadata() == {"name": "policyengine-uk"}


def test_runtime_metadata_uses_bundle_contract_when_available():
    policyengine_bundles = pytest.importorskip("policyengine_bundles")

    policyengine_bundles.load_component_metadata(get_runtime_metadata())
