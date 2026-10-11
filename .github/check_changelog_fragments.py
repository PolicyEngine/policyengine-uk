"""Fail a pull request whose changelog fragments towncrier would mishandle.

towncrier writes a fragment to CHANGELOG.md only when its name carries a
fragment type configured in pyproject.toml. It never reads, and never
deletes, any other file in the fragment directory, and it leaves an empty
fragment out. Neither tells the author. On 11 October 2026 main held 93 such
files, and every one of their notes was missing from CHANGELOG.md.

The Changelog workflow (.github/workflows/pr_changelog.yaml) runs this on the
pull request's merge commit, whose first parent is main:

    python .github/check_changelog_fragments.py --base HEAD^1 --head HEAD

and on a merge queue group against the group's base.

Each file the pull request adds or changes in the fragment directory must:

- sit directly in the directory, as a regular file (towncrier follows a
  symbolic link when it builds, and a missing target stops the release);
- be named ``<slug>.<type>.md``, with a type configured in pyproject.toml at
  ``--head``, and a slug of letters, digits, ``.``, ``_`` and ``-``
  (optionally after towncrier's orphan prefix). towncrier also consumes
  other forms, such as ``<slug>.<type>`` and ``<slug>.<type>.<n>.md``; this
  repository does not use them;
- be UTF-8 text that is not blank (towncrier writes other bytes as
  replacement characters, and leaves a blank fragment out);
- not share towncrier's (issue, type, counter) key with another fragment,
  such as ``7.fixed.md`` and ``007.fixed.md``, which stops ``towncrier
  build`` and so the release.

Files towncrier ignores (.gitkeep, README and the configured ``ignore``) are
not fragments and pass. Every name this accepts is one towncrier consumes,
with the type the name shows. Deleting a fragment always passes.

A pull request that changes a file the release workflow runs on
(pyproject.toml or the fragment directory; ``on.push.paths`` in
.github/workflows/versioning.yaml) also fails when its merge would leave no
typed fragment: .github/bump_version.py then has nothing to release and
exits 1.

It warns, without failing, when the pull request adds no fragment, when a
fragment starts with a list marker (towncrier adds the bullet, so it renders
as ``- - ``), and when the directory already holds files towncrier drops.

Exit status: 0 if the pull request passes, 1 if it fails, 2 on a usage,
configuration or git error. Standard library only.
"""

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from bump_version import (  # noqa: E402
    TowncrierConfig,
    annotation,
    is_ignored,
    parse_fragment_name,
    parse_towncrier_config,
)

SLUG = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")
LIST_MARKER = re.compile(r"[-*+]\s")
REGULAR_FILE_MODES = ("100644", "100755")
SYMLINK_MODE = "120000"
# Files, besides the fragment directory, whose changes start the release
# workflow: on.push.paths in .github/workflows/versioning.yaml.
RELEASE_TRIGGER_FILES = ("pyproject.toml",)


@dataclass
class Report:
    errors: list[tuple[str | None, str]] = field(default_factory=list)
    warnings: list[tuple[str | None, str]] = field(default_factory=list)


def name_problem(name: str, config: TowncrierConfig) -> str | None:
    """Why a fragment's name is not ``<slug>.<type>.md``, or None if it is."""
    parsed = parse_fragment_name(name, config.types)
    if parsed is None:
        if config.strict:
            return (
                "has no towncrier type, and towncrier build stops at it because "
                "[tool.towncrier] sets `ignore`"
            )
        return (
            "has no towncrier type, so towncrier never writes it to CHANGELOG.md "
            "and never deletes it"
        )
    slug, dot, shown = name.removesuffix(".md").rpartition(".")
    if not name.endswith(".md") or not dot or shown != parsed[1]:
        return (
            f"is a name towncrier reads as a `{parsed[1]}` fragment, but it is "
            "not in this repository's form"
        )
    if config.orphan_prefix:
        slug = slug.removeprefix(config.orphan_prefix)
    if not SLUG.fullmatch(slug):
        return (
            f"has the slug {slug!r}; use letters, digits, '.', '_' and '-' "
            "(for example the issue number or branch name)"
        )
    return None


