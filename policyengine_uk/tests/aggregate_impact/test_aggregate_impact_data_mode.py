"""Mandatory-data mode end to end, in a subprocess with this repo's hooks.

A scratch test directory imports the real conftest's hooks, so the cases
exercise the hook ordering pytest actually applies.
"""

import os
import subprocess
import sys
import textwrap

import pytest

CONFTEST = "from policyengine_uk.tests.conftest import *  # noqa: F401,F403\n"
CASES = textwrap.dedent(
    """
    import pytest

    def test_needs_no_data():
        assert True

    @pytest.mark.microsimulation
    def test_needs_data():
        assert True

    @pytest.mark.microsimulation
    @pytest.mark.skip(reason="a skip marker must not hide missing data")
    def test_needs_data_but_is_marked_skip():
        assert True
    """
)


def run(tmp_path, **env_changes):
    (tmp_path / "conftest.py").write_text(CONFTEST)
    (tmp_path / "test_cases.py").write_text(CASES)
    env = {
        k: v
        for k, v in os.environ.items()
        if k
        not in (
            "HUGGING_FACE_TOKEN",
            "POLICYENGINE_UK_DEFAULT_DATASET",
            "POLICYENGINE_UK_REQUIRE_TEST_DATA",
            "PYTEST_ADDOPTS",
        )
    }
    env.update(env_changes)
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            str(tmp_path),
            "-q",
            "-p",
            "no:cacheprovider",
            "-p",
            "no:xdist",
            "--rootdir",
            str(tmp_path),
            "-W",
            "ignore::pytest.PytestUnknownMarkWarning",
        ],
        env=env,
        capture_output=True,
        text=True,
        timeout=600,
    )


def test_without_data_the_data_tests_skip_and_the_rest_run(tmp_path):
    done = run(tmp_path)
    assert done.returncode == 0, done.stdout + done.stderr
    assert "1 passed, 2 skipped" in done.stdout


def test_in_mandatory_mode_every_data_test_fails_even_one_marked_skip(tmp_path):
    done = run(tmp_path, POLICYENGINE_UK_REQUIRE_TEST_DATA="1")
    assert done.returncode != 0
    assert "1 passed, 2 errors" in done.stdout, done.stdout
    assert "skipped" not in done.stdout.splitlines()[-1]
    assert "Mandatory-data mode" in done.stdout


@pytest.mark.parametrize("value", ["maybe", "2"])
def test_an_unrecognised_mode_value_fails_closed(tmp_path, value):
    done = run(tmp_path, POLICYENGINE_UK_REQUIRE_TEST_DATA=value)
    assert done.returncode != 0
    assert "2 errors" in done.stdout, done.stdout
