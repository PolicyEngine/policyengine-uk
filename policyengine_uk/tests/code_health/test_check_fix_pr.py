"""Fix PRs carry executable, named evidence of the bug they fix.

The check runs without installing the model. These tests hold its rules to
the invariants reviewers rely on:

1. Exactly an added or modified fixed fragment, or a bug/bug-fix label,
   classifies a PR as a fix.
2. Deleted tests never count as changed executable tests or reproducers.
3. Formatting reproducer ids with supported separators and quoting round
   trips through the body parser.
4. A pytest reproducer resolves exactly when its changed file defines the
   named function or class method, ignoring parametrisation suffixes.
5. An n/a reason is accepted exactly when it is non-empty and no model
   source outside the test tree was added, modified or deleted.
6. Non-fix PRs pass regardless of their bodies.
7. The CLI returns 0/1/2 for passing/failing/unusable input and appends its
   Markdown report without replacing an existing job summary.
8. Real git diffs and script subprocesses obey the same rules for passing
   and failing fix PRs.
9. The workflow reports the check on pull requests and on merge queue
   groups, so a branch rule can require it with a merge queue.
"""

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest
from hypothesis import HealthCheck, example, given, settings
from hypothesis import strategies as st

TESTS_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = TESTS_DIR.parents[1]
CHECKER = REPO_ROOT / ".github" / "check_fix_pr.py"

if not CHECKER.exists():
    pytest.skip(
        "the .github folder is not part of an installed package",
        allow_module_level=True,
    )

_spec = importlib.util.spec_from_file_location("check_fix_pr", CHECKER)
checker = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = checker
_spec.loader.exec_module(checker)

PROPERTY_SETTINGS = settings(
    max_examples=20,
    deadline=None,
    derandomize=True,
    # Cold imports can be charged to input generation on busy runners.
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow],
)

_identifier = st.from_regex(r"[A-Za-z_][A-Za-z0-9_]{0,10}", fullmatch=True)
_status = st.sampled_from(list("ABCDEFGHIJKLMNOPQRSTUVWXYZ"))
_label = st.one_of(
    st.sampled_from(
        ["bug", "bug-fix", "Bug", "bugfix", "enhancement", "documentation"]
    ),
    st.text(alphabet="abcdefghijklmnopqrstuvwxyz-_", max_size=20),
)
_change_path = st.one_of(
    _identifier.map(lambda name: f"changelog.d/{name}.fixed.md"),
    st.sampled_from(
        [
            "changelog.d/regression.added.md",
            "changelog.d/regression.changed.md",
            "docs/regression.fixed.md",
            "policyengine_uk/variables/regression.py",
            "policyengine_uk/parameters/regression.yaml",
            "policyengine_uk/__init__.py",
            "policyengine_uk/tests/test_regression.py",
            "policyengine_uk/tests/policy/regression.yaml",
            "policyengine_uk/tests2/test_regression.py",
            ".github/workflows/check.yaml",
            "docs/regression.md",
        ]
    ),
)
_changes = st.lists(st.tuples(_status, _change_path), max_size=12)
_python_path = _identifier.map(
    lambda name: f"policyengine_uk/tests/code_health/test_{name}.py"
)
_yaml_path = st.builds(
    lambda name, extension: f"policyengine_uk/tests/policy/{name}.{extension}",
    _identifier,
    st.sampled_from(["yaml", "yml"]),
)
_executable_path = st.one_of(_python_path, _yaml_path)
_params = st.one_of(
    st.just(""),
    st.text(alphabet="abc012 ::/-,;", max_size=15).map(lambda value: f"[{value}]"),
)
_valid_id = st.one_of(
    st.builds(
        lambda path, name, params: f"{path}::test_{name}{params}",
        _python_path,
        _identifier,
        _params,
    ),
    st.builds(
        lambda path, name, params: f"{path}::TestRegression::test_{name}{params}",
        _python_path,
        _identifier,
        _params,
    ),
    _yaml_path,
    st.builds(lambda path, name: f"{path}::{name}", _yaml_path, _identifier),
    st.builds(
        lambda prefix, reason: prefix + reason,
        st.sampled_from(["n/a: ", "n/a - ", "none: "]),
        _identifier,
    ),
)


def _write(repo_root, path, text):
    destination = repo_root / path
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(text, encoding="utf-8")
    return destination


def _report(repo_root, body, changes, labels=("bug",)):
    return checker.check_fix_pr(
        "Fix a regression", body, list(labels), changes, repo_root
    )


