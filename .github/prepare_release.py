"""Make the release's version commit on the latest main, and push it.

The release workflow (.github/workflows/versioning.yaml) runs this once per
release, one run at a time:

    python3 .github/prepare_release.py --towncrier "uvx --from towncrier==X towncrier" \\
        --github-output "$GITHUB_OUTPUT"

Each attempt fetches main and starts from its tip. If that tip is already a
version commit, or ``changelog.d`` has no fragments, there is nothing to
release. Otherwise it bumps the version
(.github/bump_version.py), builds the changelog (towncrier), commits that as
"Update package version", checks the commit changes nothing else, and pushes
it to main. If main moved in the meantime the push is rejected; the next
attempt starts again from the new tip, so the version and changelog always
describe the commit they sit on. It never force-pushes.

It writes ``committed``, ``pushed``, ``version``, ``sha`` and ``base`` (the
tip the commit was made on) as ``key=value`` lines to stdout and, with
``--github-output``, appends them to that file.

Before this, the workflow committed on the commit that triggered it and
failed when main had moved: 20 failed runs in two weeks to 11 October 2026.

Standard library only.
"""

import argparse
import importlib.util
import os
import re
import shlex
import subprocess
import sys
import time
import tomllib
from pathlib import Path

COMMIT_MESSAGE = "Update package version"
BOT_NAME = "github-actions[bot]"
BOT_EMAIL = "41898282+github-actions[bot]@users.noreply.github.com"
VERSION_LINE = re.compile(r'^version\s*=\s*"[0-9]+\.[0-9]+\.[0-9]+"$')


class ReleaseError(Exception):
    """The release cannot be prepared; the message says why."""


class Git:
    def __init__(self, repo: Path):
        self.repo = repo

    def run(self, *args: str, check: bool = True) -> subprocess.CompletedProcess:
        # The bot is the author and committer whatever the environment says;
        # GIT_AUTHOR_* variables would override user.name and user.email.
        env = {
            **os.environ,
            "GIT_AUTHOR_NAME": BOT_NAME,
            "GIT_AUTHOR_EMAIL": BOT_EMAIL,
            "GIT_COMMITTER_NAME": BOT_NAME,
            "GIT_COMMITTER_EMAIL": BOT_EMAIL,
        }
        result = subprocess.run(
            ["git", *args],
            cwd=self.repo,
            capture_output=True,
            text=True,
            env=env,
        )
        if check and result.returncode != 0:
            raise ReleaseError(
                f"git {' '.join(args)} failed: {result.stderr.strip() or result.stdout.strip()}"
            )
        return result

    def out(self, *args: str) -> str:
        return self.run(*args).stdout.strip()


def find_fragments(repo: Path) -> list[str]:
    """The changelog fragments, as the tip's own .github/bump_version.py counts them.

    A bump_version.py that classifies fragments (load_towncrier_config and
    classify_fragments, from #2324) counts only those towncrier consumes, so
    a file without a towncrier type is not something to release. An older
    one counts every file but .gitkeep, and so does this.
    """
    spec = importlib.util.spec_from_file_location(
        "bump_version", repo / ".github" / "bump_version.py"
    )
    bump = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bump)
    if hasattr(bump, "load_towncrier_config") and hasattr(bump, "classify_fragments"):
        try:
            config = bump.load_towncrier_config(repo / "pyproject.toml")
        except ValueError as error:
            raise ReleaseError(f"cannot read the towncrier settings: {error}") from None
        directory = repo / config.directory
        if not directory.is_dir():
            return []
        typed, _ = bump.classify_fragments(directory, config)
        return sorted(path.name for path, _ in typed)
    directory = repo / "changelog.d"
    if not directory.is_dir():
        return []
    return sorted(
        path.name
        for path in directory.iterdir()
        if path.is_file() and path.name != ".gitkeep"
    )


def parse_version(text: str) -> tuple[int, int, int]:
    version = tomllib.loads(text)["project"]["version"]
    parts = version.split(".")
    if len(parts) != 3 or not all(part.isdigit() for part in parts):
        raise ReleaseError(f"version {version!r} is not X.Y.Z")
    return tuple(int(part) for part in parts)


