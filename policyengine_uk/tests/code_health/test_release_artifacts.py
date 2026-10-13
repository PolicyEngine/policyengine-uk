"""The release publishes the files it tested, and nothing else.

``.github/release_artifacts.py`` makes the release workflow's two identity
checks: ``check-dist`` (the wheel and sdist hold exactly a commit's files)
and ``pypi-state`` (what PyPI already serves for the version). These tests
hold it to:

1. ``classify`` gives every pair of local and remote files exactly the state
   its definition says (differential against an independent statement of
   the rule): ``complete`` iff the index has exactly our files; ``conflict``
   iff the index has a file that is not ours byte for byte; never
   ``complete`` or ``partial`` when any remote digest differs from ours.
2. ``check-dist`` passes for a wheel and sdist laid out as hatchling builds
   them from a commit's tree.
3. Any single change to those files fails it and names the file: a changed
   byte in any member, a missing or extra file, a wrong version in METADATA
   or PKG-INFO, a wrong file name, another file in the directory, an unsafe
   or linked member, or a different commit.
4. The manifest and SHA256SUMS hold the files' real sha256 digests.
5. ``pypi-state --require complete --wait`` waits for the index to serve our
   files, stops at once on a conflict, and gives up at the deadline.
"""

import hashlib
import importlib.util
import io
import json
import os
import subprocess
import tarfile
import zipfile
from pathlib import Path

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT = REPO_ROOT / ".github" / "release_artifacts.py"

if not SCRIPT.exists():
    pytest.skip(
        "the .github folder is not part of an installed package",
        allow_module_level=True,
    )

_spec = importlib.util.spec_from_file_location("release_artifacts", SCRIPT)
release = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(release)

SETTINGS = settings(
    max_examples=100,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.function_scoped_fixture],
)
GIT_ENV = {
    **os.environ,
    "GIT_CONFIG_GLOBAL": os.devnull,
    "GIT_CONFIG_NOSYSTEM": "1",
    "GIT_AUTHOR_NAME": "t",
    "GIT_AUTHOR_EMAIL": "t@example.com",
    "GIT_COMMITTER_NAME": "t",
    "GIT_COMMITTER_EMAIL": "t@example.com",
}
VERSION = "2.126.8"


# Invariant 1: classify.

names = st.sampled_from(
    ["a-2.0.0-py3-none-any.whl", "a-2.0.0.tar.gz", "a-2.0.0-cp313-none-any.whl"]
)
digests = st.sampled_from(["0" * 64, "1" * 64, "2" * 64])
files = st.dictionaries(names, digests, max_size=3)


def model_state(local, remote):
    if not remote:
        return "absent"
    if any(name not in local or local[name] != remote[name] for name in remote):
        return "conflict"
    return "complete" if remote == local else "partial"


@SETTINGS
@given(local=files.filter(bool), remote=st.none() | files)
def test_classify_matches_its_definition(local, remote):
    state = release.classify(local, remote)
    assert state in release.STATES
    assert state == model_state(local, remote)
    assert (state == "complete") == (remote == local)
    if remote and any(local.get(n) != d for n, d in remote.items()):
        assert state == "conflict"


# Invariants 2 to 4: check-dist.


def git(repo, *args):
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        text=True,
        env=GIT_ENV,
    ).stdout.strip()


TREE = {
    "pyproject.toml": b'[project]\nname = "policyengine-uk"\nversion = "2.126.8"\n',
    "README.md": b"# readme\n",
    "LICENSE": b"licence\n",
    "CHANGELOG.md": b"## [2.126.8]\n",
    "policyengine_uk/__init__.py": b"from .x import y\n",
    "policyengine_uk/x.py": b"y = 1\n",
    "policyengine_uk/parameters/gov/a.yaml": b"values:\n  2026-01-01: 1\n",
    "policyengine_uk/tests/test_y.py": b"def test_y():\n    pass\n",
}


