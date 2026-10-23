"""The Test job runs every test exactly once, and goes red unless it passed.

CI runs ``pytest policyengine_uk/tests`` as several jobs, each with
``--shard K/N`` (conftest.py) and ``.github/pytest_outcome_log.py`` recording
each test's outcome. ``.github/check_test_shards.py`` then compares those
records with an unsharded ``pytest --collect-only -q`` listing and the
accepted outcomes in ``.github/test_outcome_allowlist.toml``. These tests hold
the pieces to the invariants the Test job relies on:

1. ``shard_of(nodeid, N)`` is between 1 and N and depends only on its
   arguments, so it is the same in every process and on every runner.
2. For any set of node ids and any N, the N shards are disjoint and their
   union is the whole set.
3. ``parse_shard`` accepts exactly ``K/N`` with 1 <= K <= N.
4. ``read_collected`` returns exactly the listed node ids, or refuses.
5. The check's verdict on any collection, sharding, outcomes and allowlist
   equals an independent model of the rule: every collected test ran in
   exactly one shard, nothing else ran, nothing failed or was left
   unfinished, and every skip, expected failure, XPASS and skipped module is
   accepted by an allowlist entry for this mode and dataset (differential).
6. An allowlist entry can never accept a failure, must say why, and an entry
   that matches nothing is a warning, never a failure.
7. The outcome log records what pytest did, by raw node id, the same with
   and without pytest-xdist: passes, failures in setup, call and teardown,
   skips with their reasons (including a skipped subtest), expected
   failures, XPASSes and skipped modules.
8. With real pytest runs over three shards, with and without xdist, the
   check passes exactly when the allowlist covers the sample suite's skips,
   and fails if a shard's log is left out, repeated, or a test fails.
9. The checked-in allowlist parses, and each entry naming one test names a
   test function that exists.
10. Every pull request and merge queue group reports the required
    "Test / Result" check: the pull request workflow has no path filter and
    runs on merge_group, and the paths its Changes job counts as code are the
    main push workflow's paths. Main push runs are never cancelled.
11. ``changed_code.py`` calls a change code exactly when a path matches a
    pattern as a workflow ``paths`` filter would (``dir/**`` is every file
    under ``dir/``), and calls an empty change list code.
"""

import ast
import fnmatch
import importlib.util
import json
import os
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

import pytest
from hypothesis import HealthCheck, example, given, settings
from hypothesis import strategies as st

TESTS_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = TESTS_DIR.parents[1]
GITHUB_DIR = REPO_ROOT / ".github"
CHECKER = GITHUB_DIR / "check_test_shards.py"
ALLOWLIST = GITHUB_DIR / "test_outcome_allowlist.toml"

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


# Invariants 1 to 3: sharding.


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
    import argparse

    with pytest.raises(argparse.ArgumentTypeError):
        conftest.parse_shard(value)


# Invariant 4: the collection listing.


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


# Invariant 5: the check against an independent model of its rule.

OUTCOMES = ["passed", "failed", "skipped", "xfailed", "xpassed", "incomplete"]
REASONS = ["", "because", "#1986 known", "Requires the dataset", "could not import x"]
modes = st.sampled_from(sorted(checker.MODES))
datas = st.sampled_from(sorted(checker.DATA))


@st.composite
def allowances(draw, ids):
    """An allowlist entry: an exact id, a wildcard or an unrelated path."""
    patterns = st.sampled_from(["*", "mod*.py", "mod_a.py"]) | _path
    if ids:
        patterns = st.sampled_from(ids) | patterns
    reason = draw(st.sampled_from([None, "#1986", "^Requires", "x$"]))
    return checker.Allowance(
        nodeid=draw(patterns),
        outcome=draw(st.sampled_from(sorted(checker.ALLOWABLE_OUTCOMES))),
        why="test",
        reason=None if reason is None else re.compile(reason),
        modes=frozenset(draw(st.sets(modes, min_size=1))),
        data=frozenset(draw(st.sets(datas, min_size=1))),
    )


