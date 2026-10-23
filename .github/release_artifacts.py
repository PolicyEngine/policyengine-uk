"""Check release files against the commit they come from and against PyPI.

The release workflow (.github/workflows/versioning.yaml) builds the wheel and
sdist once, tests the wheel, and uploads those same files. This script makes
the two checks that rest on:

    python3 .github/release_artifacts.py check-dist --dist dist \\
        --version 2.126.8 --sha <commit> [--manifest-out m.json] [--sums-out SHA256SUMS]

checks the wheel and sdist hold exactly the files git tracks at that commit:
every file under ``policyengine_uk/`` and nothing else, byte for byte, with the
right version in their metadata. A wheel built from a dirty or different tree
fails it.

    python3 .github/release_artifacts.py pypi-state --manifest m.json --version 2.126.8 \\
        [--require complete --wait 600]

compares those files with what PyPI serves for that version. ``--manifest``
names the manifest ``check-dist`` wrote, so the comparison is with the files
that were checked and tested, whatever else lands in ``dist`` later (the
publish step writes attestation files there); ``--dist dist`` reads the
files from a directory that must hold exactly the wheel and sdist.

- ``absent``: PyPI has no files for the version.
- ``partial``: every file PyPI has is one of ours, byte for byte, and some of
  ours are missing (an earlier upload stopped part way).
- ``complete``: PyPI has exactly our files.
- ``conflict``: PyPI has a file under one of our names with other bytes, or a
  file that is not ours. The workflow never uploads then.

Standard library only: the jobs that run it do not install the package.
"""

import argparse
import hashlib
import json
import re
import subprocess
import sys
import tarfile
import time
import urllib.error
import urllib.request
import zipfile
from pathlib import Path, PurePosixPath

PACKAGE = "policyengine_uk"
PROJECT = "policyengine-uk"
VERSION = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")
SHA = re.compile(r"^[0-9a-f]{40}$")
STATES = ("absent", "partial", "complete", "conflict")
CAP = 50  # problems listed per kind


class InputError(Exception):
    """An input that cannot be checked, as opposed to a check that failed."""


def git_blob_hash(data: bytes) -> str:
    """The id git gives a file with these bytes."""
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def tracked_files(sha: str, repo: Path) -> dict[str, str]:
    """Path -> blob id of every file git tracks at ``sha``, in one call."""
    try:
        output = subprocess.run(
            ["git", "-C", str(repo), "ls-tree", "-r", "-z", "--full-tree", sha],
            check=True,
            capture_output=True,
        ).stdout
    except (OSError, subprocess.CalledProcessError) as error:
        raise InputError(f"cannot list the files at {sha}: {error}") from None
    files = {}
    for entry in output.split(b"\0"):
        if not entry:
            continue
        meta, path = entry.split(b"\t", 1)
        mode, kind, blob = meta.decode().split()
        files[path.decode("utf-8", "surrogateescape")] = (mode, kind, blob)
    return files


def metadata_field(text: str, name: str) -> str | None:
    """The first value of a header field in METADATA or PKG-INFO."""
    for line in text.splitlines():
        if not line.strip():
            break  # the description starts after the headers
        key, sep, value = line.partition(":")
        if sep and key.strip().lower() == name.lower():
            return value.strip()
    return None


def safe_member_path(name: str) -> bool:
    path = PurePosixPath(name)
    return (
        bool(name)
        and not path.is_absolute()
        and ".." not in path.parts
        and "\\" not in name
    )


def check_package_files(
    found: dict[str, bytes], tracked: dict, label: str, problems: list
) -> None:
    """Compare a distribution's ``policyengine_uk/`` files with git's."""
    expected = {
        path: blob
        for path, (mode, kind, blob) in tracked.items()
        if path.startswith(PACKAGE + "/")
    }
    for path, (mode, kind, _) in tracked.items():
        if path.startswith(PACKAGE + "/") and (
            kind != "blob" or mode not in {"100644", "100755"}
        ):
            problems.append(f"{label}: git tracks {path} as {kind} {mode}")
    missing = sorted(set(expected) - set(found))
    extra = sorted(set(found) - set(expected))
    changed = sorted(
        path
        for path in set(found) & set(expected)
        if git_blob_hash(found[path]) != expected[path]
    )
    for path in missing[:CAP]:
        problems.append(f"{label}: missing {path}")
    for path in extra[:CAP]:
        problems.append(f"{label}: {path} is not tracked at this commit")
    for path in changed[:CAP]:
        problems.append(f"{label}: {path} differs from the commit")
    for kind, paths in (("missing", missing), ("extra", extra), ("changed", changed)):
        if len(paths) > CAP:
            problems.append(f"{label}: ... and {len(paths) - CAP} more {kind}")


