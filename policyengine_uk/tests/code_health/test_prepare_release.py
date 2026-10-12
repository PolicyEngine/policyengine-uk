"""The version commit only ever extends main, and the tag marks the release.

``.github/prepare_release.py`` makes the release workflow's version commit and
``.github/publish-git-tag.sh`` tags it. These tests run both against real git
repositories (a bare remote and clones in a temporary directory), with a
stand-in for towncrier, and hold them to:

1. With no changelog fragments, or when main's tip is already a version
   commit (a run queued behind another), nothing is committed or pushed.
   Fragments are counted as this tree's bump_version.py counts them: only
   those towncrier consumes once #2324 is in, every file before.
2. After a release, the remote branch's tip is the version commit, whose only
   parent is the tip the run fetched: history is extended, never rewritten.
   The commit deletes the fragments, adds them to the changelog and raises
   the version, and changes nothing else.
3. Race: when another commit reaches main after the run fetched it, the run
   tries again on the new tip. The version and changelog then describe the
   new tip, and the other commit stays in history.
4. The guard refuses a version commit that changes another file, adds a
   file, changes more of pyproject.toml than the version, or does not raise
   the version.
5. A push rejected for any reason other than main moving fails at once.
6. ``--github-output`` appends ``key=value`` lines and keeps what was there.
7. The tag script tags the given commit, not HEAD, with an annotated tag;
   a re-run is a no-op; it never moves an existing tag; it rejects a bad
   version or commit; it fails, not passes, when it cannot list origin's
   tags.
8. A push that landed although git reported a failure counts as pushed, so
   the release is not lost to a retry that finds a versioned tip.
9. --verify accepts exactly a commit with one parent, the version subject
   and only versioning changes, whoever wrote it, and returns its version.
"""

import importlib.util
import os
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
GITHUB_DIR = REPO_ROOT / ".github"
SCRIPT = GITHUB_DIR / "prepare_release.py"
TAG_SCRIPT = GITHUB_DIR / "publish-git-tag.sh"

if not SCRIPT.exists():
    pytest.skip(
        "the .github folder is not part of an installed package",
        allow_module_level=True,
    )

_spec = importlib.util.spec_from_file_location("prepare_release", SCRIPT)
prepare = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(prepare)

GIT_ENV = {
    "GIT_CONFIG_GLOBAL": os.devnull,
    "GIT_CONFIG_NOSYSTEM": "1",
    "GIT_AUTHOR_NAME": "t",
    "GIT_AUTHOR_EMAIL": "t@example.com",
    "GIT_COMMITTER_NAME": "t",
    "GIT_COMMITTER_EMAIL": "t@example.com",
}

_bump_spec = importlib.util.spec_from_file_location(
    "bump_version_under_test", GITHUB_DIR / "bump_version.py"
)
_bump = importlib.util.module_from_spec(_bump_spec)
_bump_spec.loader.exec_module(_bump)
# Whether this tree's bump_version.py counts only the fragments towncrier
# consumes (#2324) or every file. prepare_release.py follows it either way.
TYPED_FRAGMENTS_ONLY = hasattr(_bump, "classify_fragments")

# Stands in for towncrier: moves the fragments towncrier consumes (the typed
# ones, where bump_version.py can tell) into CHANGELOG.md.
FAKE_TOWNCRIER = """
import pathlib, subprocess, sys
sys.dont_write_bytecode = True  # leave no __pycache__ in the checkout
sys.path.insert(0, ".github")
import bump_version
version = sys.argv[sys.argv.index("--version") + 1]
if hasattr(bump_version, "classify_fragments"):
    config = bump_version.load_towncrier_config(pathlib.Path("pyproject.toml"))
    typed, _ = bump_version.classify_fragments(pathlib.Path(config.directory), config)
    fragments = sorted(path for path, _ in typed)
else:
    fragments = sorted(
        p for p in pathlib.Path("changelog.d").iterdir()
        if p.name != ".gitkeep" and p.name.count(".") >= 2
    )
entries = "".join(p.read_text() for p in fragments)
changelog = pathlib.Path("CHANGELOG.md")
changelog.write_text(f"## [{version}]\\n\\n{entries}\\n" + changelog.read_text())
if fragments:
    subprocess.run(["git", "rm", "-q", *map(str, fragments)], check=True)
"""


