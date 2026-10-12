"""Require a changed test and a named reproducer for fix pull requests.

This runs before the package is installed. Read test definitions rather than
importing PR code. YAML validation uses PyYAML when available and fails closed
without it; checking evidence never needs model dependencies or datasets.
"""

import argparse
import ast
import html
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path, PurePosixPath


TESTS_PREFIX = "policyengine_uk/tests/"
POLICY_PREFIX = TESTS_PREFIX + "policy/"
REPRODUCER_HINT = (
    'Use "Reproducer: policyengine_uk/tests/test_example.py::test_regression", '
    '"Reproducer: policyengine_uk/tests/policy/example.yaml::Case name", '
    'or "Reproducer: n/a: <reason>" when model source and dependencies are unchanged.'
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
    """Read status/path pairs from git diff --name-status --no-renames -z."""
    if not text:
        return []
    fields = text.split("\0")
    if fields.pop() != "" or len(fields) % 2:
        raise ValueError("Changes must be NUL-terminated status/path pairs")
    changes = []
    for status, path in zip(fields[::2], fields[1::2]):
        if not re.fullmatch(r"[A-Z]", status):
            raise ValueError(f"Unparseable change status: {status!r}")
        if not _relative_path(path):
            raise ValueError(f"Invalid repository path: {path!r}")
        changes.append((status, path))
    return changes


def classify_fix_pr(
    title: str, body: str, labels: list[str], changes: list[tuple[str, str]]
) -> bool:
    """Classify from PR metadata only; title and body are reserved for later rules."""
    return (
        bool({"bug", "bug-fix"}.intersection(labels))
        or any(
            status in ("A", "M", "T")
            and path.startswith("changelog.d/")
            and len(path.split("/")) == 2
            # Towncrier searches every basename part after the issue for its type.
            and "fixed" in PurePosixPath(path).name.split(".")[1:]
            for status, path in changes
        )
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
        if status in ("A", "M", "T") and (_pytest_module(path) or _policy_test(path))
    ]


def _exemption(reproducer: str) -> re.Match | None:
    return re.fullmatch(r"(?:n/a\s*[:\-]|none\s*:)\s*(.*)", reproducer, re.IGNORECASE)


def _unquote_id(value: str) -> str:
    value = value.strip()
    return value[1:-1] if value.startswith("`") and value.endswith("`") else value


def parse_reproducers(body: str) -> list[str]:
    # Template guidance is not evidence supplied by the contributor.
    body = re.sub(r"<!--.*?-->", "", body, flags=re.DOTALL)
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


def _read_test(repo_root: Path, path: str, head_sha: str | None) -> bytes:
    if head_sha is not None:

        def git(*args: str) -> bytes:
            return subprocess.run(
                ["git", "-C", str(repo_root), "--literal-pathspecs", *args],
                check=True,
                capture_output=True,
                timeout=15,
            ).stdout

        entries = git("ls-tree", "-z", head_sha, "--", path).split(b"\0")
        if len(entries) != 2 or entries[-1] != b"":
            raise ValueError("the test file is missing from the PR head")
        metadata, entry_path = entries[0].split(b"\t", 1)
        mode, kind, _ = metadata.split()
        if entry_path.decode("utf-8", errors="surrogateescape") != path:
            raise ValueError("the test file is missing from the PR head")
        # A symlink's blob is its target text, not an executable test file.
        if mode == b"120000":
            raise ValueError("a symlink cannot be a reproducer")
        if mode not in (b"100644", b"100755") or kind != b"blob":
            raise ValueError("the reproducer must be a regular test file")
        return git("cat-file", "blob", f"{head_sha}:{path}")

    # Filesystem mode supports unit fixtures; CI always reads committed blobs.
    file = repo_root
    for part in path.split("/"):
        file = file / part
        if file.is_symlink():
            raise ValueError("a symlink cannot be a reproducer")
    if not file.resolve().is_relative_to(repo_root.resolve()):
        raise ValueError("the test file must be inside the PR checkout")
    return file.read_bytes()


def _assigns_name(node: ast.AST, name: str) -> bool:
    targets = (
        node.targets
        if isinstance(node, ast.Assign)
        else [node.target]
        if isinstance(node, ast.AnnAssign)
        else []
    )
    return any(isinstance(target, ast.Name) and target.id == name for target in targets)


def _suppresses_tests(body: list[ast.stmt]) -> bool:
    return any(
        _assigns_name(node, "__test__")
        and isinstance(node.value, ast.Constant)
        and node.value.value is False
        for node in body
    )


def _reference_problem(
    reproducer: str, tests: set[str], repo_root: Path, head_sha: str | None
) -> str | None:
    path, separator, name = reproducer.partition("::")
    if path not in tests:
        return "the path must be an added, modified or type-changed executable test in this PR"
    try:
        source = _read_test(repo_root, path, head_sha)
        if _policy_test(path):
            try:
                import yaml
            except ImportError:
                return "cannot validate YAML tests without PyYAML"
            try:
                entries = yaml.safe_load(source.decode("utf-8"))
            except yaml.YAMLError as error:
                return f"the YAML file cannot be parsed: {error}"
            names = (
                {
                    entry["name"]
                    for entry in entries
                    if isinstance(entry, dict)
                    and isinstance(entry.get("name"), str)
                    and "output" in entry
                }
                if isinstance(entries, list)
                else set()
            )
            if not names:
                return "the YAML file has no test mapping with a string name and output"
            if separator and name not in names:
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
        tree = ast.parse(source, filename=path)
        if _suppresses_tests(tree.body):
            return "pytest collection is disabled by module __test__ = False"
        definitions = (ast.FunctionDef, ast.AsyncFunctionDef)
        if (
            len(parts) == 1
            and parts[0].startswith("test")
            and any(
                isinstance(node, definitions) and node.name == parts[0]
                for node in tree.body
            )
        ):
            return None
        if (
            len(parts) == 2
            and parts[0].startswith("Test")
            and parts[1].startswith("test")
            and any(
                isinstance(node, ast.ClassDef)
                and node.name == parts[0]
                and not _suppresses_tests(node.body)
                and not any(
                    (isinstance(method, definitions) and method.name == "__init__")
                    or _assigns_name(method, "__init__")
                    for method in node.body
                )
                and any(
                    isinstance(method, definitions) and method.name == parts[1]
                    for method in node.body
                )
                for node in tree.body
            )
        ):
            return None
        return "the pytest file does not define a collectable named test"
    except (
        OSError,
        RuntimeError,
        SyntaxError,
        UnicodeError,
        ValueError,
        subprocess.SubprocessError,
    ) as error:
        return f"the test file cannot be read or parsed: {error}"


def check_fix_pr(
    title: str,
    body: str,
    labels: list[str],
    changes: list[tuple[str, str]],
    repo_root: Path,
    head_sha: str | None = None,
) -> Report:
    if head_sha is not None and not re.fullmatch(
        r"(?:[0-9a-fA-F]{40}|[0-9a-fA-F]{64})", head_sha
    ):
        raise ValueError("The PR head must be a full hexadecimal commit SHA")
    if not classify_fix_pr(title, body, labels, changes):
        return Report(
            title,
            False,
            True,
            [
                "Not a fix PR: no added/modified/type-changed fixed fragment or bug/bug-fix label."
            ],
        )
    tests = set(changed_executable_tests(changes))
    model_changed = any(
        status in ("A", "M", "T", "D")
        and (
            (path.startswith("policyengine_uk/") and not path.startswith(TESTS_PREFIX))
            or path in ("pyproject.toml", "uv.lock")
        )
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
                else "n/a is allowed only when model source outside tests, pyproject.toml and uv.lock are unchanged"
                if model_changed
                else None
            )
            valid_exemption |= problem is None
        else:
            problem = _reference_problem(reproducer, tests, repo_root, head_sha)
        if problem:
            reproducer_messages.append(
                f"Invalid reproducer {reproducer!r}: {problem}. {REPRODUCER_HINT}"
            )
    if not reproducers:
        reproducer_messages.append(f"Missing named reproducer. {REPRODUCER_HINT}")
    messages = []
    if not tests and not valid_exemption:
        messages.append(
            "No added, modified or type-changed executable test. Add a pytest module under "
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
                "Exemption accepted: model source and dependencies are unchanged."
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
    parser.add_argument(
        "--head-sha",
        help="Read tests from this commit's git objects instead of the filesystem",
    )
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
        # Preserve path bytes, including literal newlines, rather than decoding Git quotes.
        changes = parse_changes(
            args.changes_file.read_bytes().decode("utf-8", errors="surrogateescape")
        )
        if not args.repo_root.is_dir():
            raise ValueError(f"Repository root is not a directory: {args.repo_root}")
        report = check_fix_pr(
            title, body, labels, changes, args.repo_root, args.head_sha
        )
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
