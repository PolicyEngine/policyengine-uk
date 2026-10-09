"""Tests for hatch_build.py, which records a wheel's build commit.

The hook may record a commit only when the wheel it builds is exactly what a
clean checkout of that commit builds. These tests build real wheels and
sdists with hatchling from small policyengine-uk projects in temporary git
repositories. Each project uses this repository's pyproject.toml,
.gitignore, hatch_build.py and build_metadata.py.
"""

import contextlib
import importlib.util
import json
import os
from pathlib import Path
import py_compile
import re
import shutil
import stat
import subprocess
import sys
import tarfile
import threading
import venv
import zipfile

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
import pytest

pytest.importorskip("hatchling")
from hatchling.builders.sdist import SdistBuilder
from hatchling.builders.wheel import WheelBuilder

REPO_ROOT = Path(__file__).resolve().parents[2]
HATCH_BUILD_PATH = REPO_ROOT / "hatch_build.py"
BUILD_METADATA_PATH = REPO_ROOT / "policyengine_uk" / "build_metadata.py"
if not HATCH_BUILD_PATH.is_file():
    pytest.skip("hatch_build.py is only in a source checkout", allow_module_level=True)


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


hatch_build = _load("policyengine_uk_hatch_build_under_test", HATCH_BUILD_PATH)
build_metadata = _load(
    "policyengine_uk_build_metadata_for_hook_test", BUILD_METADATA_PATH
)

SHA = "0123456789abcdef0123456789abcdef01234567"
OTHER_SHA = "89abcdef0123456789abcdef0123456789abcdef"
BUILD_INFO = "extra_metadata/build_info.json"
# hermetic_git only sets environment variables, so examples may share it.
SUPPRESSED_HEALTH_CHECKS = [HealthCheck.too_slow, HealthCheck.function_scoped_fixture]


@pytest.fixture(autouse=True)
def hermetic_git(monkeypatch):
    # Neither the tests' git calls nor the hook's may be shaped by the
    # user's git configuration or redirected by the caller's environment.
    for key in build_metadata.GIT_REPOSITORY_ENV_VARS:
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", os.devnull)
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")


def _git(cwd: Path, *args: str) -> str:
    return subprocess.check_output(
        ["git", "-C", str(cwd), *args], stderr=subprocess.DEVNULL, text=True
    ).strip()


def _commit(repo: Path, message: str) -> str:
    _git(repo, "add", "-A")
    _git(
        repo,
        "-c",
        "user.name=Test",
        "-c",
        "user.email=test@example.com",
        "commit",
        "-q",
        "--allow-empty",
        "-m",
        message,
    )
    return _git(repo, "rev-parse", "HEAD")


def _make_project(root: Path) -> str:
    """Create a committed policyengine-uk project at ``root``; return HEAD."""
    package = root / "policyengine_uk"
    (package / "parameters").mkdir(parents=True)
    for name in ("pyproject.toml", ".gitignore", "hatch_build.py"):
        shutil.copyfile(REPO_ROOT / name, root / name)
    shutil.copyfile(BUILD_METADATA_PATH, package / "build_metadata.py")
    (package / "__init__.py").write_text("")
    (package / "parameters" / "rate.yaml").write_text("values:\n  2025-01-01: 0.2\n")
    for name in ("README.md", "LICENSE", "CHANGELOG.md"):
        (root / name).write_text(f"{name}\n")
    _git(root, "init", "-q")
    return _commit(root, str(root))


def _project_version(root: Path) -> str:
    return WheelBuilder(str(root)).metadata.version


def _wheel_input_paths(root: Path) -> list[str]:
    paths, reason = hatch_build.wheel_input_paths(WheelBuilder(str(root)))
    assert paths is not None, reason
    return paths


def _find_build_commit(root: Path) -> tuple[str | None, str]:
    return hatch_build.build_commit(WheelBuilder(str(root)))


def _build_wheel(root: Path, out: Path, version: str = "standard") -> Path:
    [artifact] = WheelBuilder(str(root)).build(directory=str(out), versions=[version])
    return Path(artifact)


def _build_sdist(root: Path, out: Path) -> Path:
    [artifact] = SdistBuilder(str(root)).build(
        directory=str(out), versions=["standard"]
    )
    return Path(artifact)


def _wheel_build_info(wheel: Path) -> dict | None:
    with zipfile.ZipFile(wheel) as archive:
        names = [name for name in archive.namelist() if name.endswith(BUILD_INFO)]
        if not names:
            return None
        [name] = names
        return json.loads(archive.read(name))


@pytest.fixture
def project(tmp_path) -> tuple[Path, str]:
    root = tmp_path / "policyengine-uk"
    return root, _make_project(root)


# find_build_commit: the commit is recorded only for a clean checkout of
# policyengine-uk whose packaged files are all tracked.


def test_records_head_of_clean_checkout(project):
    root, head = project

    assert _find_build_commit(root) == (head, "")


def test_records_head_beside_files_both_tools_ignore(project):
    # A development tree or CI runner has bytecode, a virtualenv, build
    # output and data files that both git and hatchling ignore.
    root, head = project
    package = root / "policyengine_uk"
    (package / "__pycache__").mkdir()
    (package / "__pycache__" / "build_metadata.cpython-313.pyc").write_bytes(b"pyc")
    (package / "frs_2023.h5").write_bytes(b"data")
    (root / ".venv" / "bin").mkdir(parents=True)
    (root / ".venv" / "bin" / "python").write_text("")
    (root / "dist").mkdir()
    (root / "dist" / "old.whl").write_bytes(b"")

    assert _find_build_commit(root) == (head, "")


def _modify_tracked(root: Path) -> None:
    (root / "policyengine_uk" / "parameters" / "rate.yaml").write_text("changed\n")


def _stage_change(root: Path) -> None:
    _modify_tracked(root)
    _git(root, "add", "-A")


def _staged_then_reverted(root: Path) -> None:
    rate = root / "policyengine_uk" / "parameters" / "rate.yaml"
    original = rate.read_bytes()
    _stage_change(root)
    rate.write_bytes(original)


def _delete_tracked(root: Path) -> None:
    (root / "policyengine_uk" / "parameters" / "rate.yaml").unlink()


def _untracked_in_package(root: Path) -> None:
    (root / "policyengine_uk" / "scratch.py").write_text("x = 1\n")


def _untracked_outside_package(root: Path) -> None:
    (root / "notes.txt").write_text("notes\n")


def _modify_pyproject(root: Path) -> None:
    with (root / "pyproject.toml").open("a") as file:
        file.write("\n# local change\n")


