"""policyengine-uk runs only on a policyengine-core version it has qualified.

The stored-draw check (policyengine_uk.utils.stored_draws) reads core's
private members and relies on how core stores, carries and caches inputs.
Tests qualify that behaviour for each exact core version in
QUALIFIED_CORE_VERSIONS. The resolver floor in pyproject.toml does not.

Both checks fail on any other version, including a new core that a lock
refresh brings in. Before adding a version to QUALIFIED_CORE_VERSIONS, run
these on that exact version and record the result:

    uv run --frozen --with 'policyengine-core==<version>' pytest \
        policyengine_uk/tests/test_stored_draw_input_source.py \
        policyengine_uk/tests/test_stored_draw_consumers.py \
        policyengine_uk/tests/test_stored_draw_core_route.py \
        policyengine_uk/tests/test_supplied_input_tightening.py -n 4

The checks run when the tests run, not when policyengine_uk is imported.
"""

import importlib.metadata
import re
from pathlib import Path

from policyengine_uk.utils.stored_draws import QUALIFIED_CORE_VERSIONS

PACKAGE = Path(__file__).resolve().parents[2]
RERUN = (
    "Run the stored-draw qualification tests on that exact version (see this "
    "file's docstring) before adding it to QUALIFIED_CORE_VERSIONS in "
    "policyengine_uk/utils/stored_draws.py."
)


def locked_core_version(lock_text: str) -> str:
    match = re.search(
        r'^\[\[package\]\]\nname = "policyengine-core"\nversion = "([^"]+)"',
        lock_text,
        re.MULTILINE,
    )
    assert match, "uv.lock names no policyengine-core package."
    return match.group(1)


def find_lock() -> Path:
    """uv.lock beside the source tree, or in the directory the tests run
    from: a test of the built wheel runs from the checkout, whose lock
    installed the environment."""
    for directory in (PACKAGE.parent, Path.cwd()):
        lock = directory / "uv.lock"
        if lock.is_file():
            return lock
    raise AssertionError(
        f"No uv.lock beside {PACKAGE} or in {Path.cwd()}: run the tests from "
        "the checkout whose lock installed this environment."
    )


def test_the_locked_core_is_qualified():
    version = locked_core_version(find_lock().read_text())
    assert version in QUALIFIED_CORE_VERSIONS, (
        f"uv.lock holds policyengine-core {version}, which is not in "
        f"{sorted(QUALIFIED_CORE_VERSIONS)}. {RERUN}"
    )


def test_the_installed_core_is_qualified():
    version = importlib.metadata.version("policyengine-core")
    assert version in QUALIFIED_CORE_VERSIONS, (
        f"policyengine-core {version} is installed, which is not in "
        f"{sorted(QUALIFIED_CORE_VERSIONS)}. {RERUN}"
    )


def test_the_lock_parser_reads_the_core_entry():
    lock = (
        '[[package]]\nname = "policyengine-core-extra"\nversion = "9.9.9"\n\n'
        '[[package]]\nname = "policyengine-core"\nversion = "3.34.3"\n'
    )
    assert locked_core_version(lock) == "3.34.3"
    assert "3.34.3" not in QUALIFIED_CORE_VERSIONS
