"""The Test job's shards run every test exactly once.

CI runs ``pytest policyengine_uk/tests`` as several jobs, each with
``--shard K/N`` (conftest.py), and then runs ``.github/check_test_shards.py``
over their JUnit files and an unsharded ``pytest --collect-only -q`` listing.
These tests hold the two halves to the invariants the split relies on:

1. ``shard_of(nodeid, N)`` is between 1 and N and depends only on its
   arguments, so it is the same in every process and on every runner.
2. For any set of node ids and any N, the N shards are disjoint and their
   union is the whole set.
3. ``parse_shard`` accepts exactly ``K/N`` with 1 <= K <= N.
4. ``junit_key`` gives a node id the name pytest gives it in JUnit XML.
5. The check passes when every collected test ran in exactly one shard and
   none failed, and reports a test that is missing, repeated, not collected
   or failed.
6. With real pytest runs, the collection listing and the shards' JUnit files
   pass the check, with and without pytest-xdist, and fail it if a shard's
   file is left out.
"""

import argparse
import importlib.util
import os
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ElementTree
from pathlib import Path

import pytest
from hypothesis import HealthCheck, example, given, settings
from hypothesis import strategies as st

TESTS_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = TESTS_DIR.parents[1]
CHECKER = REPO_ROOT / ".github" / "check_test_shards.py"

if not CHECKER.exists():
    pytest.skip(
        "the .github folder is not part of an installed package",
        allow_module_level=True,
    )

_spec = importlib.util.spec_from_file_location("check_test_shards", CHECKER)
checker = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(checker)

PROPERTY_SETTINGS = settings(
    max_examples=200,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.function_scoped_fixture],
)


@pytest.fixture
def conftest(request):
    path = TESTS_DIR / "conftest.py"
    for plugin in request.config.pluginmanager.get_plugins():
        if getattr(plugin, "__file__", None) and Path(plugin.__file__) == path:
            return plugin
    raise AssertionError(f"{path} is not loaded as a plugin")


# Node ids as pytest writes them: a path, optional classes, a test name and
# optional parameters. pytest escapes non-ASCII and control characters in
# parameter ids, so the parameters here are any printable ASCII text,
# including "[", "]" and "::".
_identifier = st.from_regex(r"[A-Za-z_][A-Za-z0-9_]{0,12}", fullmatch=True)
_path = st.lists(_identifier, min_size=1, max_size=4).map(
    lambda parts: "/".join(parts) + ".py"
)
_printable = st.characters(min_codepoint=0x20, max_codepoint=0x7E)
_params = st.one_of(
    st.just(""),
    st.text(alphabet=_printable, max_size=20).map(lambda text: f"[{text}]"),
)
nodeids = st.builds(
    lambda path, classes, name, params: "::".join([path, *classes, name + params]),
    _path,
    st.lists(_identifier, max_size=2),
    _identifier,
    _params,
)
# Node ids that could come from one collection: distinct, and with distinct
# JUnit names, which pytest's own naming guarantees for real suites.
collections = st.lists(nodeids, max_size=30, unique_by=checker.junit_key)


def junit_cases(ids, outcome="passed"):
    return [(checker.junit_key(nodeid), outcome) for nodeid in ids]


@PROPERTY_SETTINGS
@given(nodeid=nodeids, shards=st.integers(1, 64))
@example(nodeid="policyengine_uk/tests/test_x.py::test_y", shards=3)
def test_shard_is_in_range_and_repeatable(conftest, nodeid, shards):
    shard = conftest.shard_of(nodeid, shards)
    assert 1 <= shard <= shards
    assert shard == conftest.shard_of(nodeid, shards)


def test_shard_does_not_depend_on_the_process(conftest):
    # Pinned values: every runner and pytest-xdist worker must agree, which
    # Python's own hash, salted per process, would not give.
    assert [
        conftest.shard_of("policyengine_uk/tests/test_x.py::test_y", shards)
        for shards in (1, 2, 3, 4, 7)
    ] == [1, 2, 1, 4, 7]
    assert conftest.shard_of("policyengine_uk/tests/test_x.py::test_y[2026-a]", 3) == 2