@pytest.fixture(autouse=True)
def git_env(monkeypatch):
    for name, value in GIT_ENV.items():
        monkeypatch.setenv(name, value)


def git(repo, *args):
    return subprocess.run(
        ["git", "-C", str(repo), *args], check=True, capture_output=True, text=True
    ).stdout.strip()


@pytest.fixture
def remote(tmp_path):
    """A bare remote whose main has version 1.2.3 and one fragment."""
    seed = tmp_path / "seed"
    seed.mkdir()
    git(seed, "init", "-q", "-b", "main")
    (seed / ".github").mkdir()
    shutil.copy(GITHUB_DIR / "bump_version.py", seed / ".github" / "bump_version.py")
    (seed / "pyproject.toml").write_text(
        '[project]\nname = "demo"\nversion = "1.2.3"\n\n[tool.x]\nkeep = 1\n\n'
        '[tool.towncrier]\ndirectory = "changelog.d"\n\n'
        '[[tool.towncrier.type]]\ndirectory = "added"\nname = "Added"\n\n'
        '[[tool.towncrier.type]]\ndirectory = "fixed"\nname = "Fixed"\n'
    )
    (seed / "CHANGELOG.md").write_text("## [1.2.3]\n")
    (seed / "changelog.d").mkdir()
    (seed / "changelog.d" / ".gitkeep").write_text("")
    (seed / "changelog.d" / "one.fixed.md").write_text("- Fixed one.\n")
    (seed / "towncrier.py").write_text(FAKE_TOWNCRIER)
    git(seed, "add", "-A")
    git(seed, "commit", "-qm", "seed")
    bare = tmp_path / "remote.git"
    git(tmp_path, "clone", "-q", "--bare", str(seed), str(bare))
    return bare


def clone(remote, path):
    git(remote.parent, "clone", "-q", str(remote), str(path))
    return path


def run(repo, **kwargs):
    kwargs.setdefault("towncrier", [sys.executable, "towncrier.py"])
    kwargs.setdefault("sleep", lambda seconds: None)
    return prepare.prepare_release(repo, **kwargs)


def version_at(repo, ref):
    return tomllib.loads(git(repo, "show", f"{ref}:pyproject.toml"))["project"][
        "version"
    ]


def test_no_fragments_means_no_release(remote, tmp_path):
    work = clone(remote, tmp_path / "work")
    git(work, "rm", "-q", "changelog.d/one.fixed.md")
    git(work, "commit", "-qm", "no fragments")
    git(work, "push", "-q", "origin", "HEAD:main")
    tip = git(remote, "rev-parse", "main")

    result = run(work)

    assert result["committed"] == "false" and result["pushed"] == "false"
    assert result["sha"] == tip == git(remote, "rev-parse", "main")
    assert result["version"] == "1.2.3"


def test_untyped_files_alone_mean_no_release(remote, tmp_path):
    work = clone(remote, tmp_path / "work")
    git(work, "rm", "-q", "changelog.d/one.fixed.md")
    (work / "changelog.d" / "1005.md").write_text("Untyped.\n")
    git(work, "add", "-A")
    git(work, "commit", "-qm", "only an untyped file")
    git(work, "push", "-q", "origin", "HEAD:main")
    tip = git(remote, "rev-parse", "main")

    result = run(work)

    if TYPED_FRAGMENTS_ONLY:
        # towncrier would consume nothing, so there is nothing to release.
        assert result["committed"] == result["pushed"] == "false"
        assert result["sha"] == tip == git(remote, "rev-parse", "main")
        assert result["version"] == "1.2.3"
    else:
        # An older bump_version.py counts the untyped file: a patch release
        # with an empty changelog entry, as the old workflow made.
        assert result["committed"] == result["pushed"] == "true"
        assert result["version"] == "1.2.4"


