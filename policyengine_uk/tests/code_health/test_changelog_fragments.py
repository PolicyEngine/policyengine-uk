"""What the changelog check accepts is what towncrier writes to CHANGELOG.md.

towncrier writes a fragment in ``changelog.d`` to CHANGELOG.md only when its
name carries a type configured in pyproject.toml; it never reads or deletes
any other file there, and leaves an empty fragment out.
``.github/bump_version.py`` counts fragments for the version bump and
``.github/check_changelog_fragments.py`` fails pull requests that add ones
towncrier would drop. These tests hold them to:

1. Config: the fragment types, directory and orphan prefix bump_version reads
   from pyproject.toml equal towncrier's own, for this repository and for
   each way towncrier can be configured (differential).
2. Names: for any file name, bump_version's (issue, type, counter) equals
   towncrier's ``parse_newfragment_basename`` (differential).
3. Directories: the files bump_version counts are exactly the fragments
   towncrier's ``find_fragments`` consumes, with the same types, and it calls
   a file untyped exactly when towncrier's strict mode rejects the directory
   (differential, every configuration in 1).
4. The check never accepts a name towncrier drops, and every name it accepts
   towncrier consumes with the type the name shows.
5. Rendering, with the real ``towncrier build``: each fragment the check
   accepts appears once, with one bullet; each it rejects is missing from
   the output; a fragment it warns about starts with ``- - ``.
6. On a real git repository the check fails exactly the files a pull request
   adds or changes that towncrier would drop or that would stop the build,
   passes deletions and ignored names, and only warns about files it does not
   change and a pull request without a fragment.
7. The version bump depends only on typed fragments (breaking is major, added
   or removed minor, any other type patch). Untyped files never change it.
   With no typed fragment the script exits 1 and leaves the version alone.
"""

import contextlib
import importlib.util
import io
import os
import shutil
import string
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path

import pytest
from click import ClickException
from hypothesis import assume, given, settings
from hypothesis import strategies as st
from towncrier._builder import (
    FragmentsPath,
    find_fragments,
    parse_newfragment_basename,
)
from towncrier._settings.load import load_config_from_options, parse_toml

REPO_ROOT = Path(__file__).resolve().parents[3]
GITHUB_DIR = REPO_ROOT / ".github"
BUMP_SCRIPT = GITHUB_DIR / "bump_version.py"
CHECK_SCRIPT = GITHUB_DIR / "check_changelog_fragments.py"

if not CHECK_SCRIPT.exists():
    pytest.skip(
        "the .github folder is not part of an installed package",
        allow_module_level=True,
    )


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


bump = load("bump_version", BUMP_SCRIPT)
check = load("check_changelog_fragments", CHECK_SCRIPT)

PYPROJECT = (REPO_ROOT / "pyproject.toml").read_text()
CONFIG = bump.parse_towncrier_config(PYPROJECT)

# The repository's configuration, and one of each other way towncrier reads
# fragment types, directories, ignore lists, templates and orphan prefixes.
CONFIGS = {
    "repository": PYPROJECT,
    "default types": '[tool.towncrier]\ndirectory = "news"\n',
    "default directory": '[tool.towncrier]\npackage = "pkg"\n',
    "type array": (
        '[tool.towncrier]\ndirectory = "news"\n'
        '[[tool.towncrier.type]]\nname = "Security"\n'
        '[[tool.towncrier.type]]\nname = "Features"\ndirectory = "feature"\n'
    ),
    "fragment tables and ignore": (
        '[tool.towncrier]\ndirectory = "news"\nignore = ["NOTES.txt", "*.tmp"]\n'
        '[tool.towncrier.fragment.chore]\n[tool.towncrier.fragment.fix]\nname = "Fixes"\n'
    ),
    "template file and orphan prefix": (
        '[tool.towncrier]\ndirectory = "news"\ntemplate = "news/template.md"\n'
        'orphan_prefix = "~"\n'
    ),
}

