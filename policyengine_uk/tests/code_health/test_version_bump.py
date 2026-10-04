"""The version bump must keep uv.lock's entry for this package in step.

CI installs with ``uv sync --locked``, which fails when uv.lock disagrees with
pyproject.toml. The lock records this package's own version, so a release that
bumps pyproject.toml without the lock would fail every later pull request.
.github/bump_version.py therefore rewrites that one entry. These tests check
that the rewrite changes the package's own version and nothing else, including
dependencies that happen to share the old version string, both on the real
uv.lock and on generated ones.

They read files from the repository checkout, so they skip when the package is
installed without one.
"""

import importlib.util
import tomllib
from pathlib import Path

import pytest
from hypothesis import given
from hypothesis import strategies as st

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / ".github" / "bump_version.py"
LOCK = ROOT / "uv.lock"
PYPROJECT = ROOT / "pyproject.toml"

if not (SCRIPT.exists() and LOCK.exists() and PYPROJECT.exists()):
    pytest.skip("needs the repository checkout", allow_module_level=True)

spec = importlib.util.spec_from_file_location("bump_version", SCRIPT)
bump_version = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bump_version)

PACKAGE = bump_version.get_project_name(PYPROJECT)

versions = st.tuples(*[st.integers(0, 999)] * 3).map(lambda v: ".".join(map(str, v)))
# Names that share a prefix with this package, plus arbitrary ones.
other_names = st.one_of(
    st.sampled_from([f"{PACKAGE}-data", f"{PACKAGE}2", "policyengine-core"]),
    st.text("abcdefghijklmnopqrstuvwxyz0123456789-", min_size=1, max_size=12),
).filter(lambda name: name != PACKAGE)


def lock_versions(text: str) -> dict:
    return {
        package["name"]: package.get("version")
        for package in tomllib.loads(text)["package"]
    }


def make_lock(entries) -> str:
    blocks = ['version = 1\nrevision = 3\nrequires-python = ">=3.11"\n']
    for name, version, editable in entries:
        source = (
            '{ editable = "." }'
            if editable
            else '{ registry = "https://pypi.org/simple" }'
        )
        blocks.append(
            f'[[package]]\nname = "{name}"\nversion = "{version}"\nsource = {source}\n'
        )
    return "\n".join(blocks)


def test_rewriting_the_real_lock_changes_only_this_package():
    text = LOCK.read_text()
    updated = bump_version.set_lock_version(text, PACKAGE, "9999.0.0")
    before, after = lock_versions(text), lock_versions(updated)
    assert after[PACKAGE] == "9999.0.0"
    assert {k: v for k, v in after.items() if k != PACKAGE} == {
        k: v for k, v in before.items() if k != PACKAGE
    }
    changed = [
        (old, new)
        for old, new in zip(text.splitlines(), updated.splitlines())
        if old != new
    ]
    assert len(changed) == 1
    assert len(text.splitlines()) == len(updated.splitlines())


def test_a_dependency_sharing_the_old_version_is_left_alone():
    text = make_lock(
        [
            ("numpy", "2.113.0", False),
            (PACKAGE, "2.113.0", True),
            ("pandas", "2.113.0", False),
        ]
    )
    updated = bump_version.set_lock_version(text, PACKAGE, "2.113.1")
    assert lock_versions(updated) == {
        "numpy": "2.113.0",
        PACKAGE: "2.113.1",
        "pandas": "2.113.0",
    }


@pytest.mark.parametrize("copies", [0, 2])
def test_a_missing_or_repeated_entry_is_an_error(copies):
    text = make_lock([("numpy", "2.1.3", False)] + [(PACKAGE, "1.0.0", True)] * copies)
    with pytest.raises(ValueError):
        bump_version.set_lock_version(text, PACKAGE, "1.0.1")


@given(
    st.lists(st.tuples(other_names, versions), max_size=6, unique_by=lambda e: e[0]),
    st.integers(0, 6),
    versions,
    versions,
)
def test_rewrite_sets_only_this_package_and_is_idempotent(
    others, position, old_version, new_version
):
    entries = [(name, version, False) for name, version in others]
    entries.insert(min(position, len(entries)), (PACKAGE, old_version, True))
    text = make_lock(entries)

    updated = bump_version.set_lock_version(text, PACKAGE, new_version)

    expected = dict(lock_versions(text), **{PACKAGE: new_version})
    assert lock_versions(updated) == expected
    assert bump_version.set_lock_version(updated, PACKAGE, new_version) == updated
    assert bump_version.set_lock_version(updated, PACKAGE, old_version) == text
