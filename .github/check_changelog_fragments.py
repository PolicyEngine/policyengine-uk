"""Fail a pull request that adds a changelog fragment towncrier would drop.

towncrier writes a fragment to CHANGELOG.md only when its name carries a
fragment type configured in pyproject.toml. It never reads, and never
deletes, any other file in the fragment directory, and it leaves an empty
fragment out. Neither tells the author. On 11 October 2026 main held 93 such
files, and every one of their notes was missing from CHANGELOG.md.

The Changelog workflow (.github/workflows/pr_changelog.yaml) runs this on the
pull request's merge commit:

    python .github/check_changelog_fragments.py --base HEAD^1 --head HEAD

Each file the pull request adds or changes in the fragment directory must:

- sit directly in the directory;
- be named ``<slug>.<type>.md``, with a type configured in pyproject.toml at
  ``--head``, and a slug of letters, digits, ``.``, ``_`` and ``-``
  (optionally after towncrier's orphan prefix ``+``);
- be UTF-8 text that is not blank.

Files towncrier ignores (.gitkeep, README and the configured ``ignore``) are
not fragments and pass. Every name this accepts is one towncrier consumes,
with the same type. Deleting a fragment always passes.

It warns, without failing, when the pull request adds no fragment, when a
fragment starts with a list marker (towncrier adds the bullet, so it renders
as ``- - ``), and when the directory already holds files towncrier drops.

Exit status: 0 if every changed fragment passes, 1 if any fails, 2 on a usage
or git error. Standard library only.
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
    is_ignored,
    parse_towncrier_config,
    towncrier_fragment_type,
)

SLUG = re.compile(r"\+?[A-Za-z0-9][A-Za-z0-9._-]*")
LIST_MARKER = re.compile(r"[-*+]\s")


@dataclass
class Report:
    errors: list[tuple[str, str]] = field(default_factory=list)
    warnings: list[tuple[str | None, str]] = field(default_factory=list)


def name_problem(name: str, types) -> str | None:
    """Why a fragment's name is not ``<slug>.<type>.md``, or None if it is."""
    if not name.endswith(".md"):
        return "does not end in .md"
    slug, dot, fragment_type = name.removesuffix(".md").rpartition(".")
    if not dot or fragment_type not in types:
        return (
            "has no towncrier type, so towncrier never writes it to CHANGELOG.md "
            "and never deletes it"
        )
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
        return "is not UTF-8 text, so towncrier cannot read it", None
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
    path: str, data: bytes, config: TowncrierConfig
) -> tuple[str | None, str | None]:
    """(error, warning) for a file the pull request adds or changes."""
    directory, _, name = path.rpartition("/")
    if directory != config.directory:
        return (
            f"is not directly in {config.directory}/, so towncrier never reads it",
            None,
        )
    if is_ignored(name, config):
        return None, None
    problem = name_problem(name, config.types)
    if problem:
        types = ", ".join(config.types)
        return f"{problem}. Name it <slug>.<type>.md with a type from {types}.", None
    return content_problems(data)


def git(repo: Path, *args: str) -> bytes:
    result = subprocess.run(["git", *args], cwd=repo, capture_output=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"git {' '.join(args)} failed: {result.stderr.decode().strip()}"
        )
    return result.stdout


def changed_files(repo: Path, base: str, head: str, directory: str) -> list[str]:
    """Paths under ``directory`` that ``head`` adds or changes relative to ``base``.

    Renames count as a deletion and an addition.
    """
    out = git(
        repo,
        "diff",
        "--name-status",
        "--no-renames",
        "-z",
        base,
        head,
        "--",
        f"{directory}/",
    ).decode()
    fields = out.split("\0")
    paths = []
    for status, path in zip(fields[::2], fields[1::2]):
        if status != "D":
            paths.append(path)
    return paths


def check(repo: Path, base: str, head: str) -> Report:
    config = parse_towncrier_config(
        git(repo, "show", f"{head}:pyproject.toml").decode()
    )
    report = Report()
    changed = changed_files(repo, base, head, config.directory)
    added_fragment = False
    for path in changed:
        error, warning = check_fragment(
            path, git(repo, "show", f"{head}:{path}"), config
        )
        if error:
            report.errors.append((path, error))
        elif warning:
            report.warnings.append((path, warning))
        name = path.rpartition("/")[2]
        if not error and not is_ignored(name, config):
            added_fragment = True
    tree = git(repo, "ls-tree", "--name-only", "-z", head, "--", f"{config.directory}/")
    for path in filter(None, tree.decode().split("\0")):
        name = path.rpartition("/")[2]
        if path in changed or is_ignored(name, config):
            continue
        if towncrier_fragment_type(name, config.types) is None:
            report.warnings.append(
                (
                    path,
                    "has no towncrier type, so towncrier never writes it to "
                    "CHANGELOG.md. This pull request does not change it; rename "
                    "or delete it separately.",
                )
            )
    if not added_fragment:
        report.warnings.append(
            (
                None,
                f"This pull request adds no changelog fragment to {config.directory}/. "
                "Every pull request needs one (docs/engineering/skills/github-prs.md).",
            )
        )
    return report


def escape_data(text: str) -> str:
    return text.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")


def escape_property(text: str) -> str:
    return escape_data(text).replace(":", "%3A").replace(",", "%2C")


def annotation(level: str, path: str | None, message: str) -> str:
    """A GitHub Actions workflow command that annotates the file."""
    location = f" file={escape_property(path)}" if path else ""
    text = f"{path} {message}" if path else message
    return f"::{level}{location}::{escape_data(text)}"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--repo", type=Path, default=Path("."))
    parser.add_argument("--base", default="HEAD^1", help="the pull request's base")
    parser.add_argument("--head", default="HEAD", help="the pull request's merge")
    args = parser.parse_args(argv)
    try:
        report = check(args.repo, args.base, args.head)
    except (KeyError, RuntimeError, ValueError) as error:
        print(f"::error::{escape_data(str(error))}")
        return 2
    for path, message in report.warnings:
        print(annotation("warning", path, message))
    for path, message in report.errors:
        print(annotation("error", path, message))
    if report.errors:
        print(
            f"{len(report.errors)} changelog fragment(s) would be left out of "
            "CHANGELOG.md. See docs/engineering/skills/github-prs.md.",
            file=sys.stderr,
        )
        return 1
    print("Changelog fragments OK.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