@st.composite
def runs(draw):
    """A collection, what each shard recorded, an allowlist, a mode and data."""
    collected = draw(st.lists(nodeids, max_size=12, unique=True))
    shards = draw(st.integers(1, 4))
    records = [[] for _ in range(shards)]
    for nodeid in collected:
        # Usually once, sometimes never or twice.
        times = draw(st.sampled_from([1, 1, 1, 1, 0, 2]))
        for _ in range(times):
            records[draw(st.integers(0, shards - 1))].append(
                checker.Record(
                    nodeid,
                    draw(st.sampled_from(OUTCOMES)),
                    draw(st.sampled_from(REASONS)),
                )
            )
    # Tests nobody collected, and skipped or broken modules.
    for nodeid in draw(st.lists(nodeids, max_size=2)):
        if nodeid not in collected:
            records[draw(st.integers(0, shards - 1))].append(
                checker.Record(nodeid, "passed")
            )
    modules = draw(st.lists(st.sampled_from(["mod_a.py", "mod_b.py"]), max_size=2))
    for module in modules:
        outcome = draw(st.sampled_from(["collect-skipped", "collect-failed"]))
        for shard in range(shards):
            records[shard].append(checker.Record(module, outcome, "gone"))
    allowlist = draw(st.lists(allowances(collected + modules), max_size=4))
    return collected, records, allowlist, draw(modes), draw(datas)


def model_passes(collected, records, allowlist, mode, data):
    """The rule, written independently of the check."""
    flat = [r for shard in records for r in shard]
    tests = [r for r in flat if r.outcome not in checker.COLLECTOR_OUTCOMES]
    counts = Counter(r.nodeid for r in tests)
    if any(counts[nodeid] != 1 for nodeid in collected):
        return False
    if any(nodeid not in collected for nodeid in counts):
        return False
    for record in flat:
        if record.outcome == "passed":
            continue
        if record.outcome in {"failed", "incomplete", "collect-failed"}:
            return False
        accepted = any(
            mode in a.modes
            and data in a.data
            and a.outcome == record.outcome
            and fnmatch.fnmatchcase(record.nodeid, a.nodeid)
            and (a.reason is None or a.reason.search(record.reason))
            for a in allowlist
        )
        if not accepted:
            return False
    return True


@settings(PROPERTY_SETTINGS, max_examples=400)
@given(run=runs())
def test_the_check_agrees_with_a_model_of_its_rule(run):
    collected, records, allowlist, mode, data = run
    result = checker.check(collected, records, allowlist, mode, data)
    assert (not result.problems) == model_passes(*run), result.problems


@PROPERTY_SETTINGS
@given(ids=st.lists(nodeids, min_size=1, max_size=20, unique=True), data=st.data())
def test_any_single_fault_turns_a_clean_run_red(conftest, ids, data):
    shards = data.draw(st.integers(1, 4))
    clean = [
        [checker.Record(i, "passed") for i in ids if conftest.shard_of(i, shards) == k]
        for k in range(1, shards + 1)
    ]
    assert checker.check(ids, clean).problems == []

    victim = data.draw(st.sampled_from(ids))
    home = conftest.shard_of(victim, shards) - 1
    fault = data.draw(
        st.sampled_from(
            ["missing", "repeated", "uncollected", *OUTCOMES[1:], "collect-failed"]
        )
    )
    faulty = [list(cases) for cases in clean]
    collected = ids
    if fault == "missing":
        faulty[home].remove(checker.Record(victim, "passed"))
    elif fault == "repeated":
        faulty[data.draw(st.integers(0, shards - 1))].append(
            checker.Record(victim, "passed")
        )
    elif fault == "uncollected":
        collected = [i for i in ids if i != victim]
    elif fault == "collect-failed":
        faulty[0].append(checker.Record("broken_module.py", "collect-failed"))
    else:
        position = faulty[home].index(checker.Record(victim, "passed"))
        faulty[home][position] = checker.Record(victim, fault, "why")
    result = checker.check(collected, faulty)
    assert result.problems, fault
    if fault not in {"collect-failed", "uncollected"}:
        assert any(victim in line for _, lines in result.problems for line in lines)


