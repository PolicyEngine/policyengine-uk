"""Require a changed test and a named reproducer for fix pull requests.

This runs before the package is installed. Read test definitions rather than
importing PR code, so checking evidence needs neither dependencies nor datasets.
"""

import argparse
import ast
import html
import json
import re
from dataclasses import dataclass
from pathlib import Path, PurePosixPath


TESTS_PREFIX = "policyengine_uk/tests/"
POLICY_PREFIX = TESTS_PREFIX + "policy/"
REPRODUCER_HINT = (
    'Use "Reproducer: policyengine_uk/tests/test_example.py::test_regression", '
    '"Reproducer: policyengine_uk/tests/policy/example.yaml::Case name", '
    'or "Reproducer: n/a: <reason>" for CI/docs-only fixes.'
)


@dataclass
class Report:
    title: str
    is_fix: bool
    passed: bool
    messages: list[str]


def _relative_path(path: str) -> bool:
    return bool(path) and all(part not in ("", ".", "..") for part in path.split("/"))


def parse_changes(text: str) -> list[tuple[str, str]]:
    """Read the two columns emitted by git diff --name-status --no-renames."""
    changes = []
    for number, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            continue
        match = re.fullmatch(r"([A-Z])\t([^\t]+)", line)
        if not match:
            raise ValueError(f"Unparseable changes line {number}: {line!r}")
        status, path = match.groups()
        if path.startswith('"'):
            # Git quotes unusual paths and encodes non-ASCII bytes as octal.
            try:
                path = ast.literal_eval(path)
                if re.search(r"\\[0-7]{3}", match[2]):
                    path = path.encode("latin-1").decode("utf-8")
            except (SyntaxError, ValueError, UnicodeError) as error:
                raise ValueError(
                    f"Unparseable path on changes line {number}"
                ) from error
        if not isinstance(path, str) or not _relative_path(path):
            raise ValueError(
                f"Invalid repository path on changes line {number}: {path!r}"
            )
        changes.append((status, path))
    return changes


def classify_fix_pr(
    title: str, body: str, labels: list[str], changes: list[tuple[str, str]]
) -> bool:
    """Classify from PR metadata only; title and body are reserved for later rules."""
    return bool({"bug", "bug-fix"}.intersection(labels)) or any(
        status in ("A", "M") and re.fullmatch(r"changelog\.d/[^/]+\.fixed\.md", path)
        for status, path in changes
    )


def _pytest_module(path: str) -> bool:
    name = PurePosixPath(path).name
    return (
        _relative_path(path)
        and path.startswith(TESTS_PREFIX)
        and name not in ("conftest.py", "__init__.py")
        and (name.startswith("test_") or name.endswith("_test.py"))
        and name.endswith(".py")
    )


def _policy_test(path: str) -> bool:
    return (
        _relative_path(path)
        and path.startswith(POLICY_PREFIX)
        and PurePosixPath(path).suffix in (".yaml", ".yml")
    )


def changed_executable_tests(changes: list[tuple[str, str]]) -> list[str]:
    return [
        path
        for status, path in changes
        if status in ("A", "M") and (_pytest_module(path) or _policy_test(path))
    ]


def _exemption(reproducer: str) -> re.Match | None:
    return re.fullmatch(r"(?:n/a\s*[:\-]|none\s*:)\s*(.*)", reproducer, re.IGNORECASE)


def _unquote_id(value: str) -> str:
    value = value.strip()
    return value[1:-1] if value.startswith("`") and value.endswith("`") else value


def parse_reproducers(body: str) -> list[str]:
    ids = []
    for line in body.splitlines():
        match = re.match(r"^\s*reproducer:\s*(.*)$", line, re.IGNORECASE)
        if not match or not match[1].strip():
            continue
        value = match[1].strip()
        start = 0
        quoted = False
        brackets = 0
        for index, character in enumerate(value):
            if character == "`":
                quoted = not quoted
            elif not quoted:
                if character == "[":
                    brackets += 1
                elif character == "]" and brackets:
                    brackets -= 1
                elif character in ",;" and brackets == 0:
                    ids.append(_unquote_id(value[start:index]))
                    start = index + 1
        ids.append(_unquote_id(value[start:]))
    return ids