NAME_PART = st.one_of(
    st.sampled_from(
        [
            *CONFIG.types,
            *bump.TOWNCRIER_DEFAULT_TYPES,
            "security",
            "chore",
            "fix",
            "md",
            "rst",
            "Fixed",
            "1",
            "007",
            "2314",
            "+x",
            "~y",
            " ",
            "",
            "readme",
            "README",
            "gitkeep",
            "tmp",
            "NOTES",
            "txt",
            "Template",
        ]
    ),
    st.text(alphabet=string.ascii_letters + string.digits + "-_+~ ", max_size=5),
)
NAMES = st.lists(NAME_PART, min_size=1, max_size=5).map(".".join)
FILE_NAMES = NAMES.filter(lambda name: name not in ("", ".", ".."))
SLUGS = st.from_regex(r"\+?[A-Za-z0-9][A-Za-z0-9._-]{0,20}", fullmatch=True)


def towncrier_parse(name, types):
    parsed = parse_newfragment_basename(name, types)
    return None if parsed == (None, None, None) else parsed


# 1. Config


@pytest.mark.parametrize("text", CONFIGS.values(), ids=CONFIGS.keys())
def test_config_matches_towncrier(text, tmp_path):
    (tmp_path / "news").mkdir()
    (tmp_path / "news" / "template.md").write_text("")
    theirs = parse_toml(str(tmp_path), tomllib.loads(text))
    ours = bump.parse_towncrier_config(text)

    assert ours.types == tuple(theirs.types)
    assert ours.orphan_prefix == theirs.orphan_prefix
    assert (tmp_path / ours.directory).resolve() == Path(
        FragmentsPath(str(tmp_path), theirs)("")
    ).resolve()


def test_repository_config():
    assert CONFIG.directory == "changelog.d"
    assert CONFIG.types == ("breaking", "added", "changed", "fixed", "removed")


def test_a_pyproject_without_towncrier_is_an_error():
    with pytest.raises(ValueError, match="tool.towncrier"):
        bump.parse_towncrier_config('[project]\nname = "x"\n')


# 2. Names


@settings(max_examples=500, deadline=None)
@given(NAMES)
def test_name_parsing_matches_towncrier(name):
    for types in (
        CONFIG.types,
        bump.TOWNCRIER_DEFAULT_TYPES,
        bump.parse_towncrier_config(CONFIGS["fragment tables and ignore"]).types,
    ):
        assert bump.parse_fragment_name(name, types) == towncrier_parse(name, types)


# 3. Directories


@pytest.mark.parametrize("text", CONFIGS.values(), ids=CONFIGS.keys())
@settings(max_examples=60, deadline=None)
@given(names=st.lists(FILE_NAMES, max_size=8, unique_by=str.lower))
def test_counted_fragments_are_the_ones_towncrier_consumes(text, names):
    config = bump.parse_towncrier_config(text)
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "pyproject.toml").write_text(text)
        directory = root / config.directory
        directory.mkdir(parents=True)
        if "template" in text:
            (root / "news" / "template.md").write_text("")
        for name in names:
            if not (directory / name).exists():
                (directory / name).write_text("A note.\n")
        base, theirs = load_config_from_options(str(root), None)
        try:
            consumed = find_fragments(base, theirs, strict=False)[1]
        except ValueError:
            # Two fragments share a key; towncrier refuses to build at all.
            assume(False)
        typed, untyped = bump.classify_fragments(directory, config)

        assert sorted((path.name, kind) for path, kind in typed) == sorted(
            (Path(path).name, kind) for path, kind in consumed
        )
        try:
            find_fragments(base, theirs, strict=True)
            towncrier_rejects = False
        except ClickException:
            towncrier_rejects = True
        assert towncrier_rejects == bool(untyped)


# 4. The check's names


@settings(max_examples=500, deadline=None)
@given(FILE_NAMES)
def test_the_check_never_accepts_a_name_towncrier_drops(name):
    parsed = towncrier_parse(name, CONFIG.types)
    if check.name_problem(name, CONFIG) is None:
        assert parsed is not None
        assert parsed[1] == name.removesuffix(".md").rpartition(".")[2]
    if parsed is None:
        assert check.name_problem(name, CONFIG) is not None


@settings(max_examples=300, deadline=None)
@given(SLUGS, st.sampled_from(CONFIG.types))
def test_slug_type_md_names_pass(slug, fragment_type):
    name = f"{slug}.{fragment_type}.md"

    assert check.name_problem(name, CONFIG) is None
    assert not bump.is_ignored(name, CONFIG)
    assert towncrier_parse(name, CONFIG.types)[1] == fragment_type