@PROPERTY_SETTINGS
@given(labels=st.sets(_label, max_size=10), changes=_changes)
def test_classification_matches_only_fragments_and_labels(labels, changes):
    expected = bool({"bug", "bug-fix"} & labels) or any(
        status in {"A", "M"}
        and path.startswith("changelog.d/")
        and path.endswith(".fixed.md")
        for status, path in changes
    )
    for title, body in [("Fix a regression", "Reproducer: missing"), ("", "")]:
        assert checker.classify_fix_pr(title, body, list(labels), changes) is expected


@PROPERTY_SETTINGS
@given(paths=st.lists(_executable_path, min_size=1, max_size=6, unique=True))
def test_deleted_tests_never_count_as_executable_or_reproducers(tmp_path, paths):
    changes = [("D", path) for path in paths]
    assert checker.changed_executable_tests(changes) == []

    path = paths[0]
    content = (
        "def test_regression():\n    pass\n"
        if path.endswith(".py")
        else "- name: regression\n"
    )
    _write(tmp_path, path, content)
    # A separate changed test isolates reproducer eligibility from the
    # requirement that the PR change some executable test.
    companion = "policyengine_uk/tests/test_companion.py"
    _write(tmp_path, companion, "def test_companion():\n    pass\n")
    target = path + ("::test_regression" if path.endswith(".py") else "")
    assert not _report(
        tmp_path, f"Reproducer: {target}", changes + [("A", companion)]
    ).passed


@PROPERTY_SETTINGS
@given(ids=st.lists(_valid_id, max_size=8), data=st.data())
def test_reproducer_line_round_trips_supported_formatting(ids, data):
    pieces = []
    for index, nodeid in enumerate(ids):
        if index:
            pieces.append(data.draw(st.sampled_from([",", ";", ", ", " ; ", "\t;\t"])))
        spaces = data.draw(st.sampled_from(["", " ", "\t", "  "]))
        quoted = data.draw(st.booleans())
        pieces.append(spaces + (f"`{nodeid}`" if quoted else nodeid) + spaces)
    key = data.draw(
        st.sampled_from(["Reproducer", "reproducer", "REPRODUCER", "RePrOdUcEr"])
    )
    body = "A description.\n" + key + ": " + "".join(pieces) + "\nA test plan."
    assert checker.parse_reproducers(body) == ids


@PROPERTY_SETTINGS
@given(
    status=_status,
    name=_identifier,
    defines_name=st.booleans(),
    in_class=st.booleans(),
    asynchronous=st.booleans(),
    params=_params,
)
@example(
    status="A",
    name="case",
    defines_name=True,
    in_class=True,
    asynchronous=False,
    params="[a::b]",
)
@example(
    status="M",
    name="case",
    defines_name=True,
    in_class=False,
    asynchronous=True,
    params="[2026]",
)
def test_pytest_reproducer_requires_changed_file_and_definition(
    tmp_path, status, name, defines_name, in_class, asynchronous, params
):
    path = "policyengine_uk/tests/test_regression.py"
    wanted = f"test_{name}"
    defined = wanted if defines_name else f"test_other_{name}"
    prefix = "async " if asynchronous else ""
    if in_class:
        source = (
            f"class TestRegression:\n    {prefix}def {defined}(self):\n        pass\n"
        )
        nodeid = f"{path}::TestRegression::{wanted}{params}"
    else:
        source = f"{prefix}def {defined}():\n    pass\n"
        nodeid = f"{path}::{wanted}{params}"
    _write(tmp_path, path, source)

    report = _report(tmp_path, f"Reproducer: {nodeid}", [(status, path)])
    assert report.passed is (status in {"A", "M"} and defines_name)


@PROPERTY_SETTINGS
@given(
    changes=_changes,
    reason=st.one_of(st.sampled_from(["", " ", "\t"]), _identifier),
    prefix=st.sampled_from(["n/a: ", "n/a - ", "none: "]),
)
@example(
    changes=[("D", "policyengine_uk/variables/regression.py")],
    reason="CI only",
    prefix="n/a: ",
)
@example(
    changes=[("M", "policyengine_uk/tests2/test_regression.py")],
    reason="CI only",
    prefix="none: ",
)
def test_na_requires_reason_and_no_model_source_changes(
    tmp_path, changes, reason, prefix
):
    has_model_source = any(
        status in {"A", "M", "D"}
        and path.startswith("policyengine_uk/")
        and not path.startswith("policyengine_uk/tests/")
        for status, path in changes
    )
    report = _report(tmp_path, f"Reproducer: {prefix}{reason}", changes)
    assert report.passed is (bool(reason.strip()) and not has_model_source)