# Invariant 6: the allowlist.


def allowlist_entry(**fields):
    entry = {"nodeid": "a.py::t", "outcome": "skipped", "why": "because"}
    entry.update(fields)
    lines = ["[[allow]]"]
    for key, value in entry.items():
        if value is not None:
            lines.append(f"{key} = {json.dumps(value)}")
    return "\n".join(lines) + "\n"


@pytest.mark.parametrize(
    "fields",
    [
        {"outcome": "failed"},
        {"outcome": "incomplete"},
        {"outcome": "collect-failed"},
        {"outcome": "passed"},
        {"why": ""},
        {"why": "   "},
        {"why": None},
        {"nodeid": ""},
        {"reason": "("},
        {"modes": ["installed"]},
        {"modes": []},
        {"data": ["maybe"]},
        {"unexpected": 1},
    ],
)
def test_the_allowlist_rejects_invalid_entries(fields):
    with pytest.raises(checker.ShardCheckError):
        checker.read_allowlist(allowlist_entry(**fields))


def test_the_allowlist_rejects_unknown_tables():
    with pytest.raises(checker.ShardCheckError):
        checker.read_allowlist('[[accept]]\nnodeid = "a"\n')


@PROPERTY_SETTINGS
@given(
    outcome=st.sampled_from(["failed", "incomplete", "collect-failed"]),
    mode=modes,
    data=datas,
)
def test_no_allowlist_entry_accepts_a_failure(outcome, mode, data):
    allowlist = [
        checker.Allowance(nodeid="*", outcome=allowed, why="everything")
        for allowed in sorted(checker.ALLOWABLE_OUTCOMES)
    ]
    records = [[checker.Record("a.py::t", outcome, "x")]]
    collected = [] if outcome == "collect-failed" else ["a.py::t"]
    if outcome == "collect-failed":
        records[0][0] = checker.Record("a.py", outcome)
    assert checker.check(collected, records, allowlist, mode, data).problems


def test_an_unused_entry_is_a_warning_not_a_failure():
    allowlist = checker.read_allowlist(
        allowlist_entry(nodeid="gone.py::t")
        + allowlist_entry(nodeid="a.py::t", modes=["wheel"])
    )
    result = checker.check(
        ["a.py::t"], [[checker.Record("a.py::t", "passed")]], allowlist, "source"
    )
    assert result.problems == []
    # Only entries that apply to this mode count as unused.
    [(title, lines)] = result.warnings
    assert lines == ["skipped gone.py::t"]


def test_a_skip_is_accepted_only_in_the_mode_and_data_its_entry_names():
    allowlist = checker.read_allowlist(
        allowlist_entry(
            nodeid="policyengine_uk/tests/*",
            reason="^Requires",
            data=["absent"],
        )
    )
    record = checker.Record(
        "policyengine_uk/tests/test_x.py::t", "skipped", "Requires X"
    )
    collected = [record.nodeid]
    assert (
        checker.check(collected, [[record]], allowlist, "source", "absent").problems
        == []
    )
    assert checker.check(collected, [[record]], allowlist, "source", "present").problems
    other = checker.Record(record.nodeid, "skipped", "something else")
    assert checker.check(collected, [[other]], allowlist, "source", "absent").problems


# Invariants 7 and 8: real pytest runs.

SAMPLE_SUITE = """
import pytest


@pytest.mark.parametrize("value", range(30))
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

    @pytest.mark.skip(reason="sample skip")
    def test_skipped(self):
        raise AssertionError

    @pytest.mark.xfail(strict=True, reason="sample bug #1")
    def test_expected_failure(self):
        raise AssertionError

    @pytest.mark.xfail(strict=False, reason="sample stale marker")
    def test_unexpected_pass(self):
        pass


def test_skips_itself():
    pytest.skip("sample runtime skip")
"""

