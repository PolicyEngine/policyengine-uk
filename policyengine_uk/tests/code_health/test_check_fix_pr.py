"""Fix PRs carry executable, named evidence of the bug they fix.

The check runs without installing the model. These tests hold its rules to
the invariants reviewers rely on:

1. Exactly an added, modified or type-changed Towncrier fixed fragment,
   or a bug/bug-fix label, classifies a PR as a fix.
2. Deleted tests never count as changed executable tests or reproducers.
3. Formatting reproducer ids with supported separators and quoting round
   trips through the body parser.
4. A pytest reproducer requires a changed file and a directly defined test
   function or class method that pytest collects, checked against real pytest
   collection, ignoring parametrisation suffixes. A collected test marked to
   skip or expected to fail is rejected too, since it reproduces nothing.
5. An n/a reason is accepted exactly when it is non-empty and no model
   source outside the test tree or dependency file was added, modified,
   type-changed or deleted.
6. Non-fix PRs pass regardless of their bodies.
7. The CLI returns 0/1/2 for passing/failing/unusable input and appends its
   Markdown report without replacing an existing job summary.
8. NUL-delimited git diffs preserve literal paths, and git-object reads
   validate committed content without following symlinks or executing PR code.
   The standalone checker entry point obeys the same passing and failing rules.
9. The workflow runs the trusted base checker on pull_request_target events,
   isolates artifacts under RUNNER_TEMP and reports on merge queue groups.
10. YAML reproducers require parsed list entries with a string name and a
    non-empty output mapping; missing PyYAML fails closed.
11. Reproducer lines inside HTML comments never count as evidence.
"""