@pytest.fixture
def commit(tmp_path):
    """A git repository holding TREE; returns (repo, sha)."""
    repo = tmp_path / "repo"
    repo.mkdir()
    git(repo, "init", "-q", "-b", "main")
    for path, data in TREE.items():
        (repo / path).parent.mkdir(parents=True, exist_ok=True)
        (repo / path).write_bytes(data)
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "tree")
    return repo, git(repo, "rev-parse", "HEAD")


def wheel_members(tree=TREE, version=VERSION):
    dist_info = f"policyengine_uk-{version}.dist-info"
    members = {p: d for p, d in tree.items() if p.startswith("policyengine_uk/")}
    members[f"{dist_info}/METADATA"] = (
        f"Metadata-Version: 2.4\nName: policyengine-uk\nVersion: {version}\n\n"
        "Version: 9.9.9 in the description is not a header\n"
    ).encode()
    members[f"{dist_info}/WHEEL"] = b"Wheel-Version: 1.0\nTag: py3-none-any\n"
    members[f"{dist_info}/licenses/LICENSE"] = tree["LICENSE"]
    members[f"{dist_info}/RECORD"] = b""
    return members


def sdist_members(tree=TREE, version=VERSION):
    root = f"policyengine_uk-{version}"
    members = {f"{root}/{p}": d for p, d in tree.items()}
    members[f"{root}/PKG-INFO"] = (
        f"Metadata-Version: 2.4\nName: policyengine-uk\nVersion: {version}\n"
    ).encode()
    return members


def write_wheel(path, members, links=()):
    with zipfile.ZipFile(path, "w") as archive:
        for name, data in members.items():
            archive.writestr(name, data)
        for name in links:
            info = zipfile.ZipInfo(name)
            info.external_attr = 0o120777 << 16
            archive.writestr(info, "target")


def write_sdist(path, members, links=()):
    with tarfile.open(path, "w:gz") as archive:
        for name, data in members.items():
            info = tarfile.TarInfo(name)
            info.size = len(data)
            archive.addfile(info, io.BytesIO(data))
        for name in links:
            info = tarfile.TarInfo(name)
            info.type = tarfile.SYMTYPE
            info.linkname = "/etc/passwd"
            archive.addfile(info)


def build(directory, wheel=None, sdist=None, version=VERSION, links=None):
    links = links or {}
    directory.mkdir(exist_ok=True)
    whl = directory / f"policyengine_uk-{version}-py3-none-any.whl"
    tgz = directory / f"policyengine_uk-{version}.tar.gz"
    write_wheel(
        whl, wheel_members() if wheel is None else wheel, links.get("wheel", ())
    )
    write_sdist(
        tgz, sdist_members() if sdist is None else sdist, links.get("sdist", ())
    )
    return directory


def check_dist(dist, repo, sha, version=VERSION, *extra):
    return release.main(
        [
            "check-dist",
            "--dist",
            str(dist),
            "--version",
            version,
            "--sha",
            sha,
            "--repo",
            str(repo),
            *extra,
        ]
    )


def test_check_dist_passes_for_the_commits_files(commit, tmp_path, capsys):
    repo, sha = commit
    dist = build(tmp_path / "dist")
    manifest, sums = tmp_path / "manifest.json", tmp_path / "SHA256SUMS"
    assert (
        check_dist(
            dist,
            repo,
            sha,
            VERSION,
            "--manifest-out",
            str(manifest),
            "--sums-out",
            str(sums),
        )
        == 0
    ), capsys.readouterr().out
    # Invariant 4.
    record = json.loads(manifest.read_text())
    assert record["sha"] == sha and record["version"] == VERSION
    actual = {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in dist.iterdir()
    }
    assert {f["filename"]: f["sha256"] for f in record["files"]} == actual
    assert {
        line.split("  ")[1]: line.split("  ")[0]
        for line in sums.read_text().splitlines()
    } == actual