@PROPERTY_SETTINGS
@given(ids=st.lists(nodeids, max_size=40, unique=True), shards=st.integers(1, 8))
def test_shards_partition_any_collection(conftest, ids, shards):
    members = {
        shard: [nodeid for nodeid in ids if conftest.shard_of(nodeid, shards) == shard]
        for shard in range(1, shards + 1)
    }
    assert sorted(sum(members.values(), [])) == sorted(ids)
    assert sum(len(group) for group in members.values()) == len(ids)


@PROPERTY_SETTINGS
@given(shards=st.integers(1, 200), data=st.data())
def test_parse_shard_accepts_k_of_n(conftest, shards, data):
    shard = data.draw(st.integers(1, shards))
    assert conftest.parse_shard(f"{shard}/{shards}") == (shard, shards)


@pytest.mark.parametrize(
    "value",
    [
        "0/3",
        "4/3",
        "1/0",
        "0/0",
        "3",
        "1/3/5",
        "a/b",
        "1-3",
        "",
        " 1/3",
        "1/3 ",
        "-1/3",
    ],
)
def test_parse_shard_rejects_anything_else(conftest, value):
    with pytest.raises(argparse.ArgumentTypeError):
        conftest.parse_shard(value)


@PROPERTY_SETTINGS
@given(nodeid=nodeids)
@example(nodeid="policyengine_uk/tests/test_x.py::TestA::test_y[a/b.yaml-1]")
@example(nodeid="policyengine_uk/tests/test_x.py::test_y[a::b[c]-d e]")
def test_junit_key_matches_pytest(nodeid):
    # Differential test against pytest's own naming, written out to XML and
    # read back as the check reads it.
    junitxml = pytest.importorskip("_pytest.junitxml")
    names = junitxml.mangle_test_address(nodeid)
    element = ElementTree.Element(
        "testcase",
        classname=".".join(names[:-1]),
        name=junitxml.bin_xml_escape(names[-1]),
    )
    read_back = ElementTree.fromstring(ElementTree.tostring(element))
    assert checker.junit_key(nodeid) == (
        read_back.get("classname"),
        read_back.get("name"),
    )


@PROPERTY_SETTINGS
@given(ids=collections, shards=st.integers(1, 5), data=st.data())
def test_check_passes_exactly_when_every_test_ran_once(conftest, ids, shards, data):
    ran = [
        junit_cases(i for i in ids if conftest.shard_of(i, shards) == shard)
        for shard in range(1, shards + 1)
    ]
    problems, summary = checker.check(ids, ran)
    assert problems == []
    assert summary.startswith(f"{len(ids)} tests collected")

    if not ids:
        return
    victim = data.draw(st.sampled_from(ids))
    key = checker.junit_key(victim)
    home = conftest.shard_of(victim, shards) - 1

    missing = [list(cases) for cases in ran]
    missing[home].remove((key, "passed"))
    problems, _ = checker.check(ids, missing)
    assert [names for title, names in problems if "ran in no shard" in title] == [
        [victim]
    ]

    repeated = [list(cases) for cases in ran]
    repeated[data.draw(st.integers(0, shards - 1))].append((key, "passed"))
    problems, _ = checker.check(ids, repeated)
    assert [names for title, names in problems if "more than once" in title] == [
        [victim]
    ]

    failed = [list(cases) for cases in ran]
    failed[home][failed[home].index((key, "passed"))] = (key, "failed")
    problems, _ = checker.check(ids, failed)
    assert [names for title, names in problems if "failed" in title] == [
        [f"shard {home + 1}: {victim}"]
    ]

    uncollected = [nodeid for nodeid in ids if nodeid != victim]
    problems, _ = checker.check(uncollected, ran)
    assert [names for title, names in problems if "not collected" in title] == [
        [f"{key[0]}::{key[1]}"]
    ]