def _yaml_double_quoted(value: str) -> str:
    # YAML allows additional escapes beyond JSON. Translate those while keeping
    # JSON's handling of Unicode and escaped quotes, without installing PyYAML.
    extra_escapes = {
        "0": "\0",
        "a": "\a",
        "v": "\v",
        "e": "\x1b",
        " ": " ",
        "\t": "\t",
        "N": "\u0085",
        "_": "\u00a0",
        "L": "\u2028",
        "P": "\u2029",
    }

    def translate(match: re.Match) -> str:
        escape = match[1]
        if escape[0] in ("x", "U") and len(escape) > 1:
            character = chr(int(escape[1:], 16))
        elif escape in extra_escapes:
            character = extra_escapes[escape]
        else:
            return match[0]
        return json.dumps(character)[1:-1]

    return json.loads(
        re.sub(r"\\(x[0-9a-fA-F]{2}|U[0-9a-fA-F]{8}|.)", translate, value)
    )


def _yaml_names(text: str) -> set[str]:
    """Read name scalars at test-entry level, excluding nested input names."""
    lines = [
        line
        for line in text.splitlines()
        if line.strip() and not line.lstrip().startswith(("#", "---", "...", "%"))
    ]
    if not lines:
        return set()
    root_indent = min(len(line) - len(line.lstrip(" ")) for line in lines)
    is_list = lines[0].lstrip().startswith("-")
    names = set()
    for line in lines:
        match = re.fullmatch(r"( *)(-\s+)?name:\s*(.*)", line)
        if not match:
            continue
        indent, marker, value = match.groups()
        expected_indent = root_indent + (2 if is_list and not marker else 0)
        if len(indent) != expected_indent or (marker and not is_list):
            continue
        if value.startswith("'"):
            scalar = re.fullmatch(r"'((?:[^']|'')*)'\s*(?:#.*)?", value)
            if scalar:
                names.add(scalar[1].replace("''", "'"))
        elif value.startswith('"'):
            scalar = re.fullmatch(r'("(?:[^"\\]|\\.)*")\s*(?:#.*)?', value)
            if scalar:
                try:
                    names.add(_yaml_double_quoted(scalar[1]))
                except ValueError:
                    continue
        elif value and not value.startswith(("#", "|", ">")):
            names.add(re.split(r"\s+#", value, maxsplit=1)[0].strip())
    return names


def _reference_problem(reproducer: str, tests: set[str], repo_root: Path) -> str | None:
    path, separator, name = reproducer.partition("::")
    if path not in tests:
        return "the path must be an added or modified executable test in this PR"
    try:
        file = (repo_root / path).resolve()
        if not file.is_relative_to(repo_root.resolve()):
            return "the test file must be inside the PR checkout"
        if _policy_test(path):
            text = file.read_text(encoding="utf-8")
            if separator and name not in _yaml_names(text):
                return f"the YAML file has no test entry named {name!r}"
            return None
        if not separator or not name:
            return "a pytest reproducer must name a test with ::test_name"
        # Parameters can contain ::, so remove them before splitting the node id.
        if "[" in name:
            if not name.endswith("]"):
                return "pytest parameters must be a terminal [param] suffix"
            name = name.split("[", 1)[0]
        parts = name.split("::")
        tree = ast.parse(file.read_bytes(), filename=path)
        definitions = (ast.FunctionDef, ast.AsyncFunctionDef)
        if len(parts) == 1 and any(
            isinstance(node, definitions) and node.name == parts[0]
            for node in tree.body
        ):
            return None
        if len(parts) == 2 and any(
            isinstance(node, ast.ClassDef)
            and node.name == parts[0]
            and any(
                isinstance(method, definitions) and method.name == parts[1]
                for method in node.body
            )
            for node in tree.body
        ):
            return None
        return "the pytest file does not define the named test"
    except (OSError, RuntimeError, SyntaxError, UnicodeError, ValueError) as error:
        return f"the test file cannot be read or parsed: {error}"