@pytest.mark.parametrize(
    "name",
    [
        "1005.md",
        "1044-explicit-leave.md",
        "fixed.md",
        ".fixed.md",
        "x.Fixed.md",
        "x.feature.md",
        "x.fixed",
        "x.fixed.txt",
        "x.fixed.2.md",
        "with space.fixed.md",
        "-x.fixed.md",
    ],
)
def test_names_the_check_rejects(name):
    assert check.name_problem(name, CONFIG) is not None


@pytest.mark.parametrize(
    "data, error, warning",
    [
        (b"Fixed a thing.\n", False, False),
        (b"Fixed:\n\n- one\n- two\n", False, False),
        (b"", True, False),
        (b"  \n\t\n", True, False),
        (b"\xff\xfe", True, False),
        (b"- Fixed a thing.\n", False, True),
        (b"\n* Fixed a thing.\n", False, True),
        (b"+ Fixed a thing.\n", False, True),
    ],
)
def test_fragment_content(data, error, warning):
    found_error, found_warning = check.content_problems(data)

    assert bool(found_error) == error
    assert bool(found_warning) == warning


# 5. Rendering


def test_rendering_agrees_with_the_check(tmp_path):
    fragments = {
        "a.fixed.md": b"Fixed a.\n",
        "b.added.md": b"Added b.\n",
        "2314.removed.md": b"Removed c.\n",
        "+orphan.changed.md": b"Changed d.\n",
        "untyped.md": b"Untyped note.\n",
        "empty.fixed.md": b"",
        "blank.added.md": b"  \n",
        "bullet.changed.md": b"- Bulleted note.\n",
    }
    (tmp_path / "pyproject.toml").write_text(PYPROJECT)
    (tmp_path / "CHANGELOG.md").write_text("# Changelog\n")
    (tmp_path / "changelog.d").mkdir()
    for name, data in fragments.items():
        (tmp_path / "changelog.d" / name).write_bytes(data)

    draft = subprocess.run(
        [
            sys.executable,
            "-m",
            "towncrier",
            "build",
            "--draft",
            "--name",
            "policyengine-uk",
            "--version",
            "9.9.9",
            "--date",
            "2026-01-01",
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    bullets = [line for line in draft.splitlines() if line.startswith("- ")]

    for name, data in fragments.items():
        error, warning = check.check_fragment(f"changelog.d/{name}", data, CONFIG)
        text = data.decode().strip()
        if error:
            # Dropped: an untyped name, or nothing to write.
            assert not text or text not in draft, name
        else:
            assert bullets.count(f"- {text}") == 1, name
            assert text.startswith("- ") == bool(warning), name
    # Only accepted fragments, and the warned one, produce bullets.
    accepted = [
        name
        for name, data in fragments.items()
        if not check.check_fragment(f"changelog.d/{name}", data, CONFIG)[0]
    ]
    assert len(bullets) == len(accepted)


# 6. The check on a real git repository

GIT_ENV = {
    **os.environ,
    "GIT_CONFIG_GLOBAL": os.devnull,
    "GIT_CONFIG_NOSYSTEM": "1",
    "GIT_AUTHOR_NAME": "t",
    "GIT_AUTHOR_EMAIL": "t@example.com",
    "GIT_COMMITTER_NAME": "t",
    "GIT_COMMITTER_EMAIL": "t@example.com",
}


def git(repo, *args):
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        env=GIT_ENV,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()


@pytest.fixture
def repo(tmp_path):
    """A repository whose base commit holds two untyped files and a fragment."""
    git(tmp_path, "init", "-q", "-b", "main")
    (tmp_path / "pyproject.toml").write_text(PYPROJECT)
    (tmp_path / "changelog.d").mkdir()
    (tmp_path / "changelog.d" / ".gitkeep").write_text("")
    (tmp_path / "changelog.d" / "stale.md").write_text("Stale note.\n")
    (tmp_path / "changelog.d" / "old.md").write_text("Old note.\n")
    (tmp_path / "changelog.d" / "kept.fixed.md").write_text("Kept.\n")
    (tmp_path / "code.py").write_text("x = 1\n")
    git(tmp_path, "add", "-A")
    git(tmp_path, "commit", "-qm", "base")
    return tmp_path


def commit(repo, files=(), delete=(), moves=()):
    base = git(repo, "rev-parse", "HEAD")
    for path, data in dict(files).items():
        target = repo / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data if isinstance(data, bytes) else data.encode())
    for path in delete:
        git(repo, "rm", "-q", path)
    for source, target in moves:
        git(repo, "mv", source, target)
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "change", "--allow-empty")
    return base, git(repo, "rev-parse", "HEAD")