@PROPERTY_SETTINGS
@given(title=st.text(max_size=80), body=st.text(max_size=300), changes=_changes)
@example(
    title="Fix the model",
    body="Reproducer: n/a:\nReproducer: missing::test_x",
    changes=[],
)
def test_non_fix_pr_always_passes(tmp_path, title, body, changes):
    non_fix_changes = [
        (status, path)
        for status, path in changes
        if not (status in {"A", "M"} and path.endswith(".fixed.md"))
    ]
    report = checker.check_fix_pr(
        title, body, ["enhancement", "Bug"], non_fix_changes, tmp_path
    )
    assert not report.is_fix
    assert report.passed
    assert report.title == title
    assert len(report.messages) == 1


@pytest.mark.parametrize(
    "path, executable",
    [
        ("policyengine_uk/tests/test_regression.py", True),
        ("policyengine_uk/tests/code_health/regression_test.py", True),
        ("policyengine_uk/tests/policy/regression.yaml", True),
        ("policyengine_uk/tests/policy/regression.yml", True),
        ("policyengine_uk/tests/conftest.py", False),
        ("policyengine_uk/tests/__init__.py", False),
        ("policyengine_uk/tests/helpers.py", False),
        ("policyengine_uk/tests/gov/regression.yaml", False),
        ("policyengine_uk/tests/policy2/regression.yaml", False),
        ("tests/test_regression.py", False),
        ("policyengine_uk/variables/test_regression.py", False),
    ],
)
def test_only_collected_test_paths_are_executable(path, executable):
    for status in ["A", "M", "D", "T", "U"]:
        assert checker.changed_executable_tests([(status, path)]) == (
            [path] if executable and status in {"A", "M"} else []
        )


@pytest.mark.parametrize(
    "source",
    [
        "- name: Regression case\n  period: 2026\n",
        "name: Regression case\nperiod: 2026\n",
        "- name: 'Regression case'\n",
        '- name: "Regression case"\n',
        "- period: 2026\n  name: Regression case\n",
        "- name: Regression case # An inline comment\n",
    ],
)
@pytest.mark.parametrize("extension", ["yaml", "yml"])
def test_yaml_reproducer_accepts_bare_files_and_named_entries(
    tmp_path, source, extension
):
    path = f"policyengine_uk/tests/policy/regression.{extension}"
    _write(tmp_path, path, source)
    changes = [("M", path)]
    assert _report(tmp_path, f"Reproducer: {path}", changes).passed
    assert _report(tmp_path, f"Reproducer: {path}::Regression case", changes).passed
    assert not _report(tmp_path, f"Reproducer: {path}::Different case", changes).passed


@pytest.mark.parametrize(
    "source, name",
    [
        ("- name: 'It''s a case' # Comment\n", "It's a case"),
        ('- name: "A \\"quoted\\" # case" # Comment\n', 'A "quoted" # case'),
        ('- name: "Case, with; punctuation"\n', "Case, with; punctuation"),
        ('- name: "Regression\\x20case"\n', "Regression case"),
        ('- name: "\\U00000041"\n', "A"),
        ('- name: "\\\\x41"\n', "\\x41"),
    ],
)
def test_quoted_yaml_names_resolve_without_treating_punctuation_as_ids(
    tmp_path, source, name
):
    path = "policyengine_uk/tests/policy/regression.yaml"
    _write(tmp_path, path, source)
    assert _report(tmp_path, f"Reproducer: `{path}::{name}`", [("A", path)]).passed


def test_nested_yaml_name_is_not_a_test_entry(tmp_path):
    path = "policyengine_uk/tests/policy/regression.yaml"
    _write(tmp_path, path, "- name: Regression case\n  input:\n    name: Impostor\n")
    changes = [("M", path)]
    assert _report(tmp_path, f"Reproducer: {path}::Regression case", changes).passed
    assert not _report(tmp_path, f"Reproducer: {path}::Impostor", changes).passed


def test_backticked_na_reason_can_include_commas_and_semicolons(tmp_path):
    assert _report(tmp_path, "Reproducer: `n/a: CI, docs; no model source`", []).passed


@pytest.mark.parametrize(
    "source, suffix",
    [
        ("def test_regression():\n    pass\n", ""),
        ("def test_regression():\n    pass\n", "::test_regression[unterminated"),
        ("def test_regression():\n    pass\n", "::test_regression[p]::junk"),
        ("def test_regression(:\n    pass\n", "::test_regression"),
        ("test_regression = True\n", "::test_regression"),
        (
            "def wrapper():\n    def test_regression():\n        pass\n",
            "::test_regression",
        ),
        (
            "class TestOther:\n    def test_regression(self):\n        pass\n",
            "::TestRegression::test_regression",
        ),
        (
            "class TestRegression:\n    def test_regression(self):\n        pass\n",
            "::TestRegression::Nested::test_regression",
        ),
    ],
)
def test_pytest_reproducer_rejects_bare_paths_and_nonexistent_definitions(
    tmp_path, source, suffix
):
    path = "policyengine_uk/tests/test_regression.py"
    _write(tmp_path, path, source)
    assert not _report(tmp_path, f"Reproducer: {path}{suffix}", [("M", path)]).passed