def content_problems(data: bytes) -> tuple[str | None, str | None]:
    """(error, warning) for a fragment's content; either may be None."""
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return (
            "is not UTF-8 text; towncrier would write it to CHANGELOG.md with "
            "replacement characters",
            None,
        )
    if not text.strip():
        return "is empty, so towncrier leaves it out of CHANGELOG.md", None
    first_line = next(line for line in text.splitlines() if line.strip())
    if LIST_MARKER.match(first_line.lstrip()):
        return None, (
            "starts with a list marker; towncrier adds the bullet itself, so it "
            "renders as '- - ...' in CHANGELOG.md"
        )
    return None, None


def check_fragment(
    path: str, data: bytes, config: TowncrierConfig, mode: str = "100644"
) -> tuple[str | None, str | None]:
    """(error, warning) for a file the pull request adds or changes.

    ``mode`` is the file's git mode; ``data`` is not read unless it is a
    regular file.
    """
    directory, _, name = path.rpartition("/")
    if directory != config.directory:
        return (
            f"is not directly in {config.directory}/, so towncrier never reads it",
            None,
        )
    if is_ignored(name, config):
        return None, None
    if mode == SYMLINK_MODE:
        return (
            "is a symbolic link. towncrier follows it when it builds, so a "
            "missing target stops the release; commit the fragment as a file",
            None,
        )
    if mode not in REGULAR_FILE_MODES:
        return "is not a regular file, so towncrier cannot read it", None
    try:
        name.encode("utf-8")
    except UnicodeEncodeError:
        return "has a file name that is not UTF-8", None
    problem = name_problem(name, config)
    if problem:
        types = ", ".join(config.types)
        return f"{problem}. Name it <slug>.<type>.md with a type from {types}.", None
    return content_problems(data)


def fragment_key(name: str, config: TowncrierConfig) -> tuple[str, str, int] | None:
    """The key towncrier files a fragment under; None for an orphan or no type.

    towncrier stops with "multiple files for ..." when two fragments share one.
    """
    parsed = parse_fragment_name(name, config.types)
    if parsed is None or (
        config.orphan_prefix and parsed[0].startswith(config.orphan_prefix)
    ):
        return None
    return parsed


def git(repo: Path, *args: str) -> bytes:
    result = subprocess.run(["git", *args], cwd=repo, capture_output=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"git {' '.join(args)} failed: "
            f"{result.stderr.decode(errors='replace').strip()}"
        )
    return result.stdout


def exists(repo: Path, head: str, path: str) -> bool:
    result = subprocess.run(
        ["git", "cat-file", "-e", f"{head}:{path}"], cwd=repo, capture_output=True
    )
    return result.returncode == 0


def decode_path(raw: bytes) -> str:
    """A git path as text; bytes that are not UTF-8 survive as surrogates."""
    return raw.decode("utf-8", "surrogateescape")


def display(path: str | None) -> str | None:
    """A path that is safe to print."""
    if path is None:
        return None
    return path.encode("utf-8", "surrogateescape").decode("utf-8", "replace")


def changes(
    repo: Path, base: str, head: str, *paths: str
) -> list[tuple[str, str, str]]:
    """(path, status, mode at head) of each change under ``paths``.

    Renames count as a deletion and an addition.
    """
    out = git(
        repo,
        "diff",
        "--raw",
        "-z",
        "--no-renames",
        "--no-abbrev",
        base,
        head,
        "--",
        *paths,
    )
    fields = out.split(b"\0")
    found = []
    for meta, path in zip(fields[::2], fields[1::2]):
        _, mode, _, _, status = meta.decode().split()
        found.append((decode_path(path), status, mode))
    return found


def tree_entries(repo: Path, head: str, directory: str) -> list[tuple[str, str]]:
    """(name, git object type) of each entry directly in ``directory``."""
    out = git(repo, "ls-tree", "-z", head, "--", f"{directory}/")
    entries = []
    for line in filter(None, out.split(b"\0")):
        meta, _, path = line.partition(b"\t")
        entries.append((decode_path(path).rpartition("/")[2], meta.split()[1].decode()))
    return entries


