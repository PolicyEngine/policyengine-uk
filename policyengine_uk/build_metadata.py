from __future__ import annotations

from functools import lru_cache
import hashlib
from importlib import metadata
import json
import os
from pathlib import Path
import re
import subprocess
import tomllib


PACKAGE_NAME = "policyengine-uk"
PACKAGE_ROOT = Path(__file__).resolve().parent
# Variables that point git at a repository other than the one it discovers
# from its working directory: the list `git rev-parse --local-env-vars`
# prints, less the configuration variables (GIT_CONFIG, GIT_CONFIG_COUNT,
# GIT_CONFIG_PARAMETERS). They are cleared so a caller's environment, such as
# a git hook, cannot substitute another repository's HEAD. Configuration is
# kept because it can carry settings like safe.directory, which a checkout
# owned by another user needs.
GIT_REPOSITORY_ENV_VARS = frozenset(
    {
        "GIT_ALTERNATE_OBJECT_DIRECTORIES",
        "GIT_COMMON_DIR",
        "GIT_DIR",
        "GIT_GRAFT_FILE",
        "GIT_IMPLICIT_WORK_TREE",
        "GIT_INDEX_FILE",
        "GIT_NO_REPLACE_OBJECTS",
        "GIT_OBJECT_DIRECTORY",
        "GIT_PREFIX",
        "GIT_REPLACE_REF_BASE",
        "GIT_SHALLOW_FILE",
        "GIT_WORK_TREE",
    }
)
GIT_SHA_PATTERN = re.compile(r"[0-9a-f]{40}|[0-9a-f]{64}")
# A git call that runs longer than this is treated as having no answer.
GIT_TIMEOUT_SECONDS = 10
# hatch_build.py writes this file to the wheel's .dist-info/extra_metadata/.
BUILD_INFO_NAME = "build_info.json"
DATA_BUILD_SURFACE = (
    "data",
    "parameters",
    "variables",
    "entities.py",
    "microsimulation.py",
    "simulation.py",
    "system.py",
    "tax_benefit_system.py",
    "programs.yaml",
)


def _iter_surface_files() -> list[Path]:
    files: list[Path] = []
    for relative_path in DATA_BUILD_SURFACE:
        path = PACKAGE_ROOT / relative_path
        if path.is_file():
            files.append(path)
            continue
        if path.is_dir():
            files.extend(
                child
                for child in sorted(path.rglob("*"))
                if child.is_file()
                and "__pycache__" not in child.parts
                and child.suffix not in {".pyc", ".pyo"}
            )
    return files


def _get_package_version() -> str:
    return metadata.version(PACKAGE_NAME)


def _get_git_sha(package_root: Path = PACKAGE_ROOT) -> str | None:
    """Return the policyengine-uk commit that ``package_root`` was loaded from.

    The commit comes from the first of these that has one:

    1. ``HEAD`` of policyengine-uk's own git checkout, when the package is
       imported from one (an editable or development install, including a
       git worktree).
    2. The ``vcs_info.commit_id`` that the installer recorded in PEP 610
       ``direct_url.json`` when it installed this copy from git.
    3. The commit that ``hatch_build.py`` recorded in the wheel's
       ``extra_metadata/build_info.json`` when it built the wheel from a
       clean policyengine-uk checkout, as the release workflow does.

    Anything else returns None, including sdist installs. A git
    repository that merely contains the install, such as a
    policyengine-uk-data checkout whose ``.venv`` holds policyengine-uk, is
    never consulted: its HEAD is that repository's commit, not this
    package's. The lookup never raises, because policyengine.py reads this
    metadata while loading the model.
    """
    for get_sha in (
        _get_checkout_git_sha,
        _get_direct_url_git_sha,
        _get_build_info_git_sha,
    ):
        try:
            sha = get_sha(package_root)
        except Exception:
            # A source that fails, for example on an unreadable pyproject,
            # has no answer; the next source may still have one.
            sha = None
        if sha is not None:
            return sha
    return None


def _get_checkout_git_sha(package_root: Path) -> str | None:
    # In a policyengine-uk checkout the package directory sits at the
    # repository root, so the parent is the only directory to check.
    checkout_root = package_root.parent
    if not (checkout_root / ".git").exists():
        return None
    if not _declares_package(checkout_root / "pyproject.toml"):
        return None
    # Git skips an unusable .git directory and keeps searching upwards, and
    # inside a .git directory or a bare repository --show-cdup prints nothing.
    # So require, from one call, a work tree ("true") rooted exactly here (an
    # empty --show-cdup) and then HEAD. No path is decoded from the output.
    output = _run_git(
        checkout_root, "rev-parse", "--is-inside-work-tree", "--show-cdup", "HEAD"
    )
    if output is None:
        return None
    lines = output.split("\n")
    if len(lines) != 3 or lines[0] != "true" or lines[1] != "":
        return None
    return _as_git_sha(lines[2])