SKIPPED_MODULE = """
import pytest

pytest.skip("sample skipped module", allow_module_level=True)


def test_never_runs():
    raise AssertionError
"""

FAILING_SUITE = """
import pytest


@pytest.fixture
def broken_setup():
    raise RuntimeError("setup fails")


@pytest.fixture
def broken_teardown():
    yield
    raise RuntimeError("teardown fails")


def test_fails():
    assert 1 == 2


def test_setup_errors(broken_setup):
    pass


def test_teardown_errors(broken_teardown):
    pass


@pytest.mark.xfail(strict=True, reason="strict")
def test_strict_unexpected_pass():
    pass


def test_passes():
    pass
"""

SAMPLE_ALLOWLIST = """
[[allow]]
nodeid = "suite/test_sample.py::TestGroup::test_skipped"
outcome = "skipped"
why = "sample"

[[allow]]
nodeid = "suite/test_sample.py::TestGroup::test_expected_failure"
outcome = "xfailed"
reason = "#1"
why = "sample"

[[allow]]
nodeid = "suite/test_sample.py::TestGroup::test_unexpected_pass"
outcome = "xpassed"
why = "sample"

[[allow]]
nodeid = "suite/test_sample.py::test_skips_itself"
outcome = "skipped"
reason = "runtime skip"
why = "sample"

[[allow]]
nodeid = "suite/test_skipped_module.py"
outcome = "collect-skipped"
why = "sample"
"""


def _pytest(cwd, *args):
    # A clean run of pytest: no options, plugins or coverage settings carried
    # over from the session that runs this test, and the outcome log plugin
    # importable as CI makes it.
    env = {
        name: value
        for name, value in os.environ.items()
        if not name.startswith(("PYTEST_", "COV_CORE_", "COVERAGE_"))
    }
    env["PYTHONPATH"] = str(GITHUB_DIR)
    return subprocess.run(
        [sys.executable, "-m", "pytest", "-p", "no:cacheprovider", *args],
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        timeout=600,
    )


def _suite(tmp_path, **modules):
    suite = tmp_path / "suite"
    suite.mkdir()
    # The suite's real conftest.py, so this runs the --shard CI uses.
    (suite / "conftest.py").write_text(
        (TESTS_DIR / "conftest.py").read_text(encoding="utf-8"), encoding="utf-8"
    )
    for name, source in modules.items():
        (suite / f"{name}.py").write_text(source, encoding="utf-8")
    return suite


def _run_shards(tmp_path, shards, *extra):
    logs = []
    for shard in range(1, shards + 1):
        logs.append(tmp_path / f"outcomes-{shard}.jsonl")
        _pytest(
            tmp_path,
            "suite",
            "--shard",
            f"{shard}/{shards}",
            "-p",
            "pytest_outcome_log",
            f"--outcome-log={logs[-1]}",
            *extra,
        )
    return logs


def _records(path):
    return sorted(
        (r.nodeid, r.outcome, r.reason)
        for r in checker.read_outcomes(path.read_text(encoding="utf-8"))
    )


def test_the_outcome_log_records_what_pytest_did(tmp_path):
    _suite(tmp_path, test_failing=FAILING_SUITE, test_skipped_module=SKIPPED_MODULE)
    serial, parallel = tmp_path / "serial.jsonl", tmp_path / "parallel.jsonl"
    _pytest(tmp_path, "suite", "-p", "pytest_outcome_log", f"--outcome-log={serial}")
    _pytest(
        tmp_path,
        "suite",
        "-p",
        "pytest_outcome_log",
        f"--outcome-log={parallel}",
        "-n",
        "2",
    )
    expected = sorted(
        [
            ("suite/test_failing.py::test_fails", "failed", ""),
            ("suite/test_failing.py::test_setup_errors", "failed", ""),
            ("suite/test_failing.py::test_teardown_errors", "failed", ""),
            ("suite/test_failing.py::test_strict_unexpected_pass", "failed", ""),
            ("suite/test_failing.py::test_passes", "passed", ""),
            (
                "suite/test_skipped_module.py",
                "collect-skipped",
                "sample skipped module",
            ),
        ]
    )
    assert _records(serial) == expected
    # The same with pytest-xdist, where the controller writes the log.
    assert _records(parallel) == expected