def test_a_versioned_tip_means_no_release(remote, tmp_path):
    work = clone(remote, tmp_path / "work")
    first = run(work)
    assert first["pushed"] == "true"
    # A new merge with a fragment, and a file towncrier does not consume,
    # which the release leaves behind.
    other = clone(remote, tmp_path / "other")
    (other / "changelog.d" / "two.fixed.md").write_text("Fixed two.\n")
    (other / "changelog.d" / "1005.md").write_text("Untyped.\n")
    git(other, "add", "-A")
    git(other, "commit", "-qm", "a merge with a fragment")
    git(other, "push", "-q", "origin", "HEAD:main")
    second = run(work)
    assert second["pushed"] == "true"  # a new merge: released as a patch
    assert second["version"] == "1.2.5"

    third = run(work)

    assert third["committed"] == third["pushed"] == "false"
    assert third["sha"] == second["sha"] == git(remote, "rev-parse", "main")
    assert third["version"] == "1.2.5"


def test_a_release_extends_main_by_one_version_commit(remote, tmp_path):
    work = clone(remote, tmp_path / "work")
    before = git(remote, "rev-parse", "main")

    result = run(work)

    assert result["committed"] == result["pushed"] == "true"
    assert result["version"] == "1.2.4"  # a .fixed fragment is a patch
    tip = git(remote, "rev-parse", "main")
    assert result["sha"] == tip and result["base"] == before
    assert git(remote, "rev-list", "--parents", "-n", "1", tip).split() == [tip, before]
    assert git(remote, "log", "-1", "--format=%s", tip) == "Update package version"
    assert git(remote, "log", "-1", "--format=%an <%ae>", tip) == (
        f"{prepare.BOT_NAME} <{prepare.BOT_EMAIL}>"
    )
    assert sorted(git(remote, "diff", "--name-status", before, tip).splitlines()) == [
        "D\tchangelog.d/one.fixed.md",
        "M\tCHANGELOG.md",
        "M\tpyproject.toml",
    ]
    assert version_at(remote, tip) == "1.2.4"
    assert "- Fixed one." in git(remote, "show", f"{tip}:CHANGELOG.md")
    # Reading the tip's bump_version.py leaves nothing behind in the checkout.
    assert git(work, "status", "--porcelain", "--untracked-files=all") == ""
    assert not (work / ".github" / "__pycache__").exists()


def test_a_race_versions_the_new_tip(remote, tmp_path):
    work = clone(remote, tmp_path / "work")
    other = clone(remote, tmp_path / "other")
    raced = []

    def someone_merges_first():
        if raced:
            return
        (other / "changelog.d" / "two.added.md").write_text("- Added two.\n")
        (other / "feature.txt").write_text("feature\n")
        git(other, "add", "-A")
        git(other, "commit", "-qm", "a merge lands")
        git(other, "push", "-q", "origin", "HEAD:main")
        raced.append(git(other, "rev-parse", "HEAD"))

    result = run(work, before_push=someone_merges_first)

    [merge] = raced
    tip = git(remote, "rev-parse", "main")
    assert result["sha"] == tip and result["base"] == merge
    assert git(remote, "rev-list", "--parents", "-n", "1", tip).split() == [tip, merge]
    # Both fragments, and an added one makes it a minor release.
    assert result["version"] == version_at(remote, tip) == "1.3.0"
    changelog = git(remote, "show", f"{tip}:CHANGELOG.md")
    assert "- Fixed one." in changelog and "- Added two." in changelog
    assert git(remote, "merge-base", "--is-ancestor", merge, tip) == ""


def test_main_that_keeps_moving_eventually_fails(remote, tmp_path):
    work = clone(remote, tmp_path / "work")
    other = clone(remote, tmp_path / "other")

    merges = []

    def someone_always_merges_first():
        merges.append(1)
        (other / "x.txt").write_text(f"merge {len(merges)}\n")
        git(other, "add", "-A")
        git(other, "commit", "-qm", "another merge")
        git(other, "pull", "-q", "--rebase", "origin", "main")
        git(other, "push", "-q", "origin", "HEAD:main")

    with pytest.raises(prepare.ReleaseError, match="kept moving"):
        run(work, max_attempts=3, before_push=someone_always_merges_first)
    assert len(merges) == 3
    # Nothing of ours reached main.
    assert "Update package version" not in git(remote, "log", "--format=%s", "main")