def check_wheel(path: Path, version: str, tracked: dict, problems: list) -> None:
    dist_info = f"{PACKAGE}-{version}.dist-info/"
    try:
        archive = zipfile.ZipFile(path)
    except (OSError, zipfile.BadZipFile) as error:
        raise InputError(f"{path.name} is not a zip file: {error}") from None
    with archive:
        package_files = {}
        names = set()
        for info in archive.infolist():
            name = info.filename
            if name in names:
                problems.append(f"wheel: {name} appears twice")
            names.add(name)
            if not safe_member_path(name):
                problems.append(f"wheel: unsafe path {name!r}")
                continue
            if info.is_dir():
                continue
            # The high 16 bits of external_attr are the Unix mode; 0o12 is a link.
            if (info.external_attr >> 28) == 0o12:
                problems.append(f"wheel: {name} is a symbolic link")
                continue
            if name.startswith(dist_info):
                continue
            if not name.startswith(PACKAGE + "/"):
                problems.append(f"wheel: {name} is outside {PACKAGE}/ and {dist_info}")
                continue
            package_files[name] = archive.read(info)
        if dist_info + "METADATA" not in names:
            problems.append(f"wheel: no {dist_info}METADATA")
        else:
            metadata = archive.read(dist_info + "METADATA").decode("utf-8", "replace")
            if metadata_field(metadata, "Name") != PROJECT:
                problems.append(
                    f"wheel: METADATA names {metadata_field(metadata, 'Name')!r}, "
                    f"not {PROJECT!r}"
                )
            if metadata_field(metadata, "Version") != version:
                problems.append(
                    f"wheel: METADATA has version "
                    f"{metadata_field(metadata, 'Version')!r}, not {version!r}"
                )
        other_dist_info = sorted(
            {
                name.split("/", 1)[0]
                for name in names
                if name.split("/", 1)[0].endswith(".dist-info")
            }
            - {dist_info.rstrip("/")}
        )
        for directory in other_dist_info:
            problems.append(f"wheel: unexpected {directory}/")
    check_package_files(package_files, tracked, "wheel", problems)


def check_sdist(path: Path, version: str, tracked: dict, problems: list) -> None:
    root = f"{PACKAGE}-{version}"
    try:
        archive = tarfile.open(path, mode="r:gz")
    except (OSError, tarfile.TarError) as error:
        raise InputError(f"{path.name} is not a gzipped tarball: {error}") from None
    files = {}
    with archive:
        for member in archive.getmembers():
            name = member.name
            if not safe_member_path(name):
                problems.append(f"sdist: unsafe path {name!r}")
                continue
            if member.isdir():
                continue
            if not member.isfile():
                problems.append(f"sdist: {name} is not a regular file")
                continue
            top, sep, rest = name.partition("/")
            if top != root or not sep or not rest:
                problems.append(f"sdist: {name} is outside {root}/")
                continue
            if rest in files:
                problems.append(f"sdist: {name} appears twice")
            files[rest] = archive.extractfile(member).read()
    pkg_info = files.pop("PKG-INFO", None)
    if pkg_info is None:
        problems.append(f"sdist: no {root}/PKG-INFO")
    elif metadata_field(pkg_info.decode("utf-8", "replace"), "Version") != version:
        problems.append(f"sdist: PKG-INFO does not have version {version!r}")
    # Every other file is tracked at the commit, byte for byte; and the
    # package is complete.
    outside = {
        rest: data for rest, data in files.items() if not rest.startswith(PACKAGE + "/")
    }
    # Check every file; CAP limits only how many are listed.
    untracked = sorted(rest for rest in outside if rest not in tracked)
    differing = sorted(
        rest
        for rest, data in outside.items()
        if rest in tracked and git_blob_hash(data) != tracked[rest][2]
    )
    for kind, paths in (
        ("is not tracked at this commit", untracked),
        ("differs from the commit", differing),
    ):
        for rest in paths[:CAP]:
            problems.append(f"sdist: {rest} {kind}")
        if len(paths) > CAP:
            problems.append(f"sdist: ... and {len(paths) - CAP} more that {kind}")
    check_package_files(
        {rest: data for rest, data in files.items() if rest.startswith(PACKAGE + "/")},
        tracked,
        "sdist",
        problems,
    )