SUBTEST_SUITE = """
import pytest


def test_with_subtests(subtests):
    with subtests.test("skipped part"):
        pytest.skip("sample subtest skip")
    with subtests.test("passing part"):
        pass
"""


def test_a_skipped_subtest_is_not_hidden_by_its_tests_pass(tmp_path):
    # pytest 9's subtests report a skipped subtest before the test's own
    # passing call; the log must keep the skip so the check sees it.
    _suite(tmp_path, test_subtests=SUBTEST_SUITE)
    log = tmp_path / "outcomes.jsonl"
    _pytest(tmp_path, "suite", "-p", "pytest_outcome_log", f"--outcome-log={log}")
    assert _records(log) == [
        (
            "suite/test_subtests.py::test_with_subtests",
            "skipped",
            "sample subtest skip",
        )
    ]


@pytest.mark.parametrize("xdist", [(), ("-n", "2", "--dist", "worksteal")])
def test_real_pytest_shards_pass_the_check_only_when_allowed(tmp_path, xdist):
    _suite(tmp_path, test_sample=SAMPLE_SUITE, test_skipped_module=SKIPPED_MODULE)
    listing = _pytest(tmp_path, "suite", "--collect-only", "-q")
    assert listing.returncode == 0, listing.stdout + listing.stderr
    collected = tmp_path / "collected.txt"
    collected.write_text(listing.stdout, encoding="utf-8")
    assert len(checker.read_collected(listing.stdout)) == 43

    logs = _run_shards(tmp_path, 3, *xdist)
    sizes = [
        sum(not r.is_collector for r in checker.read_outcomes(log.read_text()))
        for log in logs
    ]
    assert sum(sizes) == 43 and all(sizes)
    allowlist = tmp_path / "allow.toml"
    allowlist.write_text(SAMPLE_ALLOWLIST, encoding="utf-8")

    def check(*paths, allow=allowlist):
        args = ["--collected", str(collected), "--outcomes", *map(str, paths)]
        if allow is not None:
            args += ["--allowlist", str(allow)]
        return checker.main(args)

    assert check(*logs) == 0
    # Without the allowlist, the skips, xfail, XPASS and skipped module fail.
    assert check(*logs, allow=None) == 1
    assert check(*logs[:-1]) == 1
    assert check(*logs, logs[0]) == 1
    assert check(tmp_path / "absent.jsonl") == 2


def test_real_pytest_failures_fail_the_check(tmp_path, capsys):
    _suite(tmp_path, test_failing=FAILING_SUITE)
    listing = _pytest(tmp_path, "suite", "--collect-only", "-q")
    collected = tmp_path / "collected.txt"
    collected.write_text(listing.stdout, encoding="utf-8")
    logs = _run_shards(tmp_path, 2)
    assert (
        checker.main(["--collected", str(collected), "--outcomes", *map(str, logs)])
        == 1
    )
    report = capsys.readouterr().out
    for name in (
        "test_fails",
        "test_setup_errors",
        "test_teardown_errors",
        "test_strict_unexpected_pass",
    ):
        assert f"suite/test_failing.py::{name}" in report
    assert "4 tests failed" in report


# Invariant 9: the checked-in allowlist.


def test_the_checked_in_allowlist_names_tests_that_exist():
    allowlist = checker.read_allowlist(ALLOWLIST.read_text(encoding="utf-8"))
    assert allowlist
    for entry in allowlist:
        if any(char in entry.nodeid for char in "*?["):
            continue
        path, _, rest = entry.nodeid.partition("::")
        file = REPO_ROOT / path
        assert file.exists(), entry.nodeid
        if not rest:
            continue
        names = rest.split("::")
        tree = ast.parse(file.read_text(encoding="utf-8"))
        scope = tree.body
        for name in names[:-1]:
            [cls] = [n for n in scope if isinstance(n, ast.ClassDef) and n.name == name]
            scope = cls.body
        functions = {
            n.name
            for n in scope
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
        }
        assert names[-1].split("[")[0] in functions, entry.nodeid