def version_text(version: tuple[int, int, int]) -> str:
    return ".".join(map(str, version))


def check_release_diff(git: Git, base: str, head: str) -> None:
    """Fail unless ``head`` only versions ``base``.

    The commit may change only the version line of pyproject.toml and
    CHANGELOG.md, and delete changelog fragments; and the version must rise.
    """
    problems = []
    for line in git.out(
        "diff", "--name-status", "--no-renames", base, head
    ).splitlines():
        status, _, path = line.partition("\t")
        if (status, path) in {("M", "pyproject.toml"), ("M", "CHANGELOG.md")}:
            continue
        if status == "D" and path.startswith("changelog.d/") and path.count("/") == 1:
            continue
        problems.append(f"{status} {path}")
    changed = [
        line[1:]
        for line in git.out(
            "diff", "--unified=0", base, head, "--", "pyproject.toml"
        ).splitlines()
        if line[:1] in "+-" and not line.startswith(("+++", "---"))
    ]
    if len(changed) != 2 or not all(VERSION_LINE.match(line) for line in changed):
        problems.append(f"pyproject.toml changes more than the version: {changed}")
    old = parse_version(git.out("show", f"{base}:pyproject.toml"))
    new = parse_version(git.out("show", f"{head}:pyproject.toml"))
    if new <= old:
        problems.append(
            f"the version does not rise: {version_text(old)} -> {version_text(new)}"
        )
    if problems:
        raise ReleaseError(
            "the version commit changes more than versioning:\n  "
            + "\n  ".join(problems)
        )


def make_version_commit(git: Git, python: str, towncrier: list[str]) -> str:
    """Bump, build the changelog and commit; returns the new version."""
    subprocess.run([python, ".github/bump_version.py"], cwd=git.repo, check=True)
    version = version_text(parse_version((git.repo / "pyproject.toml").read_text()))
    subprocess.run(
        [*towncrier, "build", "--yes", "--version", version], cwd=git.repo, check=True
    )
    # Only what versioning changes; the guard below checks nothing else did.
    git.run("add", "--all", "--", "pyproject.toml", "CHANGELOG.md", "changelog.d")
    git.run("commit", "--no-verify", "-m", COMMIT_MESSAGE)
    return version


def prepare_release(
    repo: Path,
    remote: str = "origin",
    branch: str = "main",
    max_attempts: int = 5,
    push: bool = True,
    python: str = sys.executable,
    towncrier: list[str] = ("towncrier",),
    sleep=time.sleep,
    before_push=None,
    git=None,
) -> dict[str, str]:
    """Version the tip of ``remote/branch`` and push it; see the module docs.

    ``before_push`` is called just before each push, and ``git`` replaces the
    git runner, for tests.
    """
    git = git or Git(repo)
    for attempt in range(1, max_attempts + 1):
        git.run("fetch", "--no-tags", remote, branch)
        git.run("checkout", "--force", "--detach", "FETCH_HEAD")
        git.run("reset", "--hard", "FETCH_HEAD")
        base = git.out("rev-parse", "HEAD")
        current = version_text(parse_version((repo / "pyproject.toml").read_text()))
        fragments = find_fragments(repo)
        # A run that was queued behind another finds main already versioned:
        # the earlier run's commit took this run's changes too.
        already_versioned = git.out("log", "-1", "--format=%s") == COMMIT_MESSAGE
        if already_versioned or not fragments:
            reason = (
                "its tip is already a version commit"
                if already_versioned
                else "it has no changelog fragments"
            )
            print(f"Nothing to release: {branch} {reason}.", file=sys.stderr)
            return {
                "committed": "false",
                "pushed": "false",
                "version": current,
                "sha": base,
                "base": base,
            }
        print(
            f"Attempt {attempt}: versioning {base} ({len(fragments)} fragments)",
            file=sys.stderr,
        )
        version = make_version_commit(git, python, list(towncrier))
        head = git.out("rev-parse", "HEAD")
        check_release_diff(git, base, head)
        result = {
            "committed": "true",
            "pushed": "false",
            "version": version,
            "sha": head,
            "base": base,
        }
        if not push:
            return result
        if before_push is not None:
            before_push()
        pushed = git.run("push", remote, f"HEAD:refs/heads/{branch}", check=False)
        if pushed.returncode == 0:
            result["pushed"] = "true"
            print(f"Pushed {version} as {head} on {base}", file=sys.stderr)
            return result
        # A race: main moved after the fetch. Anything else is a real failure.
        git.run("fetch", "--no-tags", remote, branch)
        tip = git.out("rev-parse", "FETCH_HEAD")
        if tip == head:
            # The push landed although git reported a failure (say, the
            # connection dropped after the server accepted it). Retrying
            # would find a versioned tip and release nothing.
            result["pushed"] = "true"
            print(
                f"Pushed {version} as {head} on {base} (git reported an error, "
                "but the branch is at the version commit)",
                file=sys.stderr,
            )
            return result
        if tip == base:
            raise ReleaseError(
                f"pushing the version commit failed, and {branch} has not moved: "
                f"{pushed.stderr.strip()}"
            )
        delay = min(30, 2**attempt)
        print(
            f"{branch} moved from {base} to {tip}; versioning again in {delay}s",
            file=sys.stderr,
        )
        sleep(delay)
    raise ReleaseError(f"{branch} kept moving; gave up after {max_attempts} attempts")


