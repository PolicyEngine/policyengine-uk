"""Infer semver bump from towncrier fragment types and update version."""

import re
import sys
import tomllib
from pathlib import Path


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


def infer_bump(changelog_dir: Path) -> str:
    fragments = [
        f for f in changelog_dir.iterdir() if f.is_file() and f.name != ".gitkeep"
    ]
    if not fragments:
        print("No changelog fragments found", file=sys.stderr)
        sys.exit(1)

    categories = {f.suffix.lstrip(".") for f in fragments}
    for f in fragments:
        parts = f.stem.split(".")
        if len(parts) >= 2:
            categories.add(parts[-1])

    if "breaking" in categories:
        return "major"
    if "added" in categories or "removed" in categories:
        return "minor"
    return "patch"


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


def get_project_name(pyproject_path: Path) -> str:
    """The project name, normalised the way uv writes it in uv.lock."""
    name = tomllib.loads(pyproject_path.read_text())["project"]["name"]
    return re.sub(r"[-_.]+", "-", name).lower()


def set_lock_version(text: str, package: str, new_version: str) -> str:
    """Set the version of the project's own entry in uv.lock text.

    CI installs with `uv sync --locked`, which refuses a lock whose entry for
    the project disagrees with pyproject.toml, so the two must move together.
    Only that entry changes: a dependency can share the old version string.
    """
    pattern = re.compile(
        rf'^(\[\[package\]\]\nname = "{re.escape(package)}"\nversion = ")[^"\n]*(")$',
        re.MULTILINE,
    )
    updated, count = pattern.subn(rf"\g<1>{new_version}\g<2>", text)
    if count != 1:
        raise ValueError(f"Expected one {package} entry in uv.lock, found {count}")
    return updated


def update_lock(path: Path, package: str, new_version: str):
    if not path.exists():
        return
    text = path.read_text()
    try:
        updated = set_lock_version(text, package, new_version)
    except ValueError as error:
        print(error, file=sys.stderr)
        sys.exit(1)
    if updated != text:
        path.write_text(updated)
        print(f"  Updated {path}")


def main():
    root = Path(__file__).resolve().parent.parent
    pyproject = root / "pyproject.toml"
    changelog_dir = root / "changelog.d"

    current = get_current_version(pyproject)
    bump = infer_bump(changelog_dir)
    new = bump_version(current, bump)

    print(f"Version: {current} -> {new} ({bump})")

    update_file(pyproject, current, new)
    update_lock(root / "uv.lock", get_project_name(pyproject), new)


if __name__ == "__main__":
    main()