# Invariant 10: every pull request reports "Test / Result".


def test_every_pull_request_reports_the_test_result():
    import yaml

    workflows = GITHUB_DIR / "workflows"

    def load(name):
        document = yaml.safe_load((workflows / name).read_text(encoding="utf-8"))
        # PyYAML reads the key "on" as True.
        return document, document.get("on", document.get(True))

    pull_request, triggers = load("pr_code_changes.yaml")
    assert triggers["pull_request"] == {"branches": ["main"]}
    # A merge queue's groups get the same checks.
    assert "merge_group" in triggers
    main, main_triggers = load("code_changes.yaml")
    # Every commit that lands on main finishes its run: nothing cancels it.
    assert "concurrency" not in main
    code_paths = pull_request["jobs"]["Changes"]["steps"][1]["env"]["CODE_PATHS"]
    assert code_paths.split() == main_triggers["push"]["paths"]
    # Lint runs on every pull request: ruff also checks docs/ and scripts/.
    assert "if" not in pull_request["jobs"]["Lint"]
    # The suite is always called, and skips only when no code changed.
    test = pull_request["jobs"]["Test"]
    assert test["uses"] == "./.github/workflows/test-suite.yaml"
    assert "if" not in test
    assert test["with"]["skip"] == "${{ needs.Changes.outputs.code == 'false' }}"
    # Merge groups must run the microsimulation tests; so must main.
    assert test["with"]["require-data"] == "${{ github.event_name == 'merge_group' }}"
    assert main["jobs"]["Test"]["with"]["require-data"] is True
    release, _ = load("versioning.yaml")
    assert release["jobs"]["Test"]["with"]["require-data"] is True
    # A manual dispatch of the main workflow always tests.
    lookup = main["jobs"]["Tested"]["steps"][0]["run"]
    assert '"$GITHUB_EVENT_NAME" != push' in lookup
    assert "event=merge_group&status=success" in lookup


# Invariant 11: deciding whether a pull request changes code.

_changed_spec = importlib.util.spec_from_file_location(
    "changed_code", GITHUB_DIR / "changed_code.py"
)
changed_code = importlib.util.module_from_spec(_changed_spec)
_changed_spec.loader.exec_module(changed_code)
CODE_PATHS = [
    "policyengine_uk/**",
    "tests/**",
    ".github/**",
    "pyproject.toml",
    "uv.lock",
    "Makefile",
    "conftest.py",
    ".gitignore",
    "README.md",
]
_segment = st.from_regex(r"[A-Za-z0-9_.é -]{1,8}", fullmatch=True).filter(
    lambda s: s not in {".", ".."}
)
paths = st.lists(_segment, min_size=1, max_size=4).map("/".join)


def reference_is_code(path):
    # fnmatch-free statement of a workflow paths filter for these patterns.
    top, _, rest = path.partition("/")
    return (bool(rest) and top in {"policyengine_uk", "tests", ".github"}) or (
        path
        in {
            "pyproject.toml",
            "uv.lock",
            "Makefile",
            "conftest.py",
            ".gitignore",
            "README.md",
        }
    )


@PROPERTY_SETTINGS
@given(
    changed=st.lists(
        paths
        | st.sampled_from(
            [
                "policyengine_uk/x.py",
                "docs/a.md",
                "changelog.d/1.fixed.md",
                "Makefile",
                "Makefile.bak",
                "policyengine_uk",
                "policyengine_uk_other/x.py",
                ".github/workflows/a.yaml",
                "docs/pyproject.toml",
            ]
        ),
        max_size=6,
    )
)
def test_changed_code_matches_a_paths_filter(changed):
    expected = not changed or any(reference_is_code(p) for p in changed)
    assert changed_code.changes_code(changed, CODE_PATHS) == expected