@SETTINGS
@given(data=st.data())
def test_any_changed_byte_in_any_member_fails(commit, tmp_path_factory, data):
    repo, sha = commit
    which = data.draw(st.sampled_from(["wheel", "sdist"]))
    members = wheel_members() if which == "wheel" else sdist_members()
    # Files whose bytes are compared with the commit (not RECORD or WHEEL).
    candidates = sorted(
        name
        for name in members
        if "dist-info" not in name and not name.endswith("PKG-INFO")
    )
    name = data.draw(st.sampled_from(candidates))
    original = members[name]
    position = data.draw(st.integers(0, len(original) - 1))
    flipped = bytearray(original)
    flipped[position] ^= data.draw(st.integers(1, 255))
    members[name] = bytes(flipped)
    dist = build(tmp_path_factory.mktemp("dist"), **{which: members})
    assert check_dist(dist, repo, sha) == 1


def mutate(kind):
    """(wheel members, sdist members, extra keyword args) for one fault."""
    wheel, sdist = wheel_members(), sdist_members()
    root = f"policyengine_uk-{VERSION}"
    if kind == "wheel missing file":
        del wheel["policyengine_uk/x.py"]
    elif kind == "wheel extra file":
        wheel["policyengine_uk/extra.py"] = b"x = 2\n"
    elif kind == "wheel file outside package":
        wheel["other/x.py"] = b"x = 2\n"
    elif kind == "wheel unsafe path":
        wheel["policyengine_uk/../evil.py"] = b"x = 2\n"
    elif kind == "wheel wrong version":
        wheel[f"{root}.dist-info/METADATA"] = (
            b"Name: policyengine-uk\nVersion: 2.126.9\n"
        )
    elif kind == "wheel wrong name":
        wheel[f"{root}.dist-info/METADATA"] = (
            b"Name: policyengine-us\nVersion: 2.126.8\n"
        )
    elif kind == "wheel second dist-info":
        wheel["other-1.0.dist-info/METADATA"] = b"Name: other\n"
    elif kind == "sdist missing file":
        del sdist[f"{root}/policyengine_uk/parameters/gov/a.yaml"]
    elif kind == "sdist untracked file":
        sdist[f"{root}/setup.py"] = b"import os\n"
    elif kind == "sdist outside root":
        sdist["elsewhere/x.py"] = b"y = 1\n"
    elif kind == "sdist unsafe path":
        sdist[f"{root}/../evil.py"] = b"x\n"
    elif kind == "sdist absolute path":
        sdist["/tmp/evil.py"] = b"x\n"
    elif kind == "sdist wrong version":
        sdist[f"{root}/PKG-INFO"] = b"Name: policyengine-uk\nVersion: 2.126.7\n"
    elif kind == "sdist no PKG-INFO":
        del sdist[f"{root}/PKG-INFO"]
    elif kind == "sdist link":
        return wheel, sdist, {"sdist": [f"{root}/policyengine_uk/link.py"]}
    elif kind == "wheel link":
        return wheel, sdist, {"wheel": ["policyengine_uk/link.py"]}
    return wheel, sdist, {}


FAULTS = [
    "wheel missing file",
    "wheel extra file",
    "wheel file outside package",
    "wheel unsafe path",
    "wheel wrong version",
    "wheel wrong name",
    "wheel second dist-info",
    "wheel link",
    "sdist missing file",
    "sdist untracked file",
    "sdist outside root",
    "sdist unsafe path",
    "sdist absolute path",
    "sdist wrong version",
    "sdist no PKG-INFO",
    "sdist link",
]


@pytest.mark.parametrize("fault", FAULTS)
def test_each_fault_fails_check_dist(commit, tmp_path, fault, capsys):
    repo, sha = commit
    wheel, sdist, links = mutate(fault)
    dist = build(tmp_path / "dist", wheel=wheel, sdist=sdist, links=links)
    assert check_dist(dist, repo, sha) == 1
    assert "do not match" in capsys.readouterr().out


def test_every_sdist_file_is_checked_not_only_the_first_fifty(commit, tmp_path, capsys):
    # The listing is capped; the check is not. Sixty untracked files sorted
    # before a changed tracked one: the changed one must still fail.
    repo, sha = commit
    sdist = sdist_members()
    root = f"policyengine_uk-{VERSION}"
    for number in range(60):
        sdist[f"{root}/a{number:02}.txt"] = b"untracked\n"
    dist = build(tmp_path / "dist", sdist=sdist)
    assert check_dist(dist, repo, sha) == 1
    report = capsys.readouterr().out
    assert "and 10 more that is not tracked" in report

    only_changed = sdist_members()
    only_changed[f"{root}/README.md"] = b"# changed\n"
    for number in range(60):
        only_changed[f"{root}/0{number:02}.md"] = TREE["README.md"]
    dist = build(tmp_path / "dist2", sdist=only_changed)
    assert check_dist(dist, repo, sha) == 1
    assert "README.md differs from the commit" in capsys.readouterr().out