def _ignored_by_info_exclude(root: Path) -> None:
    with (root / ".git" / "info" / "exclude").open("a") as file:
        file.write("*.local\n")
    (root / "policyengine_uk" / "settings.local").write_text("secret\n")


def _ignored_by_excludes_file(root: Path) -> None:
    excludes = root.parent / "global-excludes"
    excludes.write_text("*.local\n")
    _git(root, "config", "core.excludesFile", str(excludes))
    (root / "policyengine_uk" / "settings.local").write_text("secret\n")


def _ignored_by_committed_nested_gitignore(root: Path) -> None:
    (root / "policyengine_uk" / ".gitignore").write_text("*.local\n")
    _commit(root, "nested gitignore")
    (root / "policyengine_uk" / "settings.local").write_text("secret\n")


def _assume_unchanged_then_modified(root: Path) -> None:
    _git(root, "update-index", "--assume-unchanged", "policyengine_uk/__init__.py")
    (root / "policyengine_uk" / "__init__.py").write_text("x = 1\n")


def _skip_worktree_then_deleted(root: Path) -> None:
    # What a sparse checkout that leaves out a package file looks like.
    _git(root, "update-index", "--skip-worktree", "policyengine_uk/__init__.py")
    (root / "policyengine_uk" / "__init__.py").unlink()


def _ignored_license_backup(root: Path) -> None:
    # hatchling packages every root file matching its default license globs
    # (LICEN[CS]E* and others), whether or not git ignores it; .gitignore
    # ignores editor backups (*~).
    (root / "LICENSE~").write_text("old licence\n")


def _crlf_hidden_by_autocrlf(root: Path) -> None:
    _git(root, "config", "core.autocrlf", "true")
    rate = root / "policyengine_uk" / "parameters" / "rate.yaml"
    rate.write_bytes(rate.read_bytes().replace(b"\n", b"\r\n"))
    # As a Windows checkout has it: the index is current, so status is clean.
    _git(root, "add", "policyengine_uk/parameters/rate.yaml")