def check(repo: Path, base: str, head: str) -> Report:
    if exists(repo, head, "towncrier.toml"):
        raise ValueError(
            "towncrier.toml exists, and towncrier reads it instead of "
            "pyproject.toml; this check reads only pyproject.toml"
        )
    config = parse_towncrier_config(
        git(repo, "show", f"{head}:pyproject.toml").decode()
    )
    report = Report()
    directory = config.directory
    changed = changes(repo, base, head, f"{directory}/", *RELEASE_TRIGGER_FILES)
    in_directory = {
        path: mode
        for path, status, mode in changed
        if status != "D" and path.startswith(f"{directory}/")
    }
    entries = tree_entries(repo, head, directory)
    keys = {}
    for name, _ in entries:
        if not is_ignored(name, config):
            keys.setdefault(fragment_key(name, config), []).append(name)

    touched_fragment = False
    for path, mode in in_directory.items():
        name = path.rpartition("/")[2]
        data = (
            git(repo, "show", f"{head}:{path}") if mode in REGULAR_FILE_MODES else b""
        )
        error, warning = check_fragment(path, data, config, mode)
        key = fragment_key(name, config)
        if not error and key is not None and len(keys.get(key, [])) > 1:
            others = ", ".join(other for other in keys[key] if other != name)
            error = (
                f"has the same towncrier key as {others} ({key[0]}.{key[1]}), so "
                "towncrier build stops with 'multiple files' and the release fails. "
                "Use a different slug."
            )
        if error:
            report.errors.append((path, error))
        elif warning:
            report.warnings.append((path, warning))
        if path.rpartition("/")[0] != directory or not is_ignored(name, config):
            touched_fragment = True

    for name, _ in entries:
        path = f"{directory}/{name}"
        touched = any(
            other == path or other.startswith(f"{path}/") for other in in_directory
        )
        if touched or is_ignored(name, config):
            continue
        if parse_fragment_name(name, config.types) is None:
            report.warnings.append(
                (
                    path,
                    "has no towncrier type, so towncrier never writes it to "
                    "CHANGELOG.md. This pull request does not change it; rename "
                    "or delete it separately.",
                )
            )

    has_typed_fragment = any(
        kind == "blob"
        and not is_ignored(name, config)
        and parse_fragment_name(name, config.types) is not None
        for name, kind in entries
    )
    if changed and not has_typed_fragment and not report.errors:
        triggers = sorted(
            {
                path if path in RELEASE_TRIGGER_FILES else f"{directory}/"
                for path, _, _ in changed
            }
        )
        report.errors.append(
            (
                None,
                f"This pull request changes {' and '.join(triggers)}, so the "
                "release workflow (.github/workflows/versioning.yaml) runs when "
                "it merges, but the merged tree has no changelog fragment with "
                "a towncrier type. .github/bump_version.py then has nothing to "
                f"release and exits 1. Add {directory}/<slug>.<type>.md.",
            )
        )
    elif not touched_fragment:
        report.warnings.append(
            (
                None,
                f"This pull request adds no changelog fragment to {directory}/. "
                "Every pull request needs one (docs/engineering/skills/github-prs.md).",
            )
        )
    return report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--repo", type=Path, default=Path("."))
    parser.add_argument("--base", default="HEAD^1", help="the pull request's base")
    parser.add_argument("--head", default="HEAD", help="the pull request's merge")
    args = parser.parse_args(argv)
    try:
        report = check(args.repo, args.base, args.head)
    except (KeyError, RuntimeError, ValueError) as error:
        print(annotation("error", None, str(error)))
        return 2
    for path, message in report.warnings:
        print(annotation("warning", display(path), message))
    for path, message in report.errors:
        print(annotation("error", display(path), message))
    if report.errors:
        print(
            f"{len(report.errors)} changelog problem(s). "
            "See docs/engineering/skills/github-prs.md.",
            file=sys.stderr,
        )
        return 1
    print("Changelog fragments OK.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