import importlib.util
import os
import re
import runpy
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
    st.builds(
        lambda name, suffix: f"changelog.d/{name}.{suffix}",
        _identifier,
        st.sampled_from(["fixed.md", "fixed.1.md", "fixed.md.md", "fixed"]),
    ),
    st.sampled_from(
        [
            "changelog.d/regression.added.md",
            "changelog.d/regression.changed.md",
            "changelog.d/fixed.md",
            "changelog.d/nested/regression.fixed.md",
            "docs/regression.fixed.md",
            "policyengine_uk/variables/regression.py",
            "policyengine_uk/parameters/regression.yaml",
            "policyengine_uk/__init__.py",
            "policyengine_uk/tests/test_regression.py",
            "policyengine_uk/tests/policy/regression.yaml",
            "policyengine_uk/tests2/test_regression.py",
            ".github/workflows/check.yaml",
            "docs/regression.md",
            "pyproject.toml",
            "uv.lock",
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


def _report(repo_root, body, changes, labels=("bug",), *, head_sha=None):
    return checker.check_fix_pr(
        "Fix a regression", body, list(labels), changes, repo_root, head_sha=head_sha
    )


def _fixed_fragment(path):
    return (
        Path(path).parent == Path("changelog.d")
        and "fixed" in Path(path).name.split(".")[1:]
    )


@PROPERTY_SETTINGS
@given(labels=st.sets(_label, max_size=10), changes=_changes)
def test_classification_matches_only_fragments_and_labels(labels, changes):
    expected = bool({"bug", "bug-fix"} & labels) or any(
        status in {"A", "M", "T"} and _fixed_fragment(path) for status, path in changes
    )
    for title, body in [("Fix a regression", "Reproducer: missing"), ("", "")]:
        assert checker.classify_fix_pr(title, body, list(labels), changes) is expected


@pytest.mark.parametrize("status", ["A", "M", "T"])
@pytest.mark.parametrize(
    "basename", ["x.fixed.md", "x.fixed.1.md", "x.fixed.md.md", "x.fixed"]
)
def test_towncrier_fixed_fragments_require_evidence(tmp_path, status, basename):
    changes = [
        (status, f"changelog.d/{basename}"),
        ("M", "policyengine_uk/variables/regression.py"),
    ]
    report = _report(tmp_path, "No evidence.", changes, labels=())
    assert report.is_fix
    assert not report.passed


@PROPERTY_SETTINGS
@given(paths=st.lists(_executable_path, min_size=1, max_size=6, unique=True))
def test_deleted_tests_never_count_as_executable_or_reproducers(tmp_path, paths):
    changes = [("D", path) for path in paths]
    assert checker.changed_executable_tests(changes) == []

    path = paths[0]
    content = (
        "def test_regression():\n    pass\n"
        if path.endswith(".py")
        else "- name: regression\n  output: {x: 1}\n"
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
    assert report.passed is (status in {"A", "M", "T"} and defines_name)


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
@example(
    changes=[("T", "policyengine_uk/variables/regression.py")],
    reason="CI only",
    prefix="n/a: ",
)
@example(changes=[("M", "pyproject.toml")], reason="CI only", prefix="n/a: ")
@example(changes=[("M", "uv.lock")], reason="CI only", prefix="n/a: ")
def test_na_requires_reason_and_no_model_source_changes(
    tmp_path, changes, reason, prefix
):
    has_model_source = any(
        status in {"A", "M", "T", "D"}
        and (
            path in {"pyproject.toml", "uv.lock"}
            or (
                path.startswith("policyengine_uk/")
                and not path.startswith("policyengine_uk/tests/")
            )
        )
        for status, path in changes
    )
    report = _report(tmp_path, f"Reproducer: {prefix}{reason}", changes)
    assert report.passed is (bool(reason.strip()) and not has_model_source)


@pytest.mark.parametrize("status", ["A", "M", "T", "D"])
@pytest.mark.parametrize(
    "path", ["policyengine_uk/variables/regression.py", "pyproject.toml", "uv.lock"]
)
def test_na_rejects_every_model_or_dependency_change(tmp_path, status, path):
    assert not _report(tmp_path, "Reproducer: n/a: CI only", [(status, path)]).passed


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
        if not (status in {"A", "M", "T"} and _fixed_fragment(path))
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
            [path] if executable and status in {"A", "M", "T"} else []
        )


@pytest.mark.parametrize(
    "source",
    [
        "- name: Regression case\n  period: 2026\n  input: {}\n  output: {x: 1}\n",
        "- name: 'Regression case'\n  output: {x: 1}\n",
        '- name: "Regression case"\n  output: {x: 1}\n',
        "- period: 2026\n  name: Regression case\n  output: {x: 1}\n",
        "- name: Regression case # An inline comment\n  output: {x: 1}\n",
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
    _write(tmp_path, path, source + "  output: {x: 1}\n")
    assert _report(tmp_path, f"Reproducer: `{path}::{name}`", [("A", path)]).passed


def test_nested_yaml_name_is_not_a_test_entry(tmp_path):
    path = "policyengine_uk/tests/policy/regression.yaml"
    _write(
        tmp_path,
        path,
        "- name: Regression case\n  input:\n    name: Impostor\n  output: {x: 1}\n",
    )
    changes = [("M", path)]
    assert _report(tmp_path, f"Reproducer: {path}::Regression case", changes).passed
    assert not _report(tmp_path, f"Reproducer: {path}::Impostor", changes).passed


@pytest.mark.parametrize(
    "source",
    [
        "[]\n",
        "# No policy tests here.\n",
        "- |\n  name: Ghost\n",
        "- name: Ghost\n  period: 2026\n",
        "name: Ghost\noutput: {x: 1}\n",
        "- name: 123\n  output: {x: 1}\n",
        "- name: [invalid\n  output: {x: 1}\n",
    ],
)
@pytest.mark.parametrize("suffix", ["", "::Ghost"])
def test_yaml_reproducer_rejects_non_executable_documents(tmp_path, source, suffix):
    path = "policyengine_uk/tests/policy/fake.yaml"
    _write(tmp_path, path, source)
    assert not _report(tmp_path, f"Reproducer: {path}{suffix}", [("A", path)]).passed


@pytest.mark.parametrize("output", ["{}", "[]", "5", "null", "[x]"])
def test_yaml_reproducer_needs_a_non_empty_output_mapping(tmp_path, output):
    # An entry whose output is empty or not a mapping asserts nothing.
    path = "policyengine_uk/tests/policy/regression.yaml"
    _write(tmp_path, path, f"- name: Regression\n  output: {output}\n")
    changes = [("A", path)]
    assert not _report(tmp_path, f"Reproducer: {path}", changes).passed
    assert not _report(tmp_path, f"Reproducer: {path}::Regression", changes).passed


def test_yaml_named_reproducer_requires_output_on_the_named_entry(tmp_path):
    path = "policyengine_uk/tests/policy/regression.yaml"
    _write(
        tmp_path,
        path,
        "- name: Ghost\n  period: 2026\n- name: Real\n  output: {x: 1}\n",
    )
    changes = [("A", path)]
    assert _report(tmp_path, f"Reproducer: {path}", changes).passed
    assert _report(tmp_path, f"Reproducer: {path}::Real", changes).passed
    assert not _report(tmp_path, f"Reproducer: {path}::Ghost", changes).passed


def test_yaml_reproducer_fails_closed_without_pyyaml(tmp_path, monkeypatch):
    path = "policyengine_uk/tests/policy/regression.yaml"
    _write(tmp_path, path, "- name: Regression\n  output: {x: 1}\n")
    monkeypatch.setitem(sys.modules, "yaml", None)
    report = _report(tmp_path, f"Reproducer: {path}::Regression", [("A", path)])
    assert not report.passed
    assert any(
        "cannot validate YAML tests without PyYAML" in message
        for message in report.messages
    )
    # Python evidence still works when the optional YAML parser is unavailable.
    python_path = "policyengine_uk/tests/test_regression.py"
    _write(tmp_path, python_path, "def test_regression():\n    pass\n")
    assert _report(
        tmp_path, f"Reproducer: {python_path}::test_regression", [("A", python_path)]
    ).passed


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
        ("def helper():\n    pass\n", "::helper"),
        (
            "class Regression:\n    def test_regression(self):\n        pass\n",
            "::Regression::test_regression",
        ),
        (
            "class TestRegression:\n    def __init__(self):\n        pass\n"
            "    def test_regression(self):\n        pass\n",
            "::TestRegression::test_regression",
        ),
        (
            "__test__ = False\ndef test_regression():\n    pass\n",
            "::test_regression",
        ),
        (
            "def test_regression():\n    pass\n__test__: bool = False\n",
            "::test_regression",
        ),
        (
            "class TestRegression:\n    __test__ = False\n"
            "    def test_regression(self):\n        pass\n",
            "::TestRegression::test_regression",
        ),
        (
            "class TestRegression:\n    __test__: bool = False\n"
            "    def test_regression(self):\n        pass\n",
            "::TestRegression::test_regression",
        ),
        (
            "def wrapper():\n    def test_regression():\n        pass\n",
            "::test_regression",
        ),
        (
            "if False:\n    def test_regression():\n        pass\n",
            "::test_regression",
        ),
        (
            "if True:\n    class TestRegression:\n"
            "        def test_regression(self):\n            pass\n",
            "::TestRegression::test_regression",
        ),
        (
            "class TestRegression:\n    if True:\n"
            "        def test_regression(self):\n            pass\n",
            "::TestRegression::test_regression",
        ),
        (
            "class TestOther:\n    def test_regression(self):\n        pass\n",
            "::TestRegression::test_regression",
        ),
        (
            "class TestRegression:\n    def test_regression(self):\n        pass\n",
            "::TestRegression::Nested::test_regression",
        ),
        (
            "__test__ = 0\ndef test_regression():\n    pass\n",
            "::test_regression",
        ),
        (
            "class TestRegression:\n    __test__ = None\n"
            "    def test_regression(self):\n        pass\n",
            "::TestRegression::test_regression",
        ),
        (
            "def test_regression():\n    pass\ntest_regression.__test__ = False\n",
            "::test_regression",
        ),
        (
            "class TestRegression:\n    def test_regression(self):\n        pass\n"
            "TestRegression.__test__ = False\n",
            "::TestRegression::test_regression",
        ),
        (
            "class TestRegression:\n    def __new__(cls):\n        pass\n"
            "    def test_regression(self):\n        pass\n",
            "::TestRegression::test_regression",
        ),
        (
            "class Base:\n    def __init__(self):\n        pass\n"
            "class TestRegression(Base):\n    def test_regression(self):\n"
            "        pass\n",
            "::TestRegression::test_regression",
        ),
        (
            "import pytest\n@pytest.fixture\ndef test_regression():\n    pass\n",
            "::test_regression",
        ),
        (
            "def test_regression():\n    pass\ndef test_regression(x):\n    pass\n"
            "test_regression.__test__ = False\n",
            "::test_regression",
        ),
        (
            "from helpers import TestCase\nclass TestRegression(TestCase):\n"
            "    def test_regression(self):\n        pass\n",
            "::TestRegression::test_regression",
        ),
        (
            "from .unittest import TestCase\nclass TestRegression(TestCase):\n"
            "    def test_regression(self):\n        pass\n",
            "::TestRegression::test_regression",
        ),
        (
            "from unittest import TestCase\nfrom helpers import TestCase\n"
            "class TestRegression(TestCase):\n"
            "    def test_regression(self):\n        pass\n",
            "::TestRegression::test_regression",
        ),
        (
            "from helpers import TestCase\nclass TestRegression(TestCase):\n"
            "    def test_regression(self):\n        pass\n"
            "from unittest import TestCase\n",
            "::TestRegression::test_regression",
        ),
        (
            "from unittest import TestCase\nfrom helpers import *\n"
            "class TestRegression(TestCase):\n"
            "    def test_regression(self):\n        pass\n",
            "::TestRegression::test_regression",
        ),
        (
            "from unittest import TestCase\nif True:\n"
            "    from helpers import TestCase\n"
            "class TestRegression(TestCase):\n"
            "    def test_regression(self):\n        pass\n",
            "::TestRegression::test_regression",
        ),
        (
            "import helpers\nfrom unittest import TestCase\n"
            "TestCase, _ = helpers.TestCase, 0\n"
            "class TestRegression(TestCase):\n"
            "    def test_regression(self):\n        pass\n",
            "::TestRegression::test_regression",
        ),
    ],
)
def test_pytest_reproducer_rejects_bare_paths_and_nonexistent_definitions(
    tmp_path, source, suffix
):
    path = "policyengine_uk/tests/test_regression.py"
    _write(tmp_path, path, source)
    assert not _report(tmp_path, f"Reproducer: {path}{suffix}", [("M", path)]).passed


def test_pytest_default_collection_confirms_function_and_class_names(
    tmp_path, monkeypatch
):
    path = "policyengine_uk/tests/test_regression.py"
    _write(
        tmp_path,
        path,
        "def testament():\n    pass\n"
        "def helper():\n    pass\n"
        "class Testimony:\n    def testimony(self):\n        pass\n"
        "class Regression:\n    def test_hidden(self):\n        pass\n"
        "class TestConstructor:\n    def __init__(self):\n        pass\n"
        "    def test_hidden(self):\n        pass\n"
        "class TestDisabled:\n    __test__ = False\n"
        "    def test_hidden(self):\n        pass\n"
        "class TestFalsy:\n    __test__ = 0\n"
        "    def test_hidden(self):\n        pass\n"
        "class TestAllocator:\n    def __new__(cls):\n        pass\n"
        "    def test_hidden(self):\n        pass\n"
        "class TestInherited(TestConstructor):\n"
        "    def test_hidden(self):\n        pass\n"
        "def test_switched_off():\n    pass\n"
        "test_switched_off.__test__ = False\n"
        "from unittest import TestCase\n"
        "class TestUnittest(TestCase):\n"
        "    def test_case(self):\n        pass\n",
    )

    class Collection:
        def pytest_collection_finish(self, session):
            self.nodeids = [item.nodeid for item in session.items]

    collection = Collection()
    # Reuse pytest's interpreter so the oracle only pays the cost of collection.
    with monkeypatch.context() as context:
        context.chdir(tmp_path)
        context.setenv("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "1")
        result = pytest.main(
            [
                "-c",
                os.devnull,
                "--collect-only",
                "--import-mode=importlib",
                "--confcutdir",
                str(tmp_path),
                "-q",
                "-p",
                "no:cacheprovider",
                path,
            ],
            plugins=[collection],
        )
    assert result == pytest.ExitCode.OK
    collected = {nodeid.split("::", 1)[1] for nodeid in collection.nodeids}
    assert collected == {"testament", "Testimony::testimony", "TestUnittest::test_case"}
    for suffix in [
        "testament",
        "helper",
        "Testimony::testimony",
        "Regression::test_hidden",
        "TestConstructor::test_hidden",
        "TestDisabled::test_hidden",
        "TestFalsy::test_hidden",
        "TestAllocator::test_hidden",
        "TestInherited::test_hidden",
        "test_switched_off",
        "TestUnittest::test_case",
    ]:
        nodeid = f"{path}::{suffix}"
        report = _report(tmp_path, f"Reproducer: {nodeid}", [("A", path)])
        assert report.passed is (suffix in collected)


@pytest.mark.parametrize(
    "source, suffix",
    [
        (
            "import pytest\n@pytest.mark.skip(reason='later')\n"
            "def test_regression():\n    pass\n",
            "::test_regression",
        ),
        (
            "from pytest import mark\n@mark.xfail\ndef test_regression():\n    pass\n",
            "::test_regression",
        ),
        (
            "import pytest\npytestmark = [pytest.mark.skip]\n"
            "def test_regression():\n    pass\n",
            "::test_regression",
        ),
        (
            "import pytest\n@pytest.mark.xfail(strict=True)\nclass TestRegression:\n"
            "    def test_regression(self):\n        pass\n",
            "::TestRegression::test_regression",
        ),
        (
            "import pytest\nclass TestRegression:\n"
            "    pytestmark = pytest.mark.skip(reason='later')\n"
            "    def test_regression(self):\n        pass\n",
            "::TestRegression::test_regression",
        ),
        (
            "import unittest\nclass TestRegression(unittest.TestCase):\n"
            "    @unittest.skip('later')\n"
            "    def test_regression(self):\n        pass\n",
            "::TestRegression::test_regression",
        ),
        (
            "from unittest import TestCase, expectedFailure\n"
            "class TestRegression(TestCase):\n    @expectedFailure\n"
            "    def test_regression(self):\n        pass\n",
            "::TestRegression::test_regression",
        ),
        (
            "from pytest import mark as m\npytestmark = m.skip\n"
            "def test_regression():\n    pass\n",
            "::test_regression",
        ),
        (
            "import pytest\nm = pytest.mark\nclass TestRegression:\n"
            "    pytestmark = [m.xfail]\n"
            "    def test_regression(self):\n        pass\n",
            "::TestRegression::test_regression",
        ),
    ],
)
def test_pytest_reproducer_must_not_be_skipped_or_expected_to_fail(
    tmp_path, source, suffix
):
    # pytest collects these, but a skipped or xfailed test reproduces nothing.
    path = "policyengine_uk/tests/test_regression.py"
    _write(tmp_path, path, source)
    report = _report(tmp_path, f"Reproducer: {path}{suffix}", [("M", path)])
    assert not report.passed
    assert any("so it would not run" in message for message in report.messages)


@pytest.mark.parametrize(
    "source, suffix",
    [
        (
            "from hypothesis import given, strategies as st\n"
            "@given(st.integers())\ndef test_regression(x):\n    pass\n",
            "::test_regression",
        ),
        (
            "import pytest\n@pytest.mark.parametrize('x', [1, 2])\n"
            "@pytest.mark.microsimulation\ndef test_regression(x):\n    pass\n",
            "::test_regression[1]",
        ),
        (
            "import unittest\nclass TestRegression(unittest.TestCase):\n"
            "    def test_regression(self):\n        pass\n",
            "::TestRegression::test_regression",
        ),
        (
            "import sys, pytest\n"
            "@pytest.mark.skipif(sys.platform == 'win32', reason='no FIFOs')\n"
            "def test_regression():\n    pass\n",
            "::test_regression",
        ),
        (
            "from unittest import TestCase\nclass TestRegression(TestCase):\n"
            "    def test_regression(self):\n        pass\n",
            "::TestRegression::test_regression",
        ),
        (
            "from unittest import TestCase\nclass TestRegression(TestCase):\n"
            "    def test_regression(self):\n        pass\n"
            "from helpers import TestCase\n",
            "::TestRegression::test_regression",
        ),
        (
            "import pytest, config\n"
            "pytestmark = pytest.mark.skipif(config.skip, reason='optional')\n"
            "def test_regression():\n    pass\n",
            "::test_regression",
        ),
        (
            "import unittest, sys\nclass TestRegression(unittest.TestCase):\n"
            "    @unittest.skipIf(sys.platform == 'win32', 'no FIFOs')\n"
            "    def test_regression(self):\n        pass\n",
            "::TestRegression::test_regression",
        ),
        (
            "class TestRegression(object):\n    __test__ = True\n"
            "    def test_regression(self):\n        pass\n",
            "::TestRegression::test_regression",
        ),
    ],
)
def test_pytest_reproducer_accepts_marks_and_decorators_that_still_run(
    tmp_path, source, suffix
):
    path = "policyengine_uk/tests/test_regression.py"
    _write(tmp_path, path, source)
    assert _report(tmp_path, f"Reproducer: {path}{suffix}", [("M", path)]).passed


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


def test_html_commented_reproducer_is_ignored(tmp_path):
    path = "policyengine_uk/tests/test_regression.py"
    _write(tmp_path, path, "def test_regression():\n    pass\n")
    commented = "<!-- Template guidance.\nReproducer: <test id>\n-->\n"
    body = commented + f"Reproducer: {path}::test_regression"
    assert checker.parse_reproducers(body) == [f"{path}::test_regression"]
    assert _report(tmp_path, body, [("A", path)]).passed
    assert not _report(
        tmp_path, f"<!--\nReproducer: {path}::test_regression\n-->", [("A", path)]
    ).passed


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
    head_sha=None,
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
    if head_sha is not None:
        args.extend(["--head-sha", head_sha])
    if summary is not None:
        args.extend(["--summary-file", str(summary)])
    return args


def _standalone_checker(args, repo_root, monkeypatch):
    # Execute the real trusted entry point without starting another interpreter.
    with monkeypatch.context() as context:
        context.chdir(repo_root)
        context.setattr(sys, "argv", [str(CHECKER), *args])
        with pytest.raises(SystemExit) as exit:
            runpy.run_path(str(CHECKER), run_name="__main__")
    return exit.value.code


@pytest.mark.parametrize(
    "body, labels, changes, expected",
    [
        ("Reproducer: n/a: CI only", "bug\n", "M\0.github/workflows/check.yaml\0", 0),
        (
            "Reproducer: policyengine_uk/tests/test_regression.py::test_regression",
            "bug-fix\n",
            "M\0policyengine_uk/tests/test_regression.py\0",
            0,
        ),
        ("No evidence.", "bug\n", "M\0policyengine_uk/variables/regression.py\0", 1),
        (
            "Reproducer: invalid",
            "enhancement\n",
            "D\0changelog.d/regression.fixed.md\0",
            0,
        ),
        (
            "Reproducer: n/a: CI only",
            "bug\n",
            "T\0.github/workflows/check.yaml\0Q\0docs/regression.md\0",
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
        "M\tpath.py\n",
        "M\0\0",
        "MM\0path.py\0",
        "R100\0old.py\0new.py\0",
        "M\0first.py\0second.py\0",
        "M\0path.py",
        "M\0../outside.py\0",
        "M\0/absolute.py\0",
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


def _git_env():
    return {
        **os.environ,
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_NOSYSTEM": "1",
    }


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
            "-c",
            "gc.auto=0",
            "-c",
            "maintenance.auto=false",
            *args,
        ],
        cwd=repo_root,
        capture_output=True,
        text=True,
        timeout=15,
        env=_git_env(),
    )
    assert result.returncode == 0, result.stdout + result.stderr
    # Stripping output would corrupt paths ending in whitespace in NUL diffs.
    return result.stdout


def _commit(repo_root, message):
    _git(repo_root, "add", ".")
    _git(repo_root, "commit", "-m", message)
    return _git(repo_root, "rev-parse", "HEAD").strip()


@pytest.fixture
def git_repo(tmp_path, monkeypatch):
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", os.devnull)
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    _git(repo_root, "init", "--initial-branch=fixture", "--template=")
    return repo_root


def test_nul_delimited_git_diff_preserves_literal_paths(git_repo):
    _write(git_repo, "baseline.txt", "Before the change.\n")
    base = _commit(git_repo, "Fixture baseline")
    paths = ["docs/é\\303.md", "docs/tab\tnewline\ntrailing .md ", 'docs/"quoted".md']
    for path in paths:
        _write(git_repo, path, "A documentation change.\n")
    head = _commit(git_repo, "Fixture literal paths")
    changes = _git(
        git_repo,
        "-c",
        "core.quotePath=false",
        "diff",
        "--name-status",
        "--no-renames",
        "-z",
        base,
        head,
    )
    assert set(checker.parse_changes(changes)) == {("A", path) for path in paths}


def test_real_git_diff_and_standalone_checker(tmp_path, git_repo, monkeypatch, capsys):
    repo_root = git_repo
    python_path = "policyengine_uk/tests/test_regression.py"
    yaml_path = "policyengine_uk/tests/gov/regression.yaml"
    _write(repo_root, python_path, "def test_regression():\n    pass\n")
    _write(repo_root, yaml_path, "- name: Regression\n  period: 2025\n")
    base = _commit(repo_root, "Fixture before the fix")

    _write(repo_root, python_path, "def test_regression():\n    assert 1 + 1 == 2\n")
    _write(repo_root, yaml_path, "- name: Regression\n  period: 2026\n")
    _write(repo_root, "changelog.d/regression.fixed.md", "- Fixed a regression.\n")
    head = _commit(repo_root, "Fixture fix and its evidence")
    merge_base = _git(repo_root, "merge-base", base, head).strip()
    changes = _git(
        repo_root, "diff", "--name-status", "--no-renames", "-z", merge_base, head
    )
    assert f"M\0{python_path}\0" in changes
    assert f"M\0{yaml_path}\0" in changes
    assert "A\0changelog.d/regression.fixed.md\0" in changes

    # The base checkout need not contain any of the PR's changed test files.
    _git(repo_root, "checkout", "--detach", base)

    for nodeid, expected in [(f"{python_path}::test_regression", 0), (yaml_path, 1)]:
        args = _arguments(
            tmp_path / "inputs",
            repo_root,
            body=f"Reproducer: {nodeid}",
            labels="",
            changes=changes,
            head_sha=head,
        )
        code = _standalone_checker(args, repo_root, monkeypatch)
        output = capsys.readouterr().out
        assert code == expected, output
        assert "Fix a regression" in output
        if expected:
            assert "Reproducer:" in output


@pytest.mark.parametrize("target_in_repository", [True, False])
def test_git_object_mode_rejects_symlinked_test_paths(
    tmp_path, git_repo, target_in_repository
):
    path = "policyengine_uk/tests/test_fake.py"
    target_root = git_repo if target_in_repository else tmp_path
    target = _write(target_root, "test_real.py", "def test_regression():\n    pass\n")
    link = git_repo / path
    link.parent.mkdir(parents=True)
    link.symlink_to(target)
    head = _commit(git_repo, "Fixture symlink reproducer")
    report = _report(
        git_repo,
        f"Reproducer: {path}::test_regression",
        [("A", path)],
        head_sha=head,
    )
    assert not report.passed
    assert any("symlink" in message.lower() for message in report.messages)


def test_git_object_mode_ignores_fabricated_worktree_evidence(
    tmp_path, git_repo, monkeypatch, capsys
):
    path = "policyengine_uk/tests/test_fake.py"
    _write(git_repo, path, "# No test exists in the committed file.\n")
    _write(git_repo, ".github/check_fix_pr.py", "raise SystemExit(0)\n")
    (git_repo / "body.md").symlink_to(path)
    head = _commit(git_repo, "Fixture metadata symlink")
    body = (
        f'"""\nReproducer: {path}::test_regression\n"""\n'
        "def test_regression():\n    pass\n"
    )
    # This recreates the old metadata write so the blob must remain authoritative.
    (git_repo / "body.md").write_text(body, encoding="utf-8")
    args = _arguments(
        tmp_path / "inputs",
        git_repo,
        body=body,
        changes=f"A\0{path}\0A\0.github/check_fix_pr.py\0A\0body.md\0",
        head_sha=head,
    )
    code = _standalone_checker(args, git_repo, monkeypatch)
    output = capsys.readouterr().out
    assert code == 1, output
    assert "does not define a collectable named test" in output


def test_git_object_mode_reads_head_without_importing_pr_code(git_repo):
    path = "policyengine_uk/tests/test_regression.py"
    marker = git_repo / "pr-code-executed"
    _write(
        git_repo,
        path,
        f"from pathlib import Path\nPath({str(marker)!r}).touch()\n"
        "def test_regression():\n    pass\n",
    )
    _write(git_repo, ".github/check_fix_pr.py", "raise SystemExit(0)\n")
    head = _commit(git_repo, "Fixture PR code")
    (git_repo / path).unlink()
    report = _report(
        git_repo,
        f"Reproducer: {path}::test_regression",
        [("A", path)],
        head_sha=head,
    )
    assert report.passed
    assert not marker.exists()


def test_git_object_mode_rejects_paths_missing_from_head(git_repo):
    _write(git_repo, "baseline.txt", "A committed baseline.\n")
    head = _commit(git_repo, "Fixture without test")
    path = "policyengine_uk/tests/test_regression.py"
    _write(git_repo, path, "def test_regression():\n    pass\n")
    assert not _report(
        git_repo,
        f"Reproducer: {path}::test_regression",
        [("A", path)],
        head_sha=head,
    ).passed


def test_the_workflow_reports_on_pull_requests_and_merge_groups():
    import yaml

    workflow = yaml.safe_load(
        (REPO_ROOT / ".github" / "workflows" / "pr_fix_evidence.yaml").read_text(
            encoding="utf-8"
        )
    )
    # PyYAML reads the key "on" as True.
    triggers = workflow.get("on", workflow.get(True))
    assert set(triggers) == {"pull_request_target", "merge_group"}
    assert "paths" not in triggers["pull_request_target"]
    assert workflow["permissions"] == {"contents": "read"}
    [job] = workflow["jobs"].values()
    assert job["name"] == "Fix evidence"
    assert "if" not in job
    assert job.get("permissions", workflow["permissions"]) == {"contents": "read"}

    steps = job["steps"]
    [checkout] = [
        step for step in steps if step.get("uses", "").startswith("actions/checkout@")
    ]
    assert checkout["if"] == "github.event_name == 'pull_request_target'"
    # The event's default checkout supplies the trusted base workflow and checker.
    assert "ref" not in checkout.get("with", {})
    # No token stays in .git/config while PR objects are fetched and read.
    assert checkout["with"]["persist-credentials"] is False
    for step in steps:
        if step.get("uses", "").startswith("actions/checkout@"):
            reference = str(step.get("with", {}).get("ref", ""))
            assert "github.event.pull_request.head.sha" not in reference
            assert "github.event.pull_request.head.ref" not in reference
        run = step.get("run", "")
        assert not re.search(r"\b(?:pip(?:3)?\s+install|uv\s+sync|make)\b", run)
        assert not re.search(r"\bgit\s+(?:checkout|switch|reset)\b", run)

    [setup_uv] = [
        step for step in steps if step.get("uses", "").startswith("astral-sh/setup-uv@")
    ]
    assert setup_uv["uses"] == "astral-sh/setup-uv@v8.1.0"
    assert setup_uv["if"] == "github.event_name == 'pull_request_target'"

    [collect] = [step for step in steps if step.get("id") == "evidence"]
    assert collect["if"] == "github.event_name == 'pull_request_target'"
    assert collect["env"]["PR_NUMBER"] == "${{ github.event.pull_request.number }}"
    collect_run = collect["run"]
    assert 'mktemp -d "$RUNNER_TEMP/fix-evidence.XXXXXX"' in collect_run
    assert "directory=%s\\n" in collect_run
    assert '"$GITHUB_OUTPUT"' in collect_run
    for filename in ["title.txt", "body.md", "labels.txt", "changes.bin"]:
        assert f'> "$evidence_dir/{filename}"' in collect_run
    assert (
        'git fetch --no-tags origin "+refs/pull/${PR_NUMBER}/head:refs/remotes/pr/head"'
        in collect_run
    )
    assert 'git merge-base "$PR_BASE_SHA" "$PR_HEAD_SHA"' in collect_run
    assert "git diff --name-status --no-renames -z" in collect_run

    [check] = [
        step for step in steps if ".github/check_fix_pr.py" in step.get("run", "")
    ]
    assert check["if"] == "github.event_name == 'pull_request_target'"
    assert check.get("working-directory", ".") == "."
    assert check["env"]["EVIDENCE_DIR"] == "${{ steps.evidence.outputs.directory }}"
    check_run = check["run"]
    assert (
        "uv run --no-project --with pyyaml==6.0.2 python .github/check_fix_pr.py"
        in check_run
    )
    for option, filename in [
        ("title", "title.txt"),
        ("body", "body.md"),
        ("labels", "labels.txt"),
        ("changes", "changes.bin"),
    ]:
        assert f'--{option}-file "$EVIDENCE_DIR/{filename}"' in check_run
    assert '--repo-root . --head-sha "$PR_HEAD_SHA"' in check_run

    [merge_group] = [
        step for step in steps if step.get("if") == "github.event_name == 'merge_group'"
    ]
    assert merge_group["run"].startswith("echo ")