def test_reproducer_file_must_exist_at_pr_head(tmp_path):
    path = "policyengine_uk/tests/test_regression.py"
    assert not _report(
        tmp_path, f"Reproducer: {path}::test_regression", [("A", path)]
    ).passed


@pytest.mark.parametrize("outside_checkout", [True, False])
def test_reproducer_symlinks_cannot_escape_checkout_or_crash_on_loops(
    tmp_path, outside_checkout
):
    repo_root = tmp_path / "checkout"
    path = "policyengine_uk/tests/test_regression.py"
    destination = repo_root / path
    destination.parent.mkdir(parents=True)
    if outside_checkout:
        target = _write(tmp_path, "outside.py", "def test_regression():\n    pass\n")
    else:
        target = destination
    destination.symlink_to(target)
    assert not _report(
        repo_root, f"Reproducer: {path}::test_regression", [("A", path)]
    ).passed


def test_every_reproducer_on_every_line_must_resolve(tmp_path):
    path = "policyengine_uk/tests/test_regression.py"
    _write(tmp_path, path, "def test_one():\n    pass\n\ndef test_two():\n    pass\n")
    changes = [("M", path)]
    body = f"Reproducer: `{path}::test_one`\nreproducer: {path}::test_two"
    assert _report(tmp_path, body, changes).passed
    assert not _report(tmp_path, body + f"; {path}::test_missing", changes).passed
    assert not _report(tmp_path, "Reproducer: n/a: CI only; missing", []).passed


def test_report_explains_each_failed_requirement(tmp_path):
    report = _report(tmp_path, "A description without evidence.", [])
    assert not report.passed
    assert len(report.messages) >= 2
    assert sum("Reproducer:" in message for message in report.messages) >= 2


def _arguments(
    input_dir,
    repo_root,
    *,
    body="Reproducer: n/a: CI only",
    labels="bug\n",
    changes="",
    summary=None,
):
    values = {
        "title": "Fix a regression",
        "body": body,
        "labels": labels,
        "changes": changes,
    }
    args = []
    for name, value in values.items():
        path = _write(input_dir, f"{name}.txt", value)
        args.extend([f"--{name}-file", str(path)])
    args.extend(["--repo-root", str(repo_root)])
    if summary is not None:
        args.extend(["--summary-file", str(summary)])
    return args


@pytest.mark.parametrize(
    "body, labels, changes, expected",
    [
        ("Reproducer: n/a: CI only", "bug\n", "M\t.github/workflows/check.yaml\n", 0),
        (
            "Reproducer: policyengine_uk/tests/test_regression.py::test_regression",
            "bug-fix\n",
            "M\tpolicyengine_uk/tests/test_regression.py\n",
            0,
        ),
        ("No evidence.", "bug\n", "M\tpolicyengine_uk/variables/regression.py\n", 1),
        (
            "Reproducer: invalid",
            "enhancement\n",
            "D\tchangelog.d/regression.fixed.md\n",
            0,
        ),
        (
            "Reproducer: n/a: CI only",
            "bug\n",
            "T\t.github/workflows/check.yaml\nQ\tdocs/regression.md\n",
            0,
        ),
    ],
)
def test_main_returns_zero_or_one_for_usable_inputs(
    tmp_path, capsys, body, labels, changes, expected
):
    _write(
        tmp_path,
        "policyengine_uk/tests/test_regression.py",
        "def test_regression():\n    pass\n",
    )
    args = _arguments(tmp_path, tmp_path, body=body, labels=labels, changes=changes)
    assert checker.main(args) == expected
    assert "Fix a regression" in capsys.readouterr().out


@pytest.mark.parametrize("missing", ["title", "body", "labels", "changes"])
def test_main_returns_two_for_missing_input_files(tmp_path, capsys, missing):
    args = _arguments(tmp_path, tmp_path)
    (tmp_path / f"{missing}.txt").unlink()
    assert checker.main(args) == 2
    assert capsys.readouterr().out.strip()