def _get_installed_distribution(
    package_root: Path,
) -> metadata.Distribution | None:
    # The installer writes the dist-info directory next to the package it
    # installed; another copy elsewhere on sys.path does not describe this
    # one.
    distributions = list(
        metadata.distributions(name=PACKAGE_NAME, path=[str(package_root.parent)])
    )
    return distributions[0] if len(distributions) == 1 else None


def _get_direct_url_git_sha(package_root: Path) -> str | None:
    distribution = _get_installed_distribution(package_root)
    if distribution is None:
        return None
    direct_url = json.loads(
        _read_dist_info_file(distribution, "direct_url.json") or "{}"
    )
    vcs_info = direct_url.get("vcs_info") if isinstance(direct_url, dict) else None
    if not isinstance(vcs_info, dict) or vcs_info.get("vcs") != "git":
        return None
    return _as_git_sha(vcs_info.get("commit_id"))


def _get_build_info_git_sha(package_root: Path) -> str | None:
    # hatch_build.py records the commit in the dist-info of the wheel it
    # built. The recorded version must be that distribution's.
    distribution = _get_installed_distribution(package_root)
    if distribution is None:
        return None
    build_info = json.loads(
        _read_dist_info_file(distribution, f"extra_metadata/{BUILD_INFO_NAME}") or "{}"
    )
    if not isinstance(build_info, dict):
        return None
    if build_info.get("version") != distribution.version:
        return None
    return _as_git_sha(build_info.get("git_sha"))


def _read_dist_info_file(distribution: metadata.Distribution, name: str) -> str | None:
    # Read only a regular file: a FIFO or device would block the read. A
    # distribution not backed by a dist-info directory has no answer.
    dist_info = getattr(distribution, "_path", None)
    if not isinstance(dist_info, Path) or not (dist_info / name).is_file():
        return None
    return distribution.read_text(name)


def _declares_package(pyproject_path: Path) -> bool:
    # is_file() also rules out a FIFO, which would block the read.
    if not pyproject_path.is_file():
        return False
    with pyproject_path.open("rb") as file:
        project = tomllib.load(file).get("project")
    name = project.get("name") if isinstance(project, dict) else None
    return (
        isinstance(name, str) and re.sub(r"[-_.]+", "-", name).lower() == PACKAGE_NAME
    )


def _run_git(cwd: Path, *args: str) -> str | None:
    env = {
        key: value
        for key, value in os.environ.items()
        if key not in GIT_REPOSITORY_ENV_VARS
    }
    try:
        return subprocess.check_output(
            ["git", "-C", str(cwd), *args],
            stderr=subprocess.DEVNULL,
            text=True,
            env=env,
            timeout=GIT_TIMEOUT_SECONDS,
        ).strip()
    except (OSError, ValueError, subprocess.SubprocessError):
        return None


def _as_git_sha(value: object) -> str | None:
    if isinstance(value, str) and GIT_SHA_PATTERN.fullmatch(value):
        return value
    return None


@lru_cache(maxsize=1)
def get_data_build_fingerprint() -> str:
    digest = hashlib.sha256()
    for file_path in _iter_surface_files():
        relative_path = file_path.relative_to(PACKAGE_ROOT).as_posix()
        digest.update(relative_path.encode("utf-8"))
        digest.update(b"\0")
        digest.update(file_path.read_bytes())
        digest.update(b"\0")
    return f"sha256:{digest.hexdigest()}"


def get_core_runtime_metadata() -> dict[str, object]:
    # Imported here, not at module level: hatch_build.py loads this module
    # while building the wheel, where policyengine-core is not installed.
    from policyengine_core import get_runtime_metadata

    return get_runtime_metadata()


def get_runtime_metadata() -> dict[str, object]:
    return {
        "name": PACKAGE_NAME,
        "version": _get_package_version(),
        "git_sha": _get_git_sha(),
        "data_build_fingerprint": get_data_build_fingerprint(),
        "core": get_core_runtime_metadata(),
    }


def get_data_build_metadata() -> dict[str, object]:
    return get_runtime_metadata()