def run_check(repo, base, head):
    result = subprocess.run(
        [
            sys.executable,
            str(CHECK_SCRIPT),
            "--repo",
            str(repo),
            "--base",
            base,
            "--head",
            head,
        ],
        capture_output=True,
        text=True,
    )
    annotations = {"error": set(), "warning": set(), "unlocated": []}
    for line in result.stdout.splitlines():
        level, _, rest = line.removeprefix("::").partition(" file=")
        if rest:
            annotations[level].add(rest.split("::", 1)[0])
        elif line.startswith("::"):
            annotations["unlocated"].append(line)
    return result.returncode, annotations


def test_the_check_fails_exactly_the_fragments_towncrier_would_drop(repo):
    base, head = commit(
        repo,
        files={
            "changelog.d/good.fixed.md": "Fixed a thing.\n",
            "changelog.d/1234.md": "Untyped.\n",
            "changelog.d/x.feature.md": "Unknown type.\n",
            "changelog.d/empty.added.md": "",
            "changelog.d/binary.changed.md": b"\xff\xfe",
            "changelog.d/with space.fixed.md": "Space.\n",
            "changelog.d/sub/nested.fixed.md": "Nested.\n",
            "changelog.d/7.removed.md": "Seven.\n",
            "changelog.d/007.removed.md": "Seven again.\n",
            "changelog.d/bullet.changed.md": "- Changed.\n",
            "changelog.d/README.md": "About this folder.\n",
            "changelog.d/old.md": "Old note, edited.\n",
        },
        delete=["changelog.d/kept.fixed.md"],
    )

    code, found = run_check(repo, base, head)

    assert code == 1
    assert found["error"] == {
        "changelog.d/1234.md",
        "changelog.d/x.feature.md",
        "changelog.d/empty.added.md",
        "changelog.d/binary.changed.md",
        "changelog.d/with space.fixed.md",
        "changelog.d/sub/nested.fixed.md",
        "changelog.d/7.removed.md",
        "changelog.d/007.removed.md",
        "changelog.d/old.md",
    }
    assert found["warning"] == {"changelog.d/bullet.changed.md", "changelog.d/stale.md"}
    assert found["unlocated"] == []


def test_deleting_untyped_files_and_adding_a_fragment_passes(repo):
    base, head = commit(
        repo,
        files={"changelog.d/2314.fixed.md": "Fixed the changelog.\n"},
        delete=["changelog.d/stale.md", "changelog.d/old.md"],
    )

    code, found = run_check(repo, base, head)

    assert code == 0
    assert found == {"error": set(), "warning": set(), "unlocated": []}


def test_renaming_a_fragment_to_an_untyped_name_fails(repo):
    base, head = commit(
        repo, moves=[("changelog.d/kept.fixed.md", "changelog.d/kept.md")]
    )

    code, found = run_check(repo, base, head)

    assert code == 1
    assert found["error"] == {"changelog.d/kept.md"}


def test_a_pull_request_without_a_fragment_only_warns(repo):
    base, head = commit(repo, files={"code.py": "x = 2\n"})

    code, found = run_check(repo, base, head)

    assert code == 0
    assert found["error"] == set()
    assert found["warning"] == {"changelog.d/stale.md", "changelog.d/old.md"}
    assert len(found["unlocated"]) == 1
    assert "adds no changelog fragment" in found["unlocated"][0]


def test_a_type_added_in_the_same_pull_request_counts(repo):
    pyproject = PYPROJECT.replace(
        '[[tool.towncrier.type]]\ndirectory = "removed"',
        '[[tool.towncrier.type]]\ndirectory = "security"\nname = "Security"\n'
        'showcontent = true\n\n[[tool.towncrier.type]]\ndirectory = "removed"',
    )
    assert pyproject != PYPROJECT
    base, head = commit(
        repo,
        files={
            "pyproject.toml": pyproject,
            "changelog.d/patch.security.md": "Patched.\n",
        },
    )

    code, found = run_check(repo, base, head)

    assert code == 0
    assert found["error"] == set()