def check_fix_pr(
    title: str,
    body: str,
    labels: list[str],
    changes: list[tuple[str, str]],
    repo_root: Path,
) -> Report:
    if not classify_fix_pr(title, body, labels, changes):
        return Report(
            title,
            False,
            True,
            [
                "Not a fix PR: no added/modified .fixed.md fragment or bug/bug-fix label."
            ],
        )
    tests = set(changed_executable_tests(changes))
    model_changed = any(
        status in ("A", "M", "D")
        and path.startswith("policyengine_uk/")
        and not path.startswith(TESTS_PREFIX)
        for status, path in changes
    )
    reproducer_messages = []
    valid_exemption = False
    reproducers = parse_reproducers(body)
    for reproducer in reproducers:
        exemption = _exemption(reproducer)
        if exemption:
            problem = (
                "n/a requires a non-empty reason"
                if not exemption[1].strip()
                else "n/a is allowed only when no model source outside tests changes"
                if model_changed
                else None
            )
            valid_exemption |= problem is None
        else:
            problem = _reference_problem(reproducer, tests, repo_root)
        if problem:
            reproducer_messages.append(
                f"Invalid reproducer {reproducer!r}: {problem}. {REPRODUCER_HINT}"
            )
    if not reproducers:
        reproducer_messages.append(f"Missing named reproducer. {REPRODUCER_HINT}")
    messages = []
    if not tests and not valid_exemption:
        messages.append(
            "No added or modified executable test. Add a pytest module under "
            "policyengine_uk/tests/ or YAML test under policyengine_uk/tests/policy/. "
            + REPRODUCER_HINT
        )
    messages.extend(reproducer_messages)
    return Report(
        title,
        True,
        not messages,
        messages
        or [
            "Fix PR has valid reproducer evidence. "
            + (
                "CI/docs-only exemption accepted."
                if valid_exemption
                else f"Changed executable tests: {len(tests)}."
            )
        ],
    )


def _emit(report: Report, summary_file: Path | None, unusable: bool = False) -> None:
    outcome = "ERROR" if unusable else "PASS" if report.passed else "FAIL"
    title = " ".join(report.title.splitlines())
    if not report.is_fix and not unusable:
        print(f"Fix evidence: {outcome} ({title!r}). {report.messages[0]}")
    else:
        print(f"Fix evidence: {outcome} ({title!r})")
        for message in report.messages:
            print(f"- {message}")
    if summary_file:

        def markdown(text: str) -> str:
            return re.sub(r"([\\`*_[\]])", r"\\\1", html.escape(text))

        with summary_file.open("a", encoding="utf-8") as summary:
            summary.write(f"\n## Fix evidence\n\n{outcome}: {markdown(title)}\n\n")
            for message in report.messages:
                summary.write(f"- {markdown(message)}\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for option in ("title", "body", "labels", "changes"):
        parser.add_argument(f"--{option}-file", type=Path, required=True)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--summary-file", type=Path)
    args = parser.parse_args(argv)
    title = ""
    unusable = False
    try:
        title = args.title_file.read_text(encoding="utf-8").strip()
        body = args.body_file.read_text(encoding="utf-8")
        labels = [
            label.strip()
            for label in args.labels_file.read_text(encoding="utf-8").splitlines()
            if label.strip()
        ]
        changes = parse_changes(args.changes_file.read_text(encoding="utf-8"))
        if not args.repo_root.is_dir():
            raise ValueError(f"Repository root is not a directory: {args.repo_root}")
        report = check_fix_pr(title, body, labels, changes, args.repo_root)
    except (OSError, UnicodeError, ValueError) as error:
        report = Report(title, False, False, [f"Unusable input: {error}"])
        unusable = True
    try:
        _emit(report, args.summary_file, unusable)
    except (OSError, UnicodeError) as error:
        print(f"Fix evidence: ERROR. Cannot append summary: {error}")
        return 2
    return 2 if unusable else 0 if report.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
