"""Infer semver bump from towncrier fragment types and update version.

Only the fragments towncrier consumes count: files in the fragment directory
whose names carry a fragment type configured under ``[tool.towncrier]`` in
pyproject.toml, as towncrier parses them. towncrier never writes any other
file there to CHANGELOG.md and never deletes it, so such a file cannot justify
a release. This script warns about each one and ignores it.
``.github/check_changelog_fragments.py`` uses the same rules to reject them in
pull requests.

Standard library only.
"""

import fnmatch
import re
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path

# towncrier's fragment types when [tool.towncrier] configures none
# (towncrier._settings.fragment_types.DefaultFragmentTypesLoader).
TOWNCRIER_DEFAULT_TYPES = ("feature", "bugfix", "doc", "removal", "misc")
# Names towncrier always skips in the fragment directory
# (towncrier._builder.find_fragments), besides the configured `ignore`.
TOWNCRIER_IGNORED_NAMES = (
    ".gitignore",
    ".gitkeep",
    ".keep",
    "readme",
    "readme.md",
    "readme.rst",
)

# A template given as "package:resource" (towncrier._settings.load).
TOWNCRIER_RESOURCE_TEMPLATE = re.compile(r"[-\w.]+:[-\w.]+$")

MAJOR_TYPES = {"breaking"}
MINOR_TYPES = {"added", "removed"}


@dataclass(frozen=True)
class TowncrierConfig:
    """The parts of [tool.towncrier] that decide which files are fragments."""

    directory: str
    types: tuple[str, ...]
    ignore: tuple[str, ...]
    orphan_prefix: str = "+"


def parse_towncrier_config(pyproject_text: str) -> TowncrierConfig:
    """Read [tool.towncrier] from pyproject.toml text the way towncrier does."""
    config = tomllib.loads(pyproject_text).get("tool", {}).get("towncrier")
    if config is None:
        raise ValueError("pyproject.toml has no [tool.towncrier] table")
    if config.get("fragment"):
        types = tuple(sorted(config["fragment"]))
    elif config.get("type"):
        types = tuple(
            entry.get("directory", entry["name"].lower()) for entry in config["type"]
        )
    else:
        types = TOWNCRIER_DEFAULT_TYPES
    directory = config.get("directory")
    if directory is None:
        directory = str(
            Path(config.get("package_dir", ".")) / config["package"] / "newsfragments"
        )
    ignore = [name.lower() for name in TOWNCRIER_IGNORED_NAMES]
    ignore += [pattern.lower() for pattern in config.get("ignore") or []]
    template = config.get("template", "towncrier:default")
    if not TOWNCRIER_RESOURCE_TEMPLATE.match(template):
        # A template file in the repository; towncrier does not lower-case it.
        ignore.append(Path(template).name)
    return TowncrierConfig(
        directory=Path(directory).as_posix(),
        types=types,
        ignore=tuple(ignore),
        orphan_prefix=config.get("orphan_prefix", "+"),
    )


def load_towncrier_config(pyproject_path: Path) -> TowncrierConfig:
    return parse_towncrier_config(pyproject_path.read_text())


def is_ignored(name: str, config: TowncrierConfig) -> bool:
    """Whether towncrier skips this name in the fragment directory."""
    return any(fnmatch.fnmatch(name.lower(), pattern) for pattern in config.ignore)


def parse_fragment_name(name: str, types) -> tuple[str, str, int] | None:
    """(issue, type, counter) as towncrier reads a fragment's name, or None.

    Mirrors towncrier._builder.parse_newfragment_basename: the type is the
    last dot-separated part, after the first, that is a configured type; the
    parts before it are the issue (an all-digit issue loses leading zeros);
    a number right after it is the counter.
    """
    parts = name.split(".")
    for i in reversed(range(1, len(parts))):
        if parts[i] in types:
            issue = ".".join(parts[:i]).strip()
            if issue.isdigit():
                issue = str(int(issue))
            counter = 0
            if len(parts) > i + 1 and parts[i + 1].isdigit():
                counter = int(parts[i + 1])
            return issue, parts[i], counter
    return None


def towncrier_fragment_type(name: str, types) -> str | None:
    """The type towncrier reads from a fragment's name, or None if it has none."""
    parsed = parse_fragment_name(name, types)
    return parsed[1] if parsed else None


def classify_fragments(
    changelog_dir: Path, config: TowncrierConfig
) -> tuple[list[tuple[Path, str]], list[Path]]:
    """Split the directory's files into (fragment, type) pairs and untyped files.

    Files towncrier ignores (.gitkeep, README and the configured `ignore`)
    are in neither list.
    """
    typed, untyped = [], []
    for path in sorted(changelog_dir.iterdir()):
        if not path.is_file() or is_ignored(path.name, config):
            continue
        fragment_type = towncrier_fragment_type(path.name, config.types)
        if fragment_type is None:
            untyped.append(path)
        else:
            typed.append((path, fragment_type))
    return typed, untyped


def bump_for_types(fragment_types) -> str:
    fragment_types = set(fragment_types)
    if fragment_types & MAJOR_TYPES:
        return "major"
    if fragment_types & MINOR_TYPES:
        return "minor"
    return "patch"


def get_current_version(pyproject_path: Path) -> str:
    text = pyproject_path.read_text()
    match = re.search(r'^version\s*=\s*"(\d+\.\d+\.\d+)"', text, re.MULTILINE)
    if not match:
        print(
            "Could not find version in pyproject.toml",
            file=sys.stderr,
        )
        sys.exit(1)
    return match.group(1)


def infer_bump(changelog_dir: Path, config: TowncrierConfig) -> str:
    typed, untyped = classify_fragments(changelog_dir, config)
    for path in untyped:
        relative = f"{config.directory}/{path.name}"
        print(
            f"::warning file={relative}::{relative} has no towncrier type, so "
            "towncrier leaves it out of CHANGELOG.md and this release ignores it. "
            f"Fragments are named <slug>.<type>.md with a type from "
            f"{', '.join(config.types)}."
        )
    if not typed:
        print(
            f"No changelog fragments with a towncrier type in {config.directory}",
            file=sys.stderr,
        )
        sys.exit(1)
    return bump_for_types(fragment_type for _, fragment_type in typed)


def bump_version(version: str, bump: str) -> str:
    major, minor, patch = (int(x) for x in version.split("."))
    if bump == "major":
        return f"{major + 1}.0.0"
    elif bump == "minor":
        return f"{major}.{minor + 1}.0"
    else:
        return f"{major}.{minor}.{patch + 1}"


def update_file(path: Path, old_version: str, new_version: str):
    text = path.read_text()
    updated = text.replace(
        f'version = "{old_version}"',
        f'version = "{new_version}"',
    )
    if updated != text:
        path.write_text(updated)
        print(f"  Updated {path}")


def main():
    root = Path(__file__).resolve().parent.parent
    pyproject = root / "pyproject.toml"
    config = load_towncrier_config(pyproject)

    current = get_current_version(pyproject)
    bump = infer_bump(root / config.directory, config)
    new = bump_version(current, bump)

    print(f"Version: {current} -> {new} ({bump})")

    update_file(pyproject, current, new)


if __name__ == "__main__":
    main()