def test_a_rejected_push_that_is_not_a_race_fails_at_once(remote, tmp_path):
    hook = remote / "hooks" / "pre-receive"
    hook.write_text("#!/bin/sh\necho 'rejected by policy' >&2\nexit 1\n")
    hook.chmod(0o755)
    work = clone(remote, tmp_path / "work")
    attempts = []

    with pytest.raises(prepare.ReleaseError, match="has not moved"):
        run(work, before_push=lambda: attempts.append(1))
    assert len(attempts) == 1


@pytest.mark.parametrize(
    "fault",
    ["another file", "a new file", "more of pyproject", "no version rise"],
)
def test_the_guard_refuses_more_than_versioning(remote, tmp_path, fault):
    work = clone(remote, tmp_path / "work")
    base = git(work, "rev-parse", "HEAD")
    git(work, "rm", "-q", "changelog.d/one.fixed.md")
    (work / "CHANGELOG.md").write_text("## [1.2.4]\n- Fixed one.\n## [1.2.3]\n")
    pyproject = (work / "pyproject.toml").read_text()
    version = "1.2.3" if fault == "no version rise" else "1.2.4"
    pyproject = pyproject.replace('version = "1.2.3"', f'version = "{version}"')
    if fault == "more of pyproject":
        pyproject = pyproject.replace("keep = 1", "keep = 2")
    (work / "pyproject.toml").write_text(pyproject)
    if fault == "another file":
        (work / "towncrier.py").write_text("# changed\n")
    if fault == "a new file":
        (work / "new.txt").write_text("new\n")
    git(work, "add", "-A")
    git(work, "commit", "-qm", "Update package version")

    with pytest.raises(prepare.ReleaseError, match="more than versioning"):
        prepare.check_release_diff(prepare.Git(work), base, "HEAD")


def test_github_output_is_appended(remote, tmp_path, capsys, monkeypatch):
    work = clone(remote, tmp_path / "work")
    output = tmp_path / "github_output"
    output.write_text("earlier=1\n")
    monkeypatch.setattr(prepare.time, "sleep", lambda seconds: None)

    rc = prepare.main(
        [
            "--repo",
            str(work),
            "--towncrier",
            f"{sys.executable} towncrier.py",
            "--github-output",
            str(output),
        ]
    )

    assert rc == 0
    lines = output.read_text().splitlines()
    assert lines[0] == "earlier=1"
    values = dict(line.split("=", 1) for line in lines[1:])
    assert values["committed"] == values["pushed"] == "true"
    assert values["sha"] == git(remote, "rev-parse", "main")
    assert set(values) == {"committed", "pushed", "version", "sha", "base"}


def test_a_push_that_landed_but_reported_failure_counts(remote, tmp_path):
    work = clone(remote, tmp_path / "work")

    class FlakyGit(prepare.Git):
        def run(self, *args, check=True):
            result = super().run(*args, check=check)
            if args and args[0] == "push":
                # The server took the push; the client saw an error.
                return subprocess.CompletedProcess(
                    result.args, 1, "", "connection reset"
                )
            return result

    result = run(work, git=FlakyGit(work))

    assert result["pushed"] == "true"
    assert result["sha"] == git(remote, "rev-parse", "main")


