"""Pinned dataset selection: load a pin, fetch its file, verify its bytes."""

from __future__ import annotations

import hashlib
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping, Optional, Union

import yaml

_HEX40 = re.compile(r"^[0-9a-f]{40}$")
_HEX64 = re.compile(r"^[0-9a-f]{64}$")
_REPO_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*/[A-Za-z0-9][A-Za-z0-9._-]*$")


class DatasetPinError(ValueError):
    """The pin file is malformed or names a mutable revision."""


class DatasetMismatchError(RuntimeError):
    """A dataset file's bytes do not match the pinned SHA-256."""


@dataclass(frozen=True)
class DatasetPin:
    """An immutable reference to one dataset file on the Hugging Face Hub."""

    repo_id: str
    path: str
    revision: str
    sha256: str
    data_package: str = ""
    data_version: str = ""
    hf_tag: Optional[str] = None
    size_bytes: Optional[int] = None
    certification: Mapping[str, str] = field(default_factory=dict)

    @property
    def uri(self) -> str:
        """The ``hf://`` reference ``policyengine_uk.Simulation`` accepts."""
        return f"hf://{self.repo_id}/{self.path}@{self.revision}"

    def problems(self) -> list[str]:
        """Every reason this pin is not an immutable, verifiable reference."""
        problems = []
        if not _REPO_ID.match(self.repo_id or ""):
            problems.append(f"repo_id {self.repo_id!r} is not 'owner/name'")
        if not self.path or "@" in self.path or self.path.startswith("/"):
            problems.append(f"path {self.path!r} is not a relative file path")
        if not _HEX40.match(self.revision or ""):
            problems.append(
                f"revision {self.revision!r} is not a 40-character commit hash; "
                "tags and branches can move"
            )
        if not _HEX64.match(self.sha256 or ""):
            problems.append(f"sha256 {self.sha256!r} is not a lowercase hex digest")
        if self.size_bytes is not None and self.size_bytes <= 0:
            problems.append(f"size_bytes {self.size_bytes!r} is not positive")
        return problems

    def describe(self) -> str:
        version = f"{self.data_package} {self.data_version}".strip()
        return (
            f"{self.path} ({version}, commit {self.revision[:8]}, "
            f"sha256 {self.sha256[:12]})"
        )

    def as_dict(self) -> dict:
        return {
            "uri": self.uri,
            "repo_id": self.repo_id,
            "path": self.path,
            "revision": self.revision,
            "sha256": self.sha256,
            "data_package": self.data_package,
            "data_version": self.data_version,
            "hf_tag": self.hf_tag,
            "size_bytes": self.size_bytes,
            "certification": dict(self.certification),
        }


def load_pin(path: Union[str, os.PathLike]) -> DatasetPin:
    """Read a pin file and reject it unless it is immutable and complete."""
    with open(path) as f:
        raw = yaml.safe_load(f) or {}
    known = {
        "repo_id",
        "path",
        "revision",
        "sha256",
        "data_package",
        "data_version",
        "hf_tag",
        "size_bytes",
        "certification",
    }
    unknown = sorted(set(raw) - known)
    if unknown:
        raise DatasetPinError(f"{path}: unknown keys {unknown}")
    pin = DatasetPin(
        repo_id=str(raw.get("repo_id", "")),
        path=str(raw.get("path", "")),
        revision=str(raw.get("revision", "")),
        sha256=str(raw.get("sha256", "")),
        data_package=str(raw.get("data_package", "")),
        data_version=str(raw.get("data_version", "")),
        hf_tag=None if raw.get("hf_tag") is None else str(raw["hf_tag"]),
        size_bytes=None if raw.get("size_bytes") is None else int(raw["size_bytes"]),
        certification={
            str(k): str(v) for k, v in (raw.get("certification") or {}).items()
        },
    )
    problems = pin.problems()
    if problems:
        raise DatasetPinError(f"{path}: " + "; ".join(problems))
    return pin


def sha256_file(path: Union[str, os.PathLike], chunk_size: int = 1 << 20) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_file(path: Union[str, os.PathLike], expected_sha256: str) -> str:
    """Return the file's SHA-256, raising if it differs from the expected one."""
    actual = sha256_file(path)
    if actual != expected_sha256:
        raise DatasetMismatchError(
            f"{path} has sha256 {actual}, but the pin requires {expected_sha256}"
        )
    return actual


def materialise(
    pin: DatasetPin,
    token: Optional[str] = None,
    cache_dir: Optional[Union[str, os.PathLike]] = None,
) -> Path:
    """Download the pinned file (or reuse the cached copy) and verify it.

    The token defaults to ``HUGGING_FACE_TOKEN``. The Hugging Face cache is
    keyed by commit, so a verified file is never downloaded twice.
    """
    from huggingface_hub import hf_hub_download

    if token is None:
        token = os.environ.get("HUGGING_FACE_TOKEN") or None
    local = hf_hub_download(
        repo_id=pin.repo_id,
        filename=pin.path,
        revision=pin.revision,
        repo_type="model",
        token=token,
        cache_dir=cache_dir,
    )
    verify_file(local, pin.sha256)
    return Path(local)
