"""The certified dataset pin, the fixtures that record it, and the data mode."""

import hashlib
import os
from pathlib import Path

import pytest
import yaml
from hypothesis import given, settings
from hypothesis import strategies as st

from policyengine_uk.tests.conftest import (
    CERTIFIED_DATASET_PIN,
    DATASET_ENV_VAR,
    DEFAULT_TEST_DATASET_URL,
    REQUIRE_DATA_ENV_VAR,
    TOKEN_ENV_VAR,
    plan_test_data,
)
from policyengine_uk.utils.aggregate_impact.dataset import (
    DatasetMismatchError,
    DatasetPinError,
    load_pin,
    sha256_file,
    verify_file,
)

TESTS = Path(__file__).resolve().parents[1]
PIN = load_pin(CERTIFIED_DATASET_PIN)


def test_pin_is_immutable_and_complete():
    assert PIN.problems() == []
    assert len(PIN.revision) == 40 and len(PIN.sha256) == 64
    assert PIN.uri == f"hf://{PIN.repo_id}/{PIN.path}@{PIN.revision}"
    assert DEFAULT_TEST_DATASET_URL == PIN.uri


def test_reform_fixtures_record_the_pinned_dataset():
    with open(TESTS / "microsimulation" / "reforms_config.yaml") as f:
        fixtures = yaml.safe_load(f)
    recorded = fixtures["dataset"]
    assert recorded["revision"] == PIN.revision
    assert recorded["sha256"] == PIN.sha256
    assert recorded["path"] == PIN.path
    assert str(recorded["data_version"]) == PIN.data_version


def test_every_reform_fixture_keeps_its_receipts():
    with open(TESTS / "microsimulation" / "reforms_config.yaml") as f:
        fixtures = yaml.safe_load(f)
    for reform in fixtures["reforms"]:
        receipts = reform["receipts"]
        assert len(receipts) >= 2, reform["name"]
        latest = receipts[-1]
        assert PIN.data_version in latest["data"], reform["name"]
        assert round(latest["impact"], 1) == reform["expected_impact"], reform["name"]


def _pin_file(tmp_path, **overrides):
    raw = {
        "repo_id": PIN.repo_id,
        "path": PIN.path,
        "revision": PIN.revision,
        "sha256": PIN.sha256,
        **overrides,
    }
    path = tmp_path / "pin.yaml"
    path.write_text(yaml.safe_dump(raw))
    return path


@pytest.mark.parametrize(
    "overrides",
    [
        {"revision": "1.58.0"},
        {"revision": "main"},
        {"sha256": "5BA399EA"},
        {"repo_id": "no-slash"},
        {"path": "/absolute.h5"},
        {"unexpected": "key"},
    ],
)
def test_mutable_or_malformed_pins_are_rejected(tmp_path, overrides):
    with pytest.raises(DatasetPinError):
        load_pin(_pin_file(tmp_path, **overrides))


@settings(max_examples=50, deadline=None)
@given(revision=st.text(max_size=45))
def test_only_a_full_commit_hash_is_accepted_as_a_revision(revision):
    from dataclasses import replace

    pin = replace(PIN, revision=revision)
    is_commit = len(revision) == 40 and all(c in "0123456789abcdef" for c in revision)
    assert (not any("revision" in p for p in pin.problems())) == is_commit


@settings(max_examples=30, deadline=None)
@given(content=st.binary(max_size=4096), tamper=st.integers(0, 4095))
def test_verification_accepts_the_pinned_bytes_and_rejects_any_other(
    tmp_path_factory, content, tamper
):
    path = tmp_path_factory.mktemp("data") / "file.h5"
    path.write_bytes(content)
    digest = hashlib.sha256(content).hexdigest()
    assert sha256_file(path) == digest
    assert verify_file(path, digest) == digest
    if content:
        changed = bytearray(content)
        changed[tamper % len(content)] ^= 0xFF
        path.write_bytes(bytes(changed))
        with pytest.raises(DatasetMismatchError):
            verify_file(path, digest)


ENV_VALUES = st.one_of(
    st.none(), st.sampled_from(["", "0", "1", "true", "FALSE", "yes", "maybe"])
)
DATASETS = st.one_of(
    st.none(), st.just(""), st.just(PIN.uri), st.just("hf://other/repo/file.h5@abc")
)
TOKENS = st.one_of(st.none(), st.just(""), st.just("hf_token"))


def _env(flag, dataset, token, extra):
    env = dict(extra)
    for key, value in (
        (REQUIRE_DATA_ENV_VAR, flag),
        (DATASET_ENV_VAR, dataset),
        (TOKEN_ENV_VAR, token),
    ):
        if value is not None:
            env[key] = value
    return env


@settings(max_examples=300, deadline=None)
@given(
    flag=ENV_VALUES,
    dataset=DATASETS,
    token=TOKENS,
    extra=st.dictionaries(st.sampled_from(["HOME", "CI", "PATH"]), st.text(max_size=5)),
)
def test_data_plan_invariants(flag, dataset, token, extra):
    plan = plan_test_data(_env(flag, dataset, token, extra), PIN.uri)
    assert plan.action in ("run", "skip", "fail")
    # Mandatory mode never skips, and runs only on the pinned dataset.
    if plan.mandatory:
        assert plan.action != "skip"
        if plan.action == "run":
            assert plan.pinned and plan.dataset == PIN.uri
    # Running always names a dataset; an explicit one always wins.
    if plan.action == "run":
        assert plan.dataset
        if dataset:
            assert plan.dataset == dataset
    # Nothing configured and not mandatory: the old behaviour, a skip.
    if (
        not dataset
        and not token
        and str(flag or "").strip().lower() in ("", "0", "false", "no")
    ):
        assert plan.action == "skip"
    # An unrecognised mode value fails closed.
    if flag is not None and flag.strip().lower() not in (
        "",
        "0",
        "1",
        "true",
        "false",
        "yes",
        "no",
        "on",
        "off",
    ):
        assert plan.action == "fail"
    # Unrelated variables never change the plan.
    assert plan == plan_test_data(_env(flag, dataset, token, {}), PIN.uri)


def test_data_plan_examples():
    assert plan_test_data({TOKEN_ENV_VAR: "t"}, PIN.uri).action == "run"
    assert plan_test_data({}, PIN.uri).action == "skip"
    assert plan_test_data({REQUIRE_DATA_ENV_VAR: "1"}, PIN.uri).action == "fail"
    assert plan_test_data(
        {REQUIRE_DATA_ENV_VAR: "1", TOKEN_ENV_VAR: "t"}, PIN.uri
    ).pinned
    other = {REQUIRE_DATA_ENV_VAR: "1", DATASET_ENV_VAR: "local.h5"}
    assert plan_test_data(other, PIN.uri).action == "fail"
    assert plan_test_data({DATASET_ENV_VAR: "local.h5"}, PIN.uri).action == "run"