@pytest.mark.parametrize(
    "changes",
    [
        "M path/to/test.py\n",
        "M\t\n",
        "MM\tpath.py\n",
        "R100\told.py\tnew.py\n",
        "M\tfirst.py\tsecond.py\n",
    ],
)
def test_main_returns_two_for_unparseable_changes(tmp_path, capsys, changes):
    args = _arguments(tmp_path, tmp_path, changes=changes)
    assert checker.main(args) == 2
    assert capsys.readouterr().out.strip()


def test_main_returns_two_for_missing_repository_root(tmp_path):
    args = _arguments(tmp_path, tmp_path / "missing")
    assert checker.main(args) == 2


def test_main_returns_two_for_unwritable_summary(tmp_path):
    # A directory is unwritable as a summary file even when tests run as root.
    args = _arguments(tmp_path, tmp_path, summary=tmp_path)
    assert checker.main(args) == 2


def test_main_appends_markdown_to_existing_summary(tmp_path):
    summary = tmp_path / "summary.md"
    summary.write_text("Existing summary.\n", encoding="utf-8")
    args = _arguments(tmp_path, tmp_path, summary=summary)
    assert checker.main(args) == 0
    first = summary.read_text(encoding="utf-8")
    assert first.startswith("Existing summary.\n")
    assert "## Fix evidence" in first

    (tmp_path / "body.txt").write_text("No reproducer.", encoding="utf-8")
    assert checker.main(args) == 1
    second = summary.read_text(encoding="utf-8")
    assert second.startswith(first)
    assert second.count("## Fix evidence") == 2
    assert "Reproducer:" in second

    (tmp_path / "changes.txt").write_text("unparseable", encoding="utf-8")
    assert checker.main(args) == 2
    third = summary.read_text(encoding="utf-8")
    assert third.startswith(second)
    assert third.count("## Fix evidence") == 3
    assert "Unusable input" in third


def _git(repo_root, *args):
    result = subprocess.run(
        [
            "git",
            "-c",
            "user.name=Fix evidence tests",
            "-c",
            "user.email=tests@example.invalid",
            "-c",
            "commit.gpgsign=false",
            "-c",
            "core.hooksPath=/dev/null",
            *args,
        ],
        cwd=repo_root,
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    return result.stdout.strip()


def test_real_git_diff_and_script_subprocess(tmp_path):
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    _git(repo_root, "init", "--initial-branch=fixture")
    python_path = "policyengine_uk/tests/test_regression.py"
    yaml_path = "policyengine_uk/tests/gov/regression.yaml"
    _write(repo_root, python_path, "def test_regression():\n    pass\n")
    _write(repo_root, yaml_path, "- name: Regression\n  period: 2025\n")
    _git(repo_root, "add", ".")
    _git(repo_root, "commit", "-m", "Fixture before the fix")
    base = _git(repo_root, "rev-parse", "HEAD")

    _write(repo_root, python_path, "def test_regression():\n    assert 1 + 1 == 2\n")
    _write(repo_root, yaml_path, "- name: Regression\n  period: 2026\n")
    _write(repo_root, "changelog.d/regression.fixed.md", "- Fixed a regression.\n")
    _git(repo_root, "add", ".")
    _git(repo_root, "commit", "-m", "Fixture fix and its evidence")
    head = _git(repo_root, "rev-parse", "HEAD")
    merge_base = _git(repo_root, "merge-base", base, head)
    changes = (
        _git(repo_root, "diff", "--name-status", "--no-renames", merge_base, head)
        + "\n"
    )
    assert f"M\t{python_path}\n" in changes
    assert f"M\t{yaml_path}\n" in changes
    assert "A\tchangelog.d/regression.fixed.md\n" in changes

    for nodeid, expected in [(f"{python_path}::test_regression", 0), (yaml_path, 1)]:
        args = _arguments(
            tmp_path / "inputs",
            repo_root,
            body=f"Reproducer: {nodeid}",
            labels="",
            changes=changes,
        )
        result = subprocess.run(
            [sys.executable, str(CHECKER), *args],
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=15,
        )
        assert result.returncode == expected, result.stdout + result.stderr
        assert "Fix a regression" in result.stdout
        if expected:
            assert "Reproducer:" in result.stdout


def test_the_workflow_reports_on_pull_requests_and_merge_groups():
    import yaml

    workflow = yaml.safe_load(
        (REPO_ROOT / ".github" / "workflows" / "pr_fix_evidence.yaml").read_text(
            encoding="utf-8"
        )
    )
    # PyYAML reads the key "on" as True.
    triggers = workflow.get("on", workflow.get(True))
    assert set(triggers) == {"pull_request", "merge_group"}
    assert "paths" not in triggers["pull_request"]
    [job] = workflow["jobs"].values()
    assert job["name"] == "Fix evidence"
    assert "if" not in job
