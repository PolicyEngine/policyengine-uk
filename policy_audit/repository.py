"""Resolve and check out exact PolicyEngine UK releases."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
import re
import subprocess
import tomllib

from policy_audit.errors import PolicyAuditError


@dataclass(frozen=True)
class ReleaseCheckout:
    """An isolated checkout of one package release."""

    version: str
    tag: str
    root: Path
    repository: Path


def run_git(repository: Path, *arguments: str) -> str:
    """Run Git and return stripped standard output."""

    result = subprocess.run(
        ["git", "-C", str(repository), *arguments],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode:
        detail = result.stderr.strip() or result.stdout.strip()
        raise PolicyAuditError(f"Git command failed: {detail}")
    return result.stdout.strip()


def find_repository(start: Path) -> Path:
    """Return the Git repository containing ``start``."""

    output = run_git(start.resolve(), "rev-parse", "--show-toplevel")
    return Path(output)


def resolve_release_tag(repository: Path, version: str) -> str:
    """Resolve a version to an exact local release tag."""

    for candidate in (version, f"v{version}"):
        result = subprocess.run(
            [
                "git",
                "-C",
                str(repository),
                "rev-parse",
                "--verify",
                "--quiet",
                f"refs/tags/{candidate}^{{commit}}",
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            return candidate
    raise PolicyAuditError(
        f"No local release tag matches policyengine-uk {version}. "
        "Fetch the release tag and try again."
    )


def _package_version(checkout: Path) -> str:
    pyproject = checkout / "pyproject.toml"
    if not pyproject.exists():
        raise PolicyAuditError(f"Release checkout has no pyproject.toml: {checkout}")
    with pyproject.open("rb") as stream:
        data = tomllib.load(stream)
    try:
        return str(data["project"]["version"])
    except KeyError as error:
        raise PolicyAuditError("pyproject.toml has no project.version") from error


def prepare_release_checkout(
    repository: Path,
    version: str,
    state_directory: Path,
) -> ReleaseCheckout:
    """Create or reuse an isolated worktree for an exact release tag."""

    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", version):
        raise PolicyAuditError(f"Unsafe release version: {version}")
    repository = find_repository(repository)
    tag = resolve_release_tag(repository, version)
    checkout = state_directory.resolve() / "worktrees" / version
    if not checkout.exists():
        checkout.parent.mkdir(parents=True, exist_ok=True)
        run_git(
            repository,
            "worktree",
            "add",
            "--detach",
            str(checkout),
            tag,
        )
    expected_revision = run_git(repository, "rev-parse", f"{tag}^{{commit}}")
    actual_revision = run_git(checkout, "rev-parse", "HEAD")
    if actual_revision != expected_revision:
        raise PolicyAuditError(
            f"Existing worktree {checkout} is not checked out at release {version}."
        )
    if run_git(checkout, "status", "--porcelain"):
        raise PolicyAuditError(
            f"Release worktree contains local changes and cannot be audited: {checkout}"
        )
    actual_version = _package_version(checkout)
    if actual_version != version:
        raise PolicyAuditError(
            f"Tag {tag} contains package version {actual_version}, not {version}."
        )
    return ReleaseCheckout(
        version=version,
        tag=tag,
        root=checkout,
        repository=repository,
    )


def last_modified_date(
    release: ReleaseCheckout,
    source_paths: list[str],
) -> str | None:
    """Return the latest source-change date at or before the release."""

    dates: list[date] = []
    for source_path in source_paths:
        result = subprocess.run(
            [
                "git",
                "-C",
                str(release.repository),
                "log",
                "-1",
                "--follow",
                "--format=%cs",
                release.tag,
                "--",
                source_path,
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode:
            raise PolicyAuditError(
                f"Could not read history for {source_path}: {result.stderr.strip()}"
            )
        value = result.stdout.strip()
        if value:
            dates.append(date.fromisoformat(value))
    return max(dates).isoformat() if dates else None


def source_last_modified_dates(release: ReleaseCheckout) -> dict[str, str]:
    """Return last-change dates for model source paths in one Git traversal."""

    output = run_git(
        release.repository,
        "log",
        "--format=@@%cs",
        "--name-only",
        release.tag,
        "--",
        "policyengine_uk/parameters",
        "policyengine_uk/variables",
    )
    current_date: str | None = None
    result: dict[str, str] = {}
    for raw_line in output.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("@@"):
            current_date = line.removeprefix("@@")
            continue
        if current_date is not None and line not in result:
            result[line] = current_date
    return result