def test_changed_code_reads_nul_separated_unquoted_paths(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("CODE_PATHS", "\n".join(CODE_PATHS))
    listing = tmp_path / "changed"
    listing.write_text("docs/caf\u00e9 notes.md\0scripts/run.sh\0", encoding="utf-8")
    assert changed_code.main([str(listing)]) == 0
    assert capsys.readouterr().out.strip() == "code=false"
    listing.write_text("docs/a.md\0policyengine_uk/caf\u00e9.py\0", encoding="utf-8")
    assert changed_code.main([str(listing)]) == 0
    assert capsys.readouterr().out.strip() == "code=true"
    listing.write_text("", encoding="utf-8")
    assert changed_code.main([str(listing)]) == 0
    assert capsys.readouterr().out.strip() == "code=true"
    monkeypatch.setenv("CODE_PATHS", "policyengine_uk/*.py")
    assert changed_code.main([str(listing)]) == 2


def test_the_release_tells_policyengine_py_only_after_pypi_has_it():
    # The dispatch to policyengine.py comes after PyPI serves exactly the
    # tested files, names the version, and can never fail the release.
    import yaml

    workflow = yaml.safe_load(
        (GITHUB_DIR / "workflows" / "versioning.yaml").read_text(encoding="utf-8")
    )
    publish = workflow["jobs"]["Publish"]
    assert publish["environment"] == "pypi"
    names = [step["name"] for step in publish["steps"]]
    confirm = names.index("Check PyPI serves exactly these files")
    token = names.index("Generate a token for policyengine.py")
    dispatch = names.index("Tell policyengine.py the release is on PyPI")
    tag = names.index("Tag the version commit")
    assert confirm < token < dispatch < tag
    # The tag step runs whatever happened to the dispatch: no condition of its
    # own, so only the implicit success(), which continue-on-error keeps true.
    assert "if" not in publish["steps"][tag]
    assert "continue-on-error" not in publish["steps"][tag]
    for index in (token, dispatch):
        assert publish["steps"][index]["continue-on-error"] is True
        # A hung step must not use up the job before the tag step runs.
        assert publish["steps"][index]["timeout-minutes"] <= 5
    token_inputs = publish["steps"][token]["with"]
    assert token_inputs["repositories"] == "policyengine.py"
    assert token_inputs["permission-contents"] == "write"
    assert publish["steps"][dispatch]["if"] == (
        "steps.dispatch-token.outcome == 'success'"
    )
    run = publish["steps"][dispatch]["run"]
    assert "repos/PolicyEngine/policyengine.py/dispatches" in run
    assert "event_type=policyengine-uk-release" in run
    assert "client_payload[version]=$VERSION" in run


@pytest.mark.parametrize("dist_artifact", ["", "release-dist"])
def test_configured_source_and_wheel_shards_account_for_every_node(
    conftest, dist_artifact
):
    """The two configured runner budgets retain the same strict coverage audit."""
    import yaml

    workflow = yaml.safe_load(
        (GITHUB_DIR / "workflows" / "test-suite.yaml").read_text()
    )
    matrix = workflow["jobs"]["Python"]["strategy"]["matrix"]["shard"]

    # The shared matrix is the runner set for both source and wheel; N is
    # derived from the actual configured jobs, never a second fixed count.
    selected = matrix
    assert isinstance(selected, list) and selected
    assert selected == list(range(1, len(selected) + 1))
    collected = [f"tests/public_synthetic.py::test_case[{i}]" for i in range(200)]
    shards = [
        [
            checker.Record(nodeid, "passed")
            for nodeid in collected
            if conftest.shard_of(nodeid, len(selected)) == number
        ]
        for number in selected
    ]
    mode = "wheel" if dist_artifact else "source"
    assert checker.check(collected, shards, mode=mode, data="present").problems == []
    populated = next(cases for cases in shards if cases)
    missing = [cases for cases in shards if cases is not populated]
    assert checker.check(collected, missing, mode=mode, data="present").problems
    assert checker.check(
        collected, [*shards, populated], mode=mode, data="present"
    ).problems