def test_read_collected_requires_the_listed_count():
    listing = "a/test_x.py::test_one\na/test_x.py::test_two[p]\n\n2 tests collected in 0.01s\n"
    assert checker.read_collected(listing) == [
        "a/test_x.py::test_one",
        "a/test_x.py::test_two[p]",
    ]
    assert checker.read_collected("\nno tests collected in 0.01s\n") == []
    # Warnings follow the listing and may mention a node id.
    with_warnings = listing.replace(
        "\n\n2 tests",
        "\n\n=== warnings summary ===\na/test_x.py::test_one\n  x\n2 tests",
    )
    assert checker.read_collected(with_warnings) == checker.read_collected(listing)
    for bad in (
        "a/test_x.py::test_one\n",
        "a/test_x.py::test_one\n\n2 tests collected in 0.01s\n",
        "a/test_x.py::test_one\na/test_x.py::test_one\n\n2 tests collected in 0.01s\n",
        "a/test_x.py::test_one\n\n1 test collected, 1 error in 0.01s\n",
    ):
        with pytest.raises(checker.ShardCheckError):
            checker.read_collected(bad)


SAMPLE_SUITE = """
import pytest


@pytest.mark.parametrize("value", range(40))
def test_number(value):
    assert value >= 0


@pytest.mark.parametrize(
    "name", ["parameters/gov/a.yaml", "b c", "d[e]", "f::g", "h-1", "caf\\u00e9", "tab\\there"]
)
def test_name(name):
    assert name


class TestGroup:
    @pytest.mark.parametrize("value", ["x", "y"])
    def test_member(self, value):
        assert value

    @pytest.mark.skip(reason="skipped tests still count as run")
    def test_skipped(self):
        raise AssertionError

    @pytest.mark.xfail(strict=True)
    def test_expected_failure(self):
        raise AssertionError
"""


def _pytest(cwd, *args):
    # A clean run of pytest: no options, plugins or coverage settings carried
    # over from the session that runs this test.
    env = {
        name: value
        for name, value in os.environ.items()
        if not name.startswith(("PYTEST_", "COV_CORE_", "COVERAGE_"))
    }
    return subprocess.run(
        [sys.executable, "-m", "pytest", "-p", "no:cacheprovider", *args],
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        timeout=600,
    )


@pytest.mark.parametrize("xdist", [(), ("-n", "2", "--dist", "worksteal")])
def test_real_pytest_shards_pass_the_check(tmp_path, xdist):
    suite = tmp_path / "suite"
    suite.mkdir()
    # The suite's real conftest.py, so this runs the --shard CI uses.
    shutil.copy(TESTS_DIR / "conftest.py", suite / "conftest.py")
    (suite / "test_sample.py").write_text(SAMPLE_SUITE, encoding="utf-8")

    listing = _pytest(tmp_path, "suite", "--collect-only", "-q")
    assert listing.returncode == 0, listing.stdout + listing.stderr
    collected = tmp_path / "collected.txt"
    collected.write_text(listing.stdout, encoding="utf-8")
    assert len(checker.read_collected(listing.stdout)) == 51

    shards = 3
    junit = []
    for shard in range(1, shards + 1):
        junit.append(tmp_path / f"junit-{shard}.xml")
        run = _pytest(
            tmp_path,
            "suite",
            "--shard",
            f"{shard}/{shards}",
            f"--junitxml={junit[-1]}",
            *xdist,
        )
        assert run.returncode == 0, run.stdout + run.stderr
        assert f"shard: {shard} of {shards}" in run.stdout

    sizes = [len(checker.read_junit(path)) for path in junit]
    assert sum(sizes) == 51 and all(sizes)

    def check(*paths):
        return checker.main(
            ["--collected", str(collected), "--junit", *map(str, paths)]
        )

    assert check(*junit) == 0
    assert check(*junit[:-1]) == 1
    assert check(*junit, junit[0]) == 1
    assert check(tmp_path / "absent.xml") == 2