def test_verify_accepts_exactly_version_commits(remote, tmp_path, capsys):
    work = clone(remote, tmp_path / "work")
    made = run(work)
    assert prepare.main(["--repo", str(work), "--verify", made["sha"]]) == 0
    assert capsys.readouterr().out.strip() == "version=1.2.4"

    # A version commit by another author, as the old workflow made them.
    git(work, "checkout", "-q", "--detach", made["base"])
    git(work, "rm", "-q", "changelog.d/one.fixed.md")
    (work / "pyproject.toml").write_text(
        (work / "pyproject.toml").read_text().replace("1.2.3", "1.2.4")
    )
    (work / "CHANGELOG.md").write_text("## [1.2.4]\n- Fixed one.\n## [1.2.3]\n")
    git(work, "add", "-A")
    git(work, "commit", "-qm", "Update package version")
    by_hand = git(work, "rev-parse", "HEAD")
    assert prepare.main(["--repo", str(work), "--verify", by_hand]) == 0
    capsys.readouterr()

    # The same subject on a commit that also changes code.
    (work / "towncrier.py").write_text("# changed\n")
    git(work, "commit", "-qam", "Update package version")
    sneaky = git(work, "rev-parse", "HEAD")
    assert prepare.main(["--repo", str(work), "--verify", sneaky]) == 1
    # Another subject, a short SHA, a merge commit.
    assert prepare.main(["--repo", str(work), "--verify", made["base"]]) == 1
    assert prepare.main(["--repo", str(work), "--verify", by_hand[:12]]) == 1
    merge = git(
        work,
        "commit-tree",
        f"{made['sha']}^{{tree}}",
        "-p",
        made["base"],
        "-p",
        by_hand,
        "-m",
        "Update package version",
    )
    assert prepare.main(["--repo", str(work), "--verify", merge]) == 1


# Invariant 7: the tag script.

bash = shutil.which("bash")


def tag(work, *args):
    return subprocess.run(
        [bash, str(TAG_SCRIPT), *args],
        cwd=work,
        capture_output=True,
        text=True,
    )


@pytest.mark.skipif(bash is None, reason="needs bash")
def test_the_tag_script_tags_the_given_commit(remote, tmp_path):
    work = clone(remote, tmp_path / "work")
    release_sha = git(work, "rev-parse", "HEAD")
    (work / "later.txt").write_text("later\n")
    git(work, "add", "-A")
    git(work, "commit", "-qm", "a later commit")
    message = tmp_path / "message.txt"
    message.write_text("demo 1.2.3\n\nhashes\n")

    first = tag(work, "1.2.3", release_sha, str(message))
    assert first.returncode == 0, first.stderr
    assert git(remote, "rev-parse", "1.2.3^{commit}") == release_sha
    assert git(remote, "cat-file", "-t", "1.2.3") == "tag"  # annotated
    assert "hashes" in git(remote, "tag", "-l", "--format=%(contents)", "1.2.3")

    again = tag(work, "1.2.3", release_sha)
    assert again.returncode == 0 and "nothing to do" in again.stdout

    later = git(work, "rev-parse", "HEAD")
    moved = tag(work, "1.2.3", later)
    assert moved.returncode == 1 and "leaving it alone" in moved.stderr
    assert git(remote, "rev-parse", "1.2.3^{commit}") == release_sha


@pytest.mark.skipif(bash is None, reason="needs bash")
@pytest.mark.parametrize(
    "version, sha",
    [
        ("1.2", "HEAD"),
        ("v1.2.3", "HEAD"),
        ("1.2.3", "abc123"),
        ("1.2.3", "0" * 40),
    ],
)
def test_the_tag_script_rejects_bad_input(remote, tmp_path, version, sha):
    work = clone(remote, tmp_path / "work")
    if sha == "HEAD":
        sha = git(work, "rev-parse", "HEAD")
    result = tag(work, version, sha)
    assert result.returncode == 2, result.stderr
    assert git(remote, "tag", "-l") == ""


@pytest.mark.skipif(bash is None, reason="needs bash")
def test_the_tag_script_fails_when_it_cannot_list_tags(remote, tmp_path):
    work = clone(remote, tmp_path / "work")
    sha = git(work, "rev-parse", "HEAD")
    git(work, "remote", "set-url", "origin", str(tmp_path / "gone.git"))
    result = tag(work, "1.2.3", sha)
    assert result.returncode == 1
    assert "cannot list origin's tags" in result.stderr