def expected_names(version: str) -> tuple[str, str]:
    return (
        f"{PACKAGE}-{version}-py3-none-any.whl",
        f"{PACKAGE}-{version}.tar.gz",
    )


def dist_files(dist: Path, version: str) -> dict[str, Path]:
    """The wheel and sdist in ``dist``, which must hold nothing else."""
    if not dist.is_dir():
        raise InputError(f"{dist} is not a directory")
    found = {path.name: path for path in dist.iterdir()}
    wheel, sdist = expected_names(version)
    if set(found) != {wheel, sdist}:
        raise InputError(
            f"{dist} must hold exactly {wheel} and {sdist}; it holds "
            f"{sorted(found) or 'nothing'}"
        )
    for path in found.values():
        if not path.is_file() or path.is_symlink():
            raise InputError(f"{path} is not a regular file")
    return found


def manifest(files: dict[str, Path], version: str, sha: str) -> dict:
    return {
        "package": PROJECT,
        "version": version,
        "sha": sha,
        "files": [
            {
                "filename": name,
                "sha256": sha256(path.read_bytes()),
                "size": path.stat().st_size,
            }
            for name, path in sorted(files.items())
        ],
    }


def manifest_files(path: Path, version: str) -> dict[str, str]:
    """Filename -> sha256 of the wheel and sdist a ``check-dist`` manifest lists."""
    try:
        record = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise InputError(f"cannot read the manifest {path}: {error}") from None
    if not isinstance(record, dict):
        raise InputError(f"the manifest {path} is not an object")
    if record.get("package") != PROJECT or record.get("version") != version:
        raise InputError(
            f"the manifest {path} is for {record.get('package')!r} "
            f"{record.get('version')!r}, not {PROJECT!r} {version!r}"
        )
    entries = record.get("files")
    if not isinstance(entries, list) or not all(
        isinstance(entry, dict) for entry in entries
    ):
        raise InputError(f"the manifest {path} has no list of files")
    files = {entry.get("filename"): entry.get("sha256") for entry in entries}
    wheel, sdist = expected_names(version)
    if len(entries) != 2 or set(files) != {wheel, sdist}:
        raise InputError(
            f"the manifest {path} must list exactly {wheel} and {sdist}; it lists "
            f"{sorted(map(str, files)) or 'nothing'}"
        )
    for name, digest in files.items():
        if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise InputError(f"the manifest {path} has no sha256 for {name}")
    return files


def check_dist(args) -> int:
    if not VERSION.match(args.version):
        raise InputError(f"version {args.version!r} is not X.Y.Z")
    if not SHA.match(args.sha):
        raise InputError(f"sha {args.sha!r} is not a full 40-character commit")
    files = dist_files(args.dist, args.version)
    tracked = tracked_files(args.sha, args.repo)
    problems = []
    wheel, sdist = expected_names(args.version)
    check_wheel(files[wheel], args.version, tracked, problems)
    check_sdist(files[sdist], args.version, tracked, problems)
    if problems:
        print(f"The release files do not match commit {args.sha}:")
        for problem in problems:
            print(f"  {problem}")
        return 1
    record = manifest(files, args.version, args.sha)
    if args.manifest_out:
        Path(args.manifest_out).write_text(
            json.dumps(record, indent=2) + "\n", encoding="utf-8"
        )
    if args.sums_out:
        Path(args.sums_out).write_text(
            "".join(f"{f['sha256']}  {f['filename']}\n" for f in record["files"]),
            encoding="utf-8",
        )
    print(
        f"{wheel} and {sdist} hold exactly the {PACKAGE}/ files tracked at "
        f"{args.sha}, with version {args.version}."
    )
    for entry in record["files"]:
        print(f"  {entry['sha256']}  {entry['filename']}  ({entry['size']} bytes)")
    return 0