def _exec_bit_hidden_by_file_mode(root: Path) -> None:
    _git(root, "config", "core.fileMode", "false")
    rate = root / "policyengine_uk" / "parameters" / "rate.yaml"
    rate.chmod(rate.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def _content_hidden_by_clean_filter(root: Path) -> None:
    with (root / ".git" / "info" / "attributes").open("a") as file:
        file.write("*.yaml filter=hide\n")
    _git(root, "config", "filter.hide.clean", "sed -e '/^# local/d'")
    rate = root / "policyengine_uk" / "parameters" / "rate.yaml"
    rate.write_text(rate.read_text() + "# local change\n")
    # The cleaned content equals HEAD's, so once staged, status is clean.
    _git(root, "add", "policyengine_uk/parameters/rate.yaml")


def _ignore_rule_hidden_by_clean_filter(root: Path) -> None:
    # hatchling reads the raw .gitignore to choose files; status sees the
    # cleaned one, which equals HEAD's.
    with (root / ".git" / "info" / "attributes").open("a") as file:
        file.write(".gitignore filter=hiderule\n")
    _git(root, "config", "filter.hiderule.clean", "sed -e '/rate.yaml/d'")
    with (root / ".gitignore").open("a") as file:
        file.write("policyengine_uk/parameters/rate.yaml\n")
    _git(root, "add", ".gitignore")


def _exclusion_in_ignored_hatch_toml(root: Path) -> None:
    # hatchling merges hatch.toml into the build configuration.
    with (root / ".git" / "info" / "exclude").open("a") as file:
        file.write("hatch.toml\n")
    # Its [build] table replaces pyproject's [tool.hatch.build], so restate
    # the package and the hook, which would otherwise not run at all.
    (root / "hatch.toml").write_text(
        "[build.targets.wheel]\n"
        'packages = ["policyengine_uk"]\n'
        'exclude = ["policyengine_uk/parameters/rate.yaml"]\n'
        "[build.targets.wheel.hooks.custom]\n"
        'path = "hatch_build.py"\n'
    )


def _head_replaced_by_another_commit(root: Path) -> None:
    # git replace S T: HEAD still names S, but status and the index use T.
    original = _git(root, "rev-parse", "HEAD")
    rate = root / "policyengine_uk" / "parameters" / "rate.yaml"
    rate.write_text(rate.read_text() + "  2027-01-01: 0.99\n")
    replacement = _commit(root, "replacement")
    _git(root, "reset", "-q", "--hard", original)
    _git(root, "replace", "-f", original, replacement)
    _git(root, "reset", "-q", "--hard", original)


def _ignored_pkg_info(root: Path) -> None:
    # hatchling fills dynamic metadata fields from a root PKG-INFO.
    with (root / ".git" / "info" / "exclude").open("a") as file:
        file.write("PKG-INFO\n")
    (root / "PKG-INFO").write_text(
        "Metadata-Version: 2.1\nName: policyengine-uk\n"
        f"Version: {_project_version(root)}\n"
    )


def _deletion_hidden_by_stale_fsmonitor(root: Path) -> None:
    # A file-system monitor that reports nothing leaves a deleted file's
    # entry fsmonitor-valid, so status trusts it; ls-files -v still says H.
    monitor = root.parent / "fsmonitor"
    monitor.write_text("#!/bin/sh\nprintf 'token\\000'\n")
    monitor.chmod(0o755)
    _git(root, "config", "core.fsmonitor", str(monitor))
    _git(root, "config", "core.fsmonitorHookVersion", "2")
    _git(root, "update-index", "--fsmonitor")
    _git(root, "status", "--porcelain")
    _git(root, "update-index", "--fsmonitor-valid", "policyengine_uk/__init__.py")
    (root / "policyengine_uk" / "__init__.py").unlink()


def _change_under_carriage_return_name(root: Path) -> None:
    # git hash-object --stdin-paths strips a trailing carriage return, so a
    # check that passed paths on stdin hashed "rate.yaml" for "rate.yaml\r".
    rate = root / "policyengine_uk" / "parameters" / "rate.yaml"
    twin = rate.with_name("rate.yaml\r")
    twin.write_bytes(rate.read_bytes())
    _commit(root, "carriage return name")
    with (root / ".git" / "info" / "attributes").open("a") as file:
        file.write("*rate.yaml? filter=hidecr\n")
    _git(root, "config", "filter.hidecr.clean", f"cat '{rate}'")
    twin.write_text("values:\n  2025-01-01: 0.9\n")
    _git(root, "add", "-A")


def _ignored_symlink_alias(root: Path) -> None:
    # .gitignore ignores "build". hatchling's walk follows the link first,
    # excludes its files by that rule, then skips the real directory as
    # already seen, so rate.yaml drops out without any change git reports.
    (root / "policyengine_uk" / "build").symlink_to("parameters")


DIRTY_TREES = {
    "modified tracked file": _modify_tracked,
    "staged change": _stage_change,
    "staged change reverted in the working tree": _staged_then_reverted,
    "deleted tracked file": _delete_tracked,
    "untracked file in the package": _untracked_in_package,
    "untracked file outside the package": _untracked_outside_package,
    "modified pyproject": _modify_pyproject,
    "package file ignored by .git/info/exclude": _ignored_by_info_exclude,
    "package file ignored by core.excludesFile": _ignored_by_excludes_file,
    "package file ignored by a nested .gitignore": (
        _ignored_by_committed_nested_gitignore
    ),
    "assume-unchanged file modified": _assume_unchanged_then_modified,
    "skip-worktree file deleted": _skip_worktree_then_deleted,
    "ignored licence backup": _ignored_license_backup,
    "CRLF hidden by core.autocrlf": _crlf_hidden_by_autocrlf,
    "exec bit hidden by core.fileMode": _exec_bit_hidden_by_file_mode,
    "content hidden by a clean filter": _content_hidden_by_clean_filter,
    "ignore rule hidden by a clean filter": _ignore_rule_hidden_by_clean_filter,
    "exclusion in an ignored hatch.toml": _exclusion_in_ignored_hatch_toml,
    "HEAD replaced by another commit": _head_replaced_by_another_commit,
    "ignored PKG-INFO": _ignored_pkg_info,
    "deletion hidden by a stale fsmonitor": _deletion_hidden_by_stale_fsmonitor,
    "change under a carriage-return name": _change_under_carriage_return_name,
    "ignored symlink alias of a tracked directory": _ignored_symlink_alias,
}


@pytest.mark.parametrize("make_dirty", DIRTY_TREES.values(), ids=DIRTY_TREES.keys())
def test_records_nothing_for_dirty_tree(project, make_dirty):
    root, _ = project
    make_dirty(root)

    git_sha, reason = _find_build_commit(root)

    assert git_sha is None
    assert reason


@pytest.mark.skipif(os.name == "nt", reason="needs POSIX file modes")
def test_records_nothing_after_mode_change(project):
    # The wheel records the executable bit, so a mode change alters it.
    root, _ = project
    rate = root / "policyengine_uk" / "parameters" / "rate.yaml"
    rate.chmod(rate.stat().st_mode | stat.S_IXUSR)

    assert _find_build_commit(root)[0] is None


@pytest.mark.skipif(os.name == "nt", reason="needs symlinks")
def test_records_nothing_for_committed_symlink(project):
    # The wheel would contain the target's bytes, which are outside the
    # commit and can change without changing it.
    root, _ = project
    outside = root.parent / "outside.yaml"
    outside.write_text("values: {}\n")
    (root / "policyengine_uk" / "linked.yaml").symlink_to(outside)
    _commit(root, "add symlink")

    git_sha, reason = _find_build_commit(root)

    assert git_sha is None
    assert "not a regular tracked file" in reason


def _add_force_include(root: Path, source: str, target: str, exclude: str) -> None:
    pyproject = root / "pyproject.toml"
    pyproject.write_text(
        pyproject.read_text()
        + f"""
[tool.hatch.build.targets.wheel.force-include]
"{source}" = "{target}"
"""
    )
    if exclude:
        text = pyproject.read_text()
        text = text.replace(
            'packages = ["policyengine_uk"]',
            f'packages = ["policyengine_uk"]\nexclude = ["{exclude}"]',
            1,
        )
        pyproject.write_text(text)


def test_records_nothing_for_force_include_from_an_ignored_directory(project):
    # hatchling packages policyengine_uk/parameters from build/parameters,
    # which .gitignore ignores; the tracked destination is not what ships.
    root, _ = project
    _add_force_include(
        root,
        "build/parameters",
        "policyengine_uk/parameters",
        "policyengine_uk/parameters/**",
    )
    _commit(root, "force-include")
    (root / "build" / "parameters").mkdir(parents=True)
    (root / "build" / "parameters" / "rate.yaml").write_text("values: {}\n")
    assert _git(root, "status", "--porcelain") == ""

    git_sha, reason = _find_build_commit(root)

    assert git_sha is None
    assert "build/parameters/rate.yaml" in reason


def test_records_nothing_for_force_include_from_outside_the_checkout(project):
    root, _ = project
    outside = root.parent / "outside.txt"
    outside.write_text("outside\n")
    _add_force_include(root, str(outside), "policyengine_uk/outside.txt", "")
    _commit(root, "force-include")

    git_sha, reason = _find_build_commit(root)

    assert git_sha is None
    assert "outside the checkout" in reason


def test_records_head_for_force_include_of_a_tracked_file(project):
    # Force inclusion itself is fine when its source is committed.
    root, _ = project
    (root / "extras").mkdir()
    (root / "extras" / "notes.txt").write_text("notes\n")
    _add_force_include(root, "extras/notes.txt", "policyengine_uk/notes.txt", "")
    head = _commit(root, "force-include")

    assert _find_build_commit(root) == (head, "")


def test_records_nothing_for_ignored_legacy_license_file(project):
    # A ``license = {file = ...}`` table copies the file's text into METADATA.
    # The name avoids the default licence globs, which are checked anyway.
    root, _ = project
    pyproject = root / "pyproject.toml"
    pyproject.write_text(
        pyproject.read_text().replace(
            'license = "AGPL-3.0"', 'license = {file = "legal/terms.txt"}', 1
        )
    )
    _commit(root, "legacy licence table")
    with (root / ".git" / "info" / "exclude").open("a") as file:
        file.write("legal/terms.txt\n")
    (root / "legal").mkdir()
    (root / "legal" / "terms.txt").write_text("licence text\n")
    assert _git(root, "status", "--porcelain") == ""

    git_sha, reason = _find_build_commit(root)

    assert git_sha is None
    assert "legal/terms.txt" in reason


def test_records_nothing_without_git_directory(project):
    # An unpacked sdist.
    root, _ = project
    shutil.rmtree(root / ".git")

    assert _find_build_commit(root)[0] is None


def test_records_nothing_for_another_project(project):
    root, _ = project
    pyproject = root / "pyproject.toml"
    pyproject.write_text(
        pyproject.read_text().replace(
            'name = "policyengine-uk"', 'name = "policyengine-uk-fork"', 1
        )
    )
    _commit(root, "rename")

    assert _find_build_commit(root)[0] is None


def test_records_nothing_for_project_inside_another_repository(tmp_path):
    # For example an sdist unpacked and committed inside a uk-data checkout.
    outer = tmp_path / "policyengine-uk-data"
    root = outer / "vendor" / "policyengine-uk"
    _make_project(root)
    shutil.rmtree(root / ".git")
    _git(outer, "init", "-q")
    _commit(outer, "vendor")

    assert _find_build_commit(root)[0] is None
    # Git skips an empty .git directory and finds the outer repository.
    (root / ".git").mkdir()
    assert _find_build_commit(root)[0] is None


def test_records_nothing_for_unreadable_pyproject(project):
    root, _ = project
    (root / "pyproject.toml").write_text("[project\n")
    _commit(root, "break pyproject")

    git_sha, reason = hatch_build.find_build_commit(
        root, ["policyengine_uk/__init__.py"], build_metadata
    )

    assert git_sha is None
    assert "lookup failed" in reason


def test_ignores_git_environment_overrides(project, tmp_path, monkeypatch):
    root, head = project
    outer = tmp_path / "outer"
    outer.mkdir()
    _git(outer, "init", "-q")
    _commit(outer, "outer")
    # Each would make the checkout look dirty or point git elsewhere.
    monkeypatch.setenv("GIT_DIR", str(outer / ".git"))
    monkeypatch.setenv("GIT_WORK_TREE", str(outer))
    monkeypatch.setenv("GIT_INDEX_FILE", str(tmp_path / "empty-index"))

    assert _find_build_commit(root) == (head, "")


@pytest.mark.parametrize(
    ("key", "value", "change"),
    [
        ("core.autocrlf", "true", "crlf"),
        ("core.fileMode", "false", "exec bit"),
    ],
)
def test_environment_git_config_cannot_hide_changes(
    project, monkeypatch, key, value, change
):
    # The hook keeps git's configuration variables (GIT_CONFIG_COUNT and
    # friends) so an environment-supplied safe.directory works. Config from
    # there must not make a changed file pass as HEAD's either.
    root, _ = project
    monkeypatch.setenv("GIT_CONFIG_COUNT", "1")
    monkeypatch.setenv("GIT_CONFIG_KEY_0", key)
    monkeypatch.setenv("GIT_CONFIG_VALUE_0", value)
    rate = root / "policyengine_uk" / "parameters" / "rate.yaml"
    if change == "crlf":
        rate.write_bytes(rate.read_bytes().replace(b"\n", b"\r\n"))
        _git(root, "add", "policyengine_uk/parameters/rate.yaml")
    else:
        rate.chmod(rate.stat().st_mode | stat.S_IXUSR)
    assert _git(root, "status", "--porcelain") == ""

    git_sha, reason = _find_build_commit(root)

    assert git_sha is None
    assert "differs from HEAD" in reason


def test_tracked_files_must_exist_whatever_git_status_says(project, monkeypatch):
    # Defence in depth beside disabling git's caches: a tracked file that is
    # missing on disk is found by lstat even if status reports nothing.
    root, _ = project
    (root / "policyengine_uk" / "__init__.py").unlink()
    real_git_output = hatch_build._git_output

    def blind_status(build_metadata, root, *args):
        if "status" in args:
            return b""
        return real_git_output(build_metadata, root, *args)

    monkeypatch.setattr(hatch_build, "_git_output", blind_status)

    git_sha, reason = _find_build_commit(root)

    assert git_sha is None
    assert "policyengine_uk/__init__.py" in reason and "missing" in reason


@pytest.mark.skipif(
    os.name == "nt" or os.geteuid() == 0, reason="needs POSIX permissions"
)
def test_records_nothing_when_a_tracked_directory_is_unreadable(project):
    # git can still lstat the files, so status is clean; hatchling's walk
    # skips the directory silently and the wheel would lack rate.yaml.
    root, _ = project
    parameters = root / "policyengine_uk" / "parameters"
    parameters.chmod(0o311)
    try:
        assert _git(root, "status", "--porcelain") == ""
        git_sha, reason = _find_build_commit(root)
    finally:
        parameters.chmod(0o755)

    assert git_sha is None
    assert "rate.yaml" in reason


def test_records_nothing_for_context_formatted_dependency(project):
    # hatchling fills {env:...} from the build environment, so METADATA would
    # depend on the machine.
    root, _ = project
    pyproject = root / "pyproject.toml"
    pyproject.write_text(
        pyproject.read_text().replace(
            '"policyengine-core>=', '"policyengine-core>={env:PE_CORE_MIN:', 1
        )
    )
    _commit(root, "context formatting")

    git_sha, reason = _find_build_commit(root)

    assert git_sha is None
    assert "context formatting" in reason


def test_build_info_name_matches_the_reader():
    assert hatch_build.BUILD_INFO_NAME == build_metadata.BUILD_INFO_NAME


def _fail_hook_git(monkeypatch, error):
    """Make only the hook's own git calls fail; build_metadata's still run."""
    calls = []
    real_run = hatch_build.subprocess.run

    def run(args, **kwargs):
        if "--no-replace-objects" in args:
            calls.append(kwargs.get("timeout"))
            raise error(args, kwargs)
        return real_run(args, **kwargs)

    monkeypatch.setattr(hatch_build.subprocess, "run", run)
    return calls


def test_records_nothing_without_git_executable(project, monkeypatch):
    root, _ = project
    calls = _fail_hook_git(monkeypatch, lambda args, kwargs: FileNotFoundError("git"))

    assert _find_build_commit(root) == (None, "git status failed")
    assert calls


def test_records_nothing_when_git_times_out(project, monkeypatch):
    root, _ = project
    calls = _fail_hook_git(
        monkeypatch,
        lambda args, kwargs: subprocess.TimeoutExpired(args, kwargs.get("timeout")),
    )

    assert _find_build_commit(root) == (None, "git status failed")
    assert calls and all(timeout is not None for timeout in calls)


def test_records_nothing_when_git_hashes_fewer_files(project, monkeypatch):
    # Every input must be compared; a short answer must not skip the rest.
    root, _ = project
    real_run = hatch_build.subprocess.run

    def truncated_hash_object(args, **kwargs):
        result = real_run(args, **kwargs)
        if "hash-object" in args:
            result.stdout = result.stdout.splitlines(keepends=True)[0]
        return result

    monkeypatch.setattr(hatch_build.subprocess, "run", truncated_hash_object)

    assert _find_build_commit(root) == (None, "git hash-object failed")


def test_index_must_equal_heads_tree_whatever_git_status_says(project, monkeypatch):
    # A stale cache-tree or commit-graph can make status describe another
    # tree. Stage other content, leave the working file matching the index,
    # and make status blind: only the index-to-HEAD comparison is left.
    root, _ = project
    _modify_tracked(root)
    _git(root, "add", "-A")
    real_git_output = hatch_build._git_output

    def blind_status(build_metadata, root, *args):
        if "status" in args:
            return b""
        return real_git_output(build_metadata, root, *args)

    monkeypatch.setattr(hatch_build, "_git_output", blind_status)

    assert _find_build_commit(root) == (None, "the index differs from HEAD's tree")


@pytest.mark.skipif(os.name == "nt", reason="needs POSIX file modes")
def test_records_nothing_for_a_setgid_input(project):
    # The wheel keeps the bit; git does not track it.
    root, _ = project
    rate = root / "policyengine_uk" / "parameters" / "rate.yaml"
    try:
        rate.chmod(rate.stat().st_mode | stat.S_ISGID)
    except OSError:
        pytest.skip("cannot set the setgid bit here")
    if not rate.stat().st_mode & stat.S_ISGID:
        pytest.skip("the file system dropped the setgid bit")

    git_sha, reason = _find_build_commit(root)

    assert git_sha is None
    assert "setuid, setgid or sticky" in reason


def test_records_nothing_when_git_cannot_compare_a_tracked_file(project):
    # Policy, beside the content checks: if git does not compare every
    # tracked file with the working tree, the tree is not vouched for, even
    # where the wheel never reads the hidden file.
    root, _ = project
    (root / "notes.txt").write_text("notes\n")
    _commit(root, "notes")
    _git(root, "update-index", "--assume-unchanged", "notes.txt")
    (root / "notes.txt").write_text("changed\n")
    assert _git(root, "status", "--porcelain") == ""

    git_sha, reason = _find_build_commit(root)

    assert git_sha is None
    assert "notes.txt" in reason and "assume-unchanged" in reason


def test_hash_object_batches_stay_under_the_command_line_budget():
    paths = [
        f"policyengine_uk/parameters/{index:05d}/rate.yaml" for index in range(3000)
    ]

    batches = list(hatch_build._batches(paths))

    assert [path for batch in batches for path in batch] == paths
    assert len(batches) > 1
    assert all(
        sum(len(path) + 1 for path in batch) <= hatch_build.HASH_OBJECT_BATCH_CHARACTERS
        for batch in batches
    )


def test_records_head_with_a_committed_hatch_toml(project):
    # The HEAD tree carries hatch.toml's contents; an empty copy would select
    # other files and refuse a clean checkout.
    root, _ = project
    (root / "hatch.toml").write_text(
        "[build.targets.wheel]\n"
        'packages = ["policyengine_uk"]\n'
        'exclude = ["policyengine_uk/parameters/rate.yaml"]\n'
        "[build.targets.wheel.hooks.custom]\n"
        'path = "hatch_build.py"\n'
    )
    head = _commit(root, "hatch.toml")

    assert _find_build_commit(root) == (head, "")


def test_selection_must_match_heads_exactly(project):
    # An extra input that HEAD's tree would not select is refused too.
    root, _ = project
    builder = WheelBuilder(str(root))
    paths = _wheel_input_paths(root)

    assert hatch_build.head_selection_difference(builder, paths, build_metadata) == ""
    assert hatch_build.head_selection_difference(
        builder, [*paths, "extra.txt"], build_metadata
    )


def _set_wheel_option(root: Path, line: str) -> None:
    pyproject = root / "pyproject.toml"
    pyproject.write_text(
        pyproject.read_text().replace(
            'packages = ["policyengine_uk"]',
            f'packages = ["policyengine_uk"]\n{line}',
            1,
        )
    )


def test_records_nothing_for_a_non_reproducible_wheel(project):
    root, _ = project
    _set_wheel_option(root, "reproducible = false")
    _commit(root, "not reproducible")

    assert _find_build_commit(root) == (None, "the wheel build is not reproducible")


def test_records_nothing_for_dynamic_metadata(project):
    root, _ = project
    version = _project_version(root)
    pyproject = root / "pyproject.toml"
    pyproject.write_text(
        pyproject.read_text().replace(
            f'version = "{version}"', 'dynamic = ["version"]', 1
        )
        + '\n[tool.hatch.version]\npath = "policyengine_uk/__init__.py"\n'
    )
    (root / "policyengine_uk" / "__init__.py").write_text(
        f'__version__ = "{version}"\n'
    )
    _commit(root, "dynamic version")

    assert _find_build_commit(root) == (None, "the project declares dynamic metadata")


def test_records_nothing_for_metadata_hooks(project):
    root, _ = project
    pyproject = root / "pyproject.toml"
    pyproject.write_text(
        pyproject.read_text()
        + '\n[tool.hatch.metadata.hooks.custom]\npath = "metadata_hook.py"\n'
    )
    (root / "metadata_hook.py").write_text(
        "from hatchling.metadata.plugin.interface import MetadataHookInterface\n\n\n"
        "class Hook(MetadataHookInterface):\n"
        "    def update(self, metadata):\n"
        "        pass\n"
    )
    _commit(root, "metadata hook")

    assert _find_build_commit(root) == (None, "the project configures metadata hooks")


def test_records_nothing_when_the_temporary_directory_is_inside(project, monkeypatch):
    # The record would be packaged from there.
    root, _ = project
    monkeypatch.setattr(hatch_build.tempfile, "tempdir", str(root / "scratch"))

    assert _find_build_commit(root) == (
        None,
        "the temporary directory is inside the project",
    )


def test_build_metadata_loads_with_the_standard_library_only(tmp_path):
    # hatch_build.py loads build_metadata.py in the build environment, where
    # none of policyengine-uk's dependencies are installed. -S leaves out
    # site-packages.
    probe = (
        "import importlib.util, sys\n"
        "from pathlib import Path\n"
        "spec = importlib.util.spec_from_file_location('probe', sys.argv[1])\n"
        "module = importlib.util.module_from_spec(spec)\n"
        "spec.loader.exec_module(module)\n"
        "print(module._get_git_sha(Path(sys.argv[2])))\n"
    )

    output = subprocess.check_output(
        [
            sys.executable,
            "-I",
            "-S",
            "-c",
            probe,
            str(BUILD_METADATA_PATH),
            str(tmp_path / "policyengine_uk"),
        ],
        text=True,
    )

    assert output.strip() == "None"


# The hook inside real hatchling builds.


def test_wheel_records_head(project, tmp_path):
    root, head = project

    wheel = _build_wheel(root, tmp_path / "dist")

    assert _wheel_build_info(wheel) == {
        "git_sha": head,
        "version": _project_version(root),
    }
    with zipfile.ZipFile(wheel) as archive:
        [name] = [name for name in archive.namelist() if name.endswith(BUILD_INFO)]
        assert (
            name == f"policyengine_uk-{_project_version(root)}.dist-info/{BUILD_INFO}"
        )
        assert archive.getinfo(name).external_attr >> 16 & 0o777 == 0o644
        assert name in archive.read(name.replace(BUILD_INFO, "RECORD")).decode()


def test_wheel_from_dirty_tree_records_nothing(project, tmp_path):
    root, _ = project
    _modify_tracked(root)

    assert _wheel_build_info(_build_wheel(root, tmp_path / "dist")) is None


def _initialize_hook(
    root: Path, out: Path, version: str, build_hooks: tuple = ("custom",)
) -> dict:
    builder = WheelBuilder(str(root))
    hook = hatch_build.BuildInfoHook(
        str(root),
        {"path": "hatch_build.py"},
        builder.config,
        builder.metadata,
        str(out),
        "wheel",
        builder.app,
    )
    # hatchling names the hooks of this build before any initialize runs.
    build_data = {"extra_metadata": {}, "build_hooks": build_hooks}
    hook.initialize(version, build_data)
    recorded = {
        target: json.loads(Path(source).read_text())
        for source, target in build_data["extra_metadata"].items()
    }
    hook.finalize(version, build_data, str(out / "artifact.whl"))
    return recorded


def test_hook_records_head_for_a_standard_wheel(project, tmp_path):
    root, head = project

    assert _initialize_hook(root, tmp_path, "standard") == {
        "build_info.json": {"git_sha": head, "version": _project_version(root)}
    }


def test_hook_records_nothing_beside_another_build_hook(project, tmp_path):
    # Another hook could add files or metadata this one never checks.
    root, _ = project

    assert _initialize_hook(root, tmp_path, "standard", ("custom", "other")) == {}


def test_hook_removes_its_directory_even_if_the_build_fails(
    project, tmp_path, monkeypatch
):
    # finalize does not run when a build fails after initialize.
    root, _ = project
    registered = []
    monkeypatch.setattr(
        hatch_build.atexit, "register", lambda *args: registered.append(args)
    )

    _initialize_hook(root, tmp_path, "standard")

    assert len(registered) == 1
    function, directory, ignore_errors = registered[0]
    assert function is hatch_build.shutil.rmtree and ignore_errors is True
    assert Path(directory).name.startswith("policyengine-uk-build-info-")


def test_hook_records_nothing_for_an_editable_wheel(project, tmp_path):
    # An editable install reads the checkout's HEAD at runtime instead.
    root, _ = project

    assert _initialize_hook(root, tmp_path, "editable") == {}


def test_wheel_built_from_sdist_records_nothing(project, tmp_path):
    root, _ = project
    sdist = _build_sdist(root, tmp_path / "dist")
    with tarfile.open(sdist) as archive:
        names = archive.getnames()
        archive.extractall(tmp_path / "unpacked", filter="data")
    [unpacked] = (tmp_path / "unpacked").iterdir()

    wheel = _build_wheel(unpacked, tmp_path / "dist-from-sdist")

    assert any(name.endswith("/hatch_build.py") for name in names)
    assert not any(name.endswith("build_info.json") for name in names)
    assert _wheel_build_info(wheel) is None


def test_sdist_does_not_depend_on_the_commit(project, tmp_path):
    root, head = project
    first_sdist = _build_sdist(root, tmp_path / "first").read_bytes()
    first_wheel = _wheel_build_info(_build_wheel(root, tmp_path / "first"))
    next_head = _commit(root, "next")

    second_sdist = _build_sdist(root, tmp_path / "second").read_bytes()
    second_wheel = _wheel_build_info(_build_wheel(root, tmp_path / "second"))

    assert first_sdist == second_sdist
    assert first_wheel["git_sha"] == head != next_head == second_wheel["git_sha"]


def test_wheel_build_is_reproducible(project, tmp_path):
    root, _ = project

    first = _build_wheel(root, tmp_path / "first").read_bytes()
    second = _build_wheel(root, tmp_path / "second").read_bytes()

    assert first == second


def _tree_snapshot(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file() and ".git" not in path.relative_to(root).parts
    }


def test_build_writes_nothing_into_the_source_tree(project, tmp_path, monkeypatch):
    root, _ = project
    before = _tree_snapshot(root)
    temporary = []
    real_mkdtemp = hatch_build.tempfile.mkdtemp

    def recording_mkdtemp(*args, **kwargs):
        temporary.append(real_mkdtemp(*args, **kwargs))
        return temporary[-1]

    # hatchling loads its own copy of hatch_build.py, which shares the
    # tempfile module.
    monkeypatch.setattr(hatch_build.tempfile, "mkdtemp", recording_mkdtemp)
    # Write bytecode as CI does, whatever PYTHONDONTWRITEBYTECODE says here.
    monkeypatch.setattr(sys, "dont_write_bytecode", False)

    wheel = _build_wheel(root, tmp_path / "dist")
    after = _tree_snapshot(root)
    added = sorted(set(after) - set(before))

    assert _wheel_build_info(wheel) is not None
    assert {path: after[path] for path in before} == before
    # The only new file is Python's (gitignored) cache of hatch_build.py
    # itself, from hatchling importing it. Loading build_metadata leaves
    # nothing in the package.
    assert len(added) <= 1
    assert all(
        re.fullmatch(r"__pycache__/hatch_build\.[^/]+\.pyc", path) for path in added
    )
    assert _git(root, "status", "--porcelain") == ""
    assert temporary and not any(Path(path).exists() for path in temporary)


def _cache_alternate_source(path: Path, alternate: bytes) -> None:
    """Leave a valid timestamp .pyc of ``alternate`` beside ``path``'s source.

    Python runs a cached .pyc whose recorded mtime and size match the source,
    so ``alternate`` must be no longer than the source; it is padded.
    """
    original = path.read_bytes()
    times = path.stat()
    assert len(alternate) <= len(original)
    path.write_bytes(alternate.ljust(len(original), b" "))
    os.utime(path, ns=(times.st_atime_ns, times.st_mtime_ns))
    py_compile.compile(
        str(path),
        doraise=True,
        invalidation_mode=py_compile.PycInvalidationMode.TIMESTAMP,
    )
    path.write_bytes(original)
    os.utime(path, ns=(times.st_atime_ns, times.st_mtime_ns))


def test_stale_build_metadata_cache_is_not_run(project, tmp_path):
    # A cached build_metadata that reports an older commit must not run in
    # place of the checked source.
    root, old_head = project
    _commit_change(root)
    head = _git(root, "rev-parse", "HEAD")
    path = root / "policyengine_uk" / "build_metadata.py"
    lines = path.read_bytes().splitlines(keepends=True)
    comments = [i for i, line in enumerate(lines) if line.startswith(b"#")][:4]
    alternate = b"".join(line for i, line in enumerate(lines) if i not in comments)
    alternate += f'\n_get_checkout_git_sha = lambda _: "{old_head}"\n'.encode()
    _cache_alternate_source(path, alternate)

    build_info = _wheel_build_info(_build_wheel(root, tmp_path / "dist"))

    assert build_info["git_sha"] == head != old_head


def test_stale_hook_cache_records_nothing(project, tmp_path):
    # A cached copy of this hook with a check removed runs instead of the
    # source, which was checked against HEAD. The hook compares the code it
    # was loaded from with its source and records nothing.
    root, _ = project
    path = root / "hatch_build.py"
    source = path.read_bytes()
    assert source.count(b"    if status:\n") == 1
    _cache_alternate_source(
        path, source.replace(b"    if status:\n", b"    if False :\n")
    )
    # Only the status check catches this file, which the wheel never reads.
    _untracked_outside_package(root)

    wheel = _build_wheel(root, tmp_path / "dist")

    assert _wheel_build_info(wheel) is None


def test_failed_lookup_records_nothing_and_the_wheel_still_builds(project, tmp_path):
    root, _ = project
    (root / "policyengine_uk" / "build_metadata.py").unlink()
    _commit(root, "drop build_metadata")

    wheel = _build_wheel(root, tmp_path / "dist")

    assert wheel.is_file()
    assert _wheel_build_info(wheel) is None


# Property: whenever the hook records commit S, the wheel is byte-identical to
# the wheel built from a fresh clone of S. A tree with no changes records
# HEAD.


def _add_bytecode(root: Path) -> None:
    cache = root / "policyengine_uk" / "__pycache__"
    cache.mkdir(exist_ok=True)
    (cache / "build_metadata.cpython-313.pyc").write_bytes(b"pyc")


def _add_ignored_data(root: Path) -> None:
    (root / "policyengine_uk" / "frs_2023.h5").write_bytes(b"data")


def _commit_change(root: Path) -> None:
    rate = root / "policyengine_uk" / "parameters" / "rate.yaml"
    rate.write_text(rate.read_text() + "  2026-01-01: 0.21\n")
    _commit(root, "change rate")


BENIGN_CHANGES = {
    "bytecode": _add_bytecode,
    "ignored data": _add_ignored_data,
    "new commit": _commit_change,
}
TREE_CHANGES = {**BENIGN_CHANGES, **DIRTY_TREES}


@settings(
    max_examples=25,
    deadline=None,
    suppress_health_check=SUPPRESSED_HEALTH_CHECKS,
)
@given(changes=st.lists(st.sampled_from(sorted(TREE_CHANGES)), max_size=3))
def test_recorded_commit_rebuilds_the_same_wheel(tmp_path_factory, changes):
    base = tmp_path_factory.mktemp("property")
    root = base / "policyengine-uk"
    _make_project(root)
    for change in changes:
        try:
            TREE_CHANGES[change](root)
        except (FileNotFoundError, FileExistsError):
            # The change no longer applies, for example a second deletion.
            pass

    wheel = _build_wheel(root, base / "dist")
    build_info = _wheel_build_info(wheel)

    if all(change in BENIGN_CHANGES for change in changes):
        assert build_info is not None
        assert build_info["git_sha"] == _git(root, "rev-parse", "HEAD")
    if build_info is not None:
        clone = base / "clone"
        subprocess.check_call(
            ["git", "clone", "-q", "--no-hardlinks", str(root), str(clone)],
            stderr=subprocess.DEVNULL,
        )
        _git(clone, "checkout", "-q", build_info["git_sha"])
        assert (
            wheel.read_bytes() == _build_wheel(clone, base / "dist-clone").read_bytes()
        )


# The runtime reader: _get_git_sha falls back to the recorded commit.

_get_git_sha = build_metadata._get_git_sha
_get_build_info_git_sha = build_metadata._get_build_info_git_sha


def _install(
    site_packages: Path,
    build_info: object = None,
    direct_url: object = None,
    version: str = "2.0.0",
) -> Path:
    """Lay out an installed policyengine-uk with optional dist-info records."""
    package_root = site_packages / "policyengine_uk"
    package_root.mkdir(parents=True)
    (package_root / "__init__.py").write_text("")
    dist_info = site_packages / f"policyengine_uk-{version}.dist-info"
    dist_info.mkdir()
    (dist_info / "METADATA").write_text(
        f"Metadata-Version: 2.1\nName: policyengine-uk\nVersion: {version}\n"
    )
    for relative_path, record in (
        (BUILD_INFO, build_info),
        ("direct_url.json", direct_url),
    ):
        if record is not None:
            path = dist_info / relative_path
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(record if isinstance(record, str) else json.dumps(record))
    return package_root


def test_git_sha_reads_recorded_build_commit(tmp_path):
    package_root = _install(
        tmp_path / "site-packages", {"git_sha": SHA, "version": "2.0.0"}
    )

    assert _get_git_sha(package_root) == SHA


def test_git_sha_reads_recorded_build_commit_inside_another_repository(tmp_path):
    # The policyengine-uk-data layout, installed from PyPI.
    uk_data = tmp_path / "policyengine-uk-data"
    uk_data.mkdir()
    _git(uk_data, "init", "-q")
    _commit(uk_data, "uk-data")
    package_root = _install(
        uk_data / ".venv/lib/python3.13/site-packages",
        {"git_sha": SHA, "version": "2.0.0"},
    )

    assert _get_git_sha(package_root) == SHA


def test_git_sha_prefers_installer_record_to_recorded_build_commit(tmp_path):
    package_root = _install(
        tmp_path / "site-packages",
        build_info={"git_sha": OTHER_SHA, "version": "2.0.0"},
        direct_url={
            "url": "https://example.com",
            "vcs_info": {"vcs": "git", "commit_id": SHA},
        },
    )

    assert _get_git_sha(package_root) == SHA


def test_git_sha_ignores_recorded_build_commit_of_another_copy(tmp_path, monkeypatch):
    other_site_packages = tmp_path / "other-site-packages"
    _install(other_site_packages, {"git_sha": SHA, "version": "2.0.0"})
    monkeypatch.syspath_prepend(str(other_site_packages))
    package_root = _install(tmp_path / "site-packages")

    assert _get_git_sha(package_root) is None


@pytest.mark.skipif(not hasattr(os, "mkfifo"), reason="needs named pipes")
def test_git_sha_does_not_block_on_fifo_build_info(tmp_path):
    package_root = _install(tmp_path / "site-packages")
    build_info = next((tmp_path / "site-packages").glob("*.dist-info")) / BUILD_INFO
    build_info.parent.mkdir(parents=True)
    os.mkfifo(build_info)
    result = {}
    lookup = threading.Thread(
        target=lambda: result.update(sha=_get_git_sha(package_root)), daemon=True
    )
    lookup.start()
    lookup.join(timeout=10)
    # Decide before releasing the reader, which would let a blocked lookup
    # finish late and pass.
    timed_out = lookup.is_alive()
    if timed_out:
        # A lookup stuck elsewhere leaves no reader to release (ENXIO); the
        # timeout assertion below reports it.
        with contextlib.suppress(OSError):
            os.close(os.open(build_info, os.O_WRONLY | os.O_NONBLOCK))
        lookup.join(timeout=5)
    assert not timed_out
    # A lookup that raised leaves no result, so this fails with KeyError.
    assert result["sha"] is None


def test_git_sha_ignores_build_info_in_a_source_tree(tmp_path):
    # Only an installed distribution's dist-info is read, never a file that
    # sits in a checkout or source directory.
    root = tmp_path / "src"
    (root / "policyengine_uk").mkdir(parents=True)
    (root / "extra_metadata").mkdir()
    (root / BUILD_INFO).write_text(json.dumps({"git_sha": SHA, "version": "2.0.0"}))

    assert _get_git_sha(root / "policyengine_uk") is None


@pytest.mark.parametrize(
    "build_info",
    [
        "not json",
        [],
        {},
        {"git_sha": SHA},
        {"git_sha": SHA, "version": "1.9.0"},
        {"git_sha": SHA.upper(), "version": "2.0.0"},
        {"git_sha": SHA[:12], "version": "2.0.0"},
        {"git_sha": None, "version": "2.0.0"},
        {"git_sha": SHA, "version": None},
    ],
)
def test_git_sha_ignores_unusable_build_info(tmp_path, build_info):
    package_root = _install(tmp_path / "site-packages", build_info)

    assert _get_git_sha(package_root) is None


JSON_VALUES = st.recursive(
    st.none() | st.booleans() | st.integers() | st.text(max_size=8),
    lambda children: (
        st.lists(children, max_size=3)
        | st.dictionaries(st.text(max_size=8), children, max_size=3)
    ),
    max_leaves=8,
)
GIT_SHAS = st.one_of(
    st.text(alphabet="0123456789abcdef", min_size=40, max_size=40),
    st.text(alphabet="0123456789abcdef", min_size=64, max_size=64),
    st.text(alphabet="0123456789abcdefABCDEF", max_size=70),
    JSON_VALUES,
)
BUILD_INFOS = st.one_of(
    JSON_VALUES,
    st.fixed_dictionaries(
        {
            "git_sha": GIT_SHAS,
            "version": st.one_of(
                st.sampled_from(["2.0.0", "2.0", "2.0.1"]), JSON_VALUES
            ),
        }
    ),
)


@settings(
    max_examples=60,
    deadline=None,
    suppress_health_check=SUPPRESSED_HEALTH_CHECKS,
)
@given(build_info=BUILD_INFOS)
def test_build_info_property_never_invents_a_sha(tmp_path_factory, build_info):
    package_root = _install(
        tmp_path_factory.mktemp("site-packages"), json.dumps(build_info)
    )
    git_sha = build_info.get("git_sha") if isinstance(build_info, dict) else None
    is_recorded_commit = (
        isinstance(build_info, dict)
        and build_info.get("version") == "2.0.0"
        and isinstance(git_sha, str)
        and len(git_sha) in {40, 64}
        and set(git_sha) <= set("0123456789abcdef")
    )

    assert _get_build_info_git_sha(package_root) == (
        git_sha if is_recorded_commit else None
    )


# Round trip: build a wheel in a temporary policyengine-uk repository,
# install it into a virtualenv inside an unrelated repository, and read the
# commit back with the installed copy's own build_metadata.

ROUND_TRIP_PROBE = """
import importlib.util, json, sys, sysconfig, types
from pathlib import Path

# The wheel is installed without dependencies; stand in for the one that
# get_runtime_metadata calls.
core = types.ModuleType("policyengine_core")
core.get_runtime_metadata = lambda: {"name": "policyengine-core"}
sys.modules["policyengine_core"] = core
path = Path(sysconfig.get_paths()["purelib"], "policyengine_uk", "build_metadata.py")
spec = importlib.util.spec_from_file_location("installed_build_metadata", path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
metadata = module.get_runtime_metadata()
print(json.dumps({"path": str(path), "git_sha": metadata["git_sha"],
                  "version": metadata["version"]}))
"""


def _venv_python(environment: Path) -> Path:
    return environment / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def _install_with_pip(environment: Path, wheel: Path) -> None:
    # Symlinks, as `python -m venv` uses on POSIX: a copied interpreter can
    # miss its shared library.
    venv.EnvBuilder(with_pip=True, symlinks=os.name != "nt").create(environment)
    subprocess.check_call(
        [
            str(_venv_python(environment)),
            "-m",
            "pip",
            "install",
            "--quiet",
            "--no-deps",
            "--no-index",
            str(wheel),
        ]
    )


def _install_with_uv(environment: Path, wheel: Path) -> None:
    uv = shutil.which("uv")
    if uv is None:
        pytest.skip("uv is not installed")
    env = {key: value for key, value in os.environ.items() if key != "VIRTUAL_ENV"}
    subprocess.check_call(
        [uv, "venv", "--quiet", "--python", sys.executable, str(environment)], env=env
    )
    subprocess.check_call(
        [
            uv,
            "pip",
            "install",
            "--quiet",
            "--offline",
            "--no-deps",
            "--python",
            str(_venv_python(environment)),
            str(wheel),
        ],
        env=env,
    )


@pytest.mark.parametrize("install", [_install_with_pip, _install_with_uv])
def test_built_wheel_round_trip(tmp_path, install):
    root = tmp_path / "policyengine-uk"
    head = _make_project(root)
    wheel = _build_wheel(root, tmp_path / "dist")
    uk_data = tmp_path / "policyengine-uk-data"
    uk_data.mkdir()
    _git(uk_data, "init", "-q")
    uk_data_head = _commit(uk_data, "uk-data")

    install(uk_data / ".venv", wheel)
    output = subprocess.check_output(
        [str(_venv_python(uk_data / ".venv")), "-I", "-c", ROUND_TRIP_PROBE],
        cwd=uk_data,
        text=True,
    )
    result = json.loads(output)

    assert Path(result["path"]).resolve().is_relative_to((uk_data / ".venv").resolve())
    assert result["version"] == _project_version(root)
    assert result["git_sha"] == head
    assert head != uk_data_head