def verify_version_commit(repo: Path, sha: str) -> str:
    """Check ``sha`` is a version commit; return its version.

    For releasing an existing commit (the release workflow's release-sha
    input and its re-run path). The subject alone could be copied by any
    commit, so it must also have one parent and change only what versioning
    changes (check_release_diff). Such a commit's code is its parent's, which
    is on main. The author is not checked: version commits made before this
    script were authored by whoever merged the pull request.
    """
    git = Git(repo)
    if not re.fullmatch(r"[0-9a-f]{40}", sha):
        raise ReleaseError(f"{sha!r} is not a full 40-character commit SHA")
    fields = git.out("log", "-1", "--format=%P%n%s", sha)
    parents, subject = (fields.split("\n") + ["", ""])[:2]
    problems = []
    if len(parents.split()) != 1:
        problems.append(f"it has {len(parents.split())} parents, not one")
    if subject != COMMIT_MESSAGE:
        problems.append(f"its subject is {subject!r}")
    if problems:
        raise ReleaseError(f"{sha} is not a version commit: " + "; ".join(problems))
    check_release_diff(git, parents.strip(), sha)
    return version_text(parse_version(git.out("show", f"{sha}:pyproject.toml")))


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--repo", type=Path, default=Path("."))
    parser.add_argument("--remote", default="origin")
    parser.add_argument("--branch", default="main")
    parser.add_argument("--max-attempts", type=int, default=5)
    parser.add_argument(
        "--no-push", action="store_true", help="make the commit but do not push it"
    )
    parser.add_argument("--github-output", type=Path)
    parser.add_argument("--towncrier", default="towncrier")
    parser.add_argument("--python", default=sys.executable)
    parser.add_argument(
        "--verify",
        metavar="SHA",
        help="only check that SHA is a version commit this script made",
    )
    args = parser.parse_args(argv)
    if args.verify:
        try:
            version = verify_version_commit(args.repo.resolve(), args.verify)
        except (ReleaseError, ValueError, KeyError, tomllib.TOMLDecodeError) as error:
            print(f"Cannot release it: {error}", file=sys.stderr)
            return 1
        print(f"version={version}")
        return 0
    try:
        result = prepare_release(
            args.repo.resolve(),
            remote=args.remote,
            branch=args.branch,
            max_attempts=args.max_attempts,
            push=not args.no_push,
            python=args.python,
            towncrier=shlex.split(args.towncrier),
        )
    except (ReleaseError, subprocess.CalledProcessError, OSError) as error:
        print(f"Cannot prepare the release: {error}", file=sys.stderr)
        return 1
    lines = "".join(f"{key}={value}\n" for key, value in result.items())
    print(lines, end="")
    if args.github_output:
        with open(args.github_output, "a", encoding="utf-8") as file:
            file.write(lines)
    return 0


if __name__ == "__main__":
    sys.exit(main())