def classify(local: dict[str, str], remote: dict[str, str] | None) -> str:
    """The state of PyPI's files for a version, against ours.

    ``local`` and ``remote`` map filename to sha256; ``remote`` is None when
    the index does not know the version.
    """
    if not remote:
        return "absent"
    for name, digest in remote.items():
        if local.get(name) != digest:
            return "conflict"
    return "complete" if set(remote) == set(local) else "partial"


def fetch_remote(index_url: str, project: str, version: str) -> dict[str, str] | None:
    """filename -> sha256 of the files the index serves, or None for a 404."""
    url = f"{index_url.rstrip('/')}/{project}/{version}/json"
    request = urllib.request.Request(url, headers={"Accept": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            document = json.load(response)
    except urllib.error.HTTPError as error:
        if error.code == 404:
            return None
        raise
    return {entry["filename"]: entry["digests"]["sha256"] for entry in document["urls"]}


def pypi_state(args, fetch=fetch_remote, sleep=time.sleep, clock=time.monotonic) -> int:
    if not VERSION.match(args.version):
        raise InputError(f"version {args.version!r} is not X.Y.Z")
    if args.manifest is not None:
        local = manifest_files(args.manifest, args.version)
    else:
        local = {
            name: sha256(path.read_bytes())
            for name, path in dist_files(args.dist, args.version).items()
        }
    deadline = clock() + args.wait
    while True:
        try:
            remote = fetch(args.index_url, args.project, args.version)
        except (OSError, ValueError, KeyError, TypeError) as error:
            if clock() + args.interval > deadline:
                print(f"Cannot read the index: {error}", file=sys.stderr)
                return 2
            print(f"Cannot read the index ({error}); retrying", file=sys.stderr)
            sleep(args.interval)
            continue
        state = classify(local, remote)
        print(state)
        for name in sorted(set(local) | set(remote or {})):
            ours = local.get(name, "-")
            theirs = (remote or {}).get(name, "-")
            print(f"  {name}: ours {ours}, index {theirs}")
        if state == "conflict":
            print(
                f"The index has other files for {args.project} {args.version}; "
                "refusing to treat these as that release.",
                file=sys.stderr,
            )
            return 3
        if args.require is None or state == args.require:
            return 0
        if clock() + args.interval > deadline:
            print(
                f"The index is {state}, not {args.require}, after {args.wait} seconds.",
                file=sys.stderr,
            )
            return 4
        sleep(args.interval)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    commands = parser.add_subparsers(dest="command", required=True)

    check = commands.add_parser("check-dist", help="check files against a commit")
    check.add_argument("--dist", required=True, type=Path)
    check.add_argument("--version", required=True)
    check.add_argument("--sha", required=True)
    check.add_argument("--repo", default=Path("."), type=Path)
    check.add_argument("--manifest-out", type=Path)
    check.add_argument("--sums-out", type=Path)

    state = commands.add_parser("pypi-state", help="compare files with the index")
    ours = state.add_mutually_exclusive_group(required=True)
    ours.add_argument("--manifest", type=Path, help="the manifest check-dist wrote")
    ours.add_argument("--dist", type=Path, help="a directory of exactly the files")
    state.add_argument("--version", required=True)
    state.add_argument("--project", default=PROJECT)
    state.add_argument("--index-url", default="https://pypi.org/pypi")
    state.add_argument("--require", choices=STATES[:3])
    state.add_argument("--wait", type=float, default=0)
    state.add_argument("--interval", type=float, default=15)

    args = parser.parse_args(argv)
    try:
        if args.command == "check-dist":
            return check_dist(args)
        return pypi_state(args)
    except InputError as error:
        print(f"Cannot check: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
