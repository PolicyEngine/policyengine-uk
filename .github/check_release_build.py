"""Check that a release build records the commit it was built from.

Usage: python .github/check_release_build.py DIST_DIRECTORY COMMIT SDIST_WHEEL_DIRECTORY

DIST_DIRECTORY holds what ``make`` built: an sdist, and a wheel built from the
checkout. SDIST_WHEEL_DIRECTORY holds a wheel built from that sdist. Exits
non-zero unless all of these hold:

- the release wheel records COMMIT and its own version in
  ``.dist-info/extra_metadata/build_info.json`` (written by hatch_build.py);
- the sdist records no commit;
- the wheel built from the sdist records no commit, and otherwise has the
  same members and bytes as the release wheel, apart from RECORD. Before the
  release build moved to ``python -m build --sdist --wheel``, the release
  wheel was built from the sdist, which proved the sdist builds the same
  package.
"""

import json
from pathlib import Path
import sys
import tarfile
import zipfile

BUILD_INFO_SUFFIX = ".dist-info/extra_metadata/build_info.json"


def _wheel_members(wheel: Path) -> dict[str, bytes]:
    with zipfile.ZipFile(wheel) as archive:
        return {name: archive.read(name) for name in archive.namelist()}


def main(dist_directory: str, commit: str, sdist_wheel_directory: str) -> int:
    [wheel] = sorted(Path(dist_directory).glob("*.whl"))
    [sdist] = sorted(Path(dist_directory).glob("*.tar.gz"))
    [sdist_wheel] = sorted(Path(sdist_wheel_directory).glob("*.whl"))
    members = _wheel_members(wheel)
    build_info_names = [name for name in members if name.endswith(BUILD_INFO_SUFFIX)]
    if len(build_info_names) != 1:
        print(f"{wheel.name} records no build commit")
        return 1
    build_info = json.loads(members[build_info_names[0]])
    expected = {"git_sha": commit, "version": wheel.name.split("-")[1]}
    if build_info != expected:
        print(f"{wheel.name} records {build_info}, expected {expected}")
        return 1
    with tarfile.open(sdist) as archive:
        if any(name.endswith("build_info.json") for name in archive.getnames()):
            print(f"{sdist.name} contains a build_info.json")
            return 1
    sdist_members = _wheel_members(sdist_wheel)
    if any(name.endswith(BUILD_INFO_SUFFIX) for name in sdist_members):
        print(f"the wheel built from {sdist.name} records a commit")
        return 1
    expected_names = set(members) - set(build_info_names)
    if set(sdist_members) != expected_names:
        print(
            f"the wheel built from {sdist.name} differs in members: "
            f"missing {sorted(expected_names - set(sdist_members))}, "
            f"extra {sorted(set(sdist_members) - expected_names)}"
        )
        return 1
    differing = sorted(
        name
        for name in expected_names
        if not name.endswith(".dist-info/RECORD")
        and members[name] != sdist_members[name]
    )
    if differing:
        print(f"the wheel built from {sdist.name} differs in {differing}")
        return 1
    print(
        f"{wheel.name} records {build_info}; {sdist.name} records no commit and "
        "builds the same package"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:]))