def test_other_files_and_wrong_names_are_unusable_input(commit, tmp_path):
    repo, sha = commit
    dist = build(tmp_path / "dist")
    (dist / "notes.txt").write_text("x")
    assert check_dist(dist, repo, sha) == 2
    (dist / "notes.txt").unlink()
    # The files are named for another version.
    assert check_dist(dist, repo, sha, "2.126.9") == 2
    assert check_dist(dist, repo, "deadbeef") == 2
    assert check_dist(tmp_path / "absent", repo, sha) == 2


def test_a_different_commit_fails(commit, tmp_path):
    repo, sha = commit
    (repo / "policyengine_uk" / "x.py").write_bytes(b"y = 2\n")
    git(repo, "commit", "-qam", "change")
    dist = build(tmp_path / "dist")
    assert check_dist(dist, repo, git(repo, "rev-parse", "HEAD")) == 1
    assert check_dist(dist, repo, sha) == 0


# Invariant 5: pypi-state.


def state_args(dist, require=None, wait=0):
    import argparse

    return argparse.Namespace(
        dist=dist,
        version=VERSION,
        project="policyengine-uk",
        index_url="https://index.invalid/pypi",
        require=require,
        wait=wait,
        interval=1,
    )


class FakeClock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now

    def sleep(self, seconds):
        self.now += seconds


def ours(dist):
    return {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in dist.iterdir()
    }


def test_pypi_state_waits_for_the_index_to_serve_our_files(tmp_path):
    dist = build(tmp_path / "dist")
    answers = iter([None, {}, dict(list(ours(dist).items())[:1]), ours(dist)])
    clock = FakeClock()
    rc = release.pypi_state(
        state_args(dist, "complete", wait=60),
        fetch=lambda *a: next(answers),
        sleep=clock.sleep,
        clock=clock,
    )
    assert rc == 0
    assert clock.now == 3


def test_pypi_state_stops_at_once_on_a_conflict(tmp_path):
    dist = build(tmp_path / "dist")
    other = {name: "f" * 64 for name in ours(dist)}
    clock = FakeClock()
    rc = release.pypi_state(
        state_args(dist, "complete", wait=60),
        fetch=lambda *a: other,
        sleep=clock.sleep,
        clock=clock,
    )
    assert rc == 3 and clock.now == 0
    # A file that is not ours is a conflict too.
    extra = {**ours(dist), "policyengine_uk-2.126.8-cp313-none-any.whl": "0" * 64}
    assert release.pypi_state(state_args(dist), fetch=lambda *a: extra) == 3


def test_pypi_state_gives_up_at_the_deadline(tmp_path):
    dist = build(tmp_path / "dist")
    clock = FakeClock()
    rc = release.pypi_state(
        state_args(dist, "complete", wait=10),
        fetch=lambda *a: None,
        sleep=clock.sleep,
        clock=clock,
    )
    assert rc == 4 and clock.now <= 10

    def broken(*args):
        raise OSError("network down")

    clock = FakeClock()
    assert (
        release.pypi_state(
            state_args(dist, "complete", wait=5),
            fetch=broken,
            sleep=clock.sleep,
            clock=clock,
        )
        == 2
    )


def test_pypi_state_reports_without_waiting(tmp_path, capsys):
    dist = build(tmp_path / "dist")
    assert release.pypi_state(state_args(dist), fetch=lambda *a: None) == 0
    assert capsys.readouterr().out.splitlines()[0] == "absent"
    partial = dict(list(ours(dist).items())[:1])
    assert release.pypi_state(state_args(dist), fetch=lambda *a: partial) == 0
    assert capsys.readouterr().out.splitlines()[0] == "partial"