def test_a_missing_towncrier_config_is_a_usage_error(repo):
    base, head = commit(repo, files={"pyproject.toml": '[project]\nname = "x"\n'})

    code, found = run_check(repo, base, head)

    assert code == 2


def test_annotations_escape_github_command_characters():
    assert check.annotation("error", "a,b:c.md", "is 50%\nwrong") == (
        "::error file=a%2Cb%3Ac.md::a,b:c.md is 50%25%0Awrong"
    )


# 7. The version bump

UNTYPED_NAMES = FILE_NAMES.filter(
    lambda name: (
        towncrier_parse(name, CONFIG.types) is None
        and not bump.is_ignored(name, CONFIG)
    )
)


def expected_bump(types):
    types = set(types)
    if "breaking" in types:
        return "major"
    if {"added", "removed"} & types:
        return "minor"
    return "patch"


@settings(max_examples=150, deadline=None)
@given(
    typed=st.lists(st.tuples(SLUGS, st.sampled_from(CONFIG.types)), max_size=6),
    untyped=st.lists(UNTYPED_NAMES, max_size=4),
)
def test_the_bump_depends_only_on_typed_fragments(typed, untyped):
    # File names that differ only in case are one file on macOS; keep the first.
    seen, kinds, untyped_files = set(), [], []
    for slug, kind in typed:
        name = f"{slug}.{kind}.md"
        if name.lower() not in seen:
            seen.add(name.lower())
            kinds.append((name, kind))
    for name in untyped:
        if name.lower() not in seen:
            seen.add(name.lower())
            untyped_files.append(name)
    with tempfile.TemporaryDirectory() as tmp:
        directory = Path(tmp)
        for name in [name for name, _ in kinds] + untyped_files:
            (directory / name).write_text("A note.\n")
        out = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
            if kinds:
                result = bump.infer_bump(directory, CONFIG)
            else:
                with pytest.raises(SystemExit) as exit_info:
                    bump.infer_bump(directory, CONFIG)
    if kinds:
        assert result == expected_bump(kind for _, kind in kinds)
    else:
        assert exit_info.value.code == 1
    assert out.getvalue().count("::warning file=") == len(untyped_files)


def run_bump_script(tmp_path, fragments):
    (tmp_path / ".github").mkdir()
    shutil.copy(BUMP_SCRIPT, tmp_path / ".github" / "bump_version.py")
    (tmp_path / "pyproject.toml").write_text(PYPROJECT)
    if (REPO_ROOT / "uv.lock").exists():
        # A release also moves the lock's own version when the script does.
        shutil.copy(REPO_ROOT / "uv.lock", tmp_path / "uv.lock")
    (tmp_path / "changelog.d").mkdir()
    (tmp_path / "changelog.d" / ".gitkeep").write_text("")
    for name, text in fragments.items():
        (tmp_path / "changelog.d" / name).write_text(text)
    before = tomllib.loads(PYPROJECT)["project"]["version"]
    result = subprocess.run(
        [sys.executable, ".github/bump_version.py"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    after = tomllib.loads((tmp_path / "pyproject.toml").read_text())["project"][
        "version"
    ]
    return result, before, after


def test_only_untyped_files_is_nothing_to_release(tmp_path):
    result, before, after = run_bump_script(
        tmp_path, {"1005.md": "Untyped.\n", "notes.md": "Untyped.\n"}
    )

    assert result.returncode == 1
    assert after == before
    assert result.stdout.count("::warning file=changelog.d/") == 2
    assert "No changelog fragments with a towncrier type" in result.stderr


def test_untyped_files_do_not_change_the_bump(tmp_path):
    result, before, after = run_bump_script(
        tmp_path, {"1005.md": "Untyped.\n", "feature.added.md": "Added it.\n"}
    )

    assert result.returncode == 0, result.stderr
    major, minor, _ = (int(part) for part in before.split("."))
    assert after == f"{major}.{minor + 1}.0"
    assert "::warning file=changelog.d/1005.md::" in result.stdout
