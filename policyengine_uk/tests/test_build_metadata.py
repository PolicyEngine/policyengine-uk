import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import threading
import tomllib
from unittest.mock import patch

from hypothesis import HealthCheck, example, given, settings
from hypothesis import strategies as st
import pytest

BUILD_METADATA_PATH = Path(__file__).resolve().parents[1] / "build_metadata.py"
SPEC = importlib.util.spec_from_file_location(
    "policyengine_uk_build_metadata_under_test",
    BUILD_METADATA_PATH,
)
build_metadata = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = build_metadata
SPEC.loader.exec_module(build_metadata)

get_data_build_fingerprint = build_metadata.get_data_build_fingerprint
get_data_build_metadata = build_metadata.get_data_build_metadata
get_runtime_metadata = build_metadata.get_runtime_metadata


def test_data_build_fingerprint_is_stable_within_process():
    get_data_build_fingerprint.cache_clear()

    first = get_data_build_fingerprint()
    second = get_data_build_fingerprint()

    assert first.startswith("sha256:")
    assert first == second


def test_get_runtime_metadata_includes_required_bundle_fields(monkeypatch):
    get_data_build_fingerprint.cache_clear()

    monkeypatch.setattr(build_metadata, "_get_package_version", lambda: "2.74.0")
    monkeypatch.setattr(build_metadata, "_get_git_sha", lambda: "deadbeef")
    monkeypatch.setattr(
        build_metadata,
        "get_data_build_fingerprint",
        lambda: "sha256:fingerprint",
    )
    monkeypatch.setattr(
        build_metadata,
        "get_core_runtime_metadata",
        lambda: {
            "name": "policyengine-core",
            "version": "3.26.0",
            "git_sha": "coredeadbeef",
        },
    )

    metadata = get_runtime_metadata()

    assert metadata["name"] == "policyengine-uk"
    assert metadata["version"] == "2.74.0"
    assert metadata["git_sha"] == "deadbeef"
    assert metadata["data_build_fingerprint"] == "sha256:fingerprint"
    assert metadata["core"] == {
        "name": "policyengine-core",
        "version": "3.26.0",
        "git_sha": "coredeadbeef",
    }


def test_get_data_build_metadata_uses_runtime_metadata():
    with patch(
        f"{SPEC.name}.get_runtime_metadata",
        return_value={"name": "policyengine-uk"},
    ):
        assert get_data_build_metadata() == {"name": "policyengine-uk"}


def test_runtime_metadata_uses_bundle_contract_when_available():
    policyengine_bundles = pytest.importorskip("policyengine_bundles")

    policyengine_bundles.load_component_metadata(get_runtime_metadata())


# _get_git_sha must return policyengine-uk's own commit or None, never the HEAD
# of a repository that merely contains the install.

_get_git_sha = build_metadata._get_git_sha
_get_direct_url_git_sha = build_metadata._get_direct_url_git_sha

# The tests' own git calls must not be redirected by the caller's environment
# or shaped by the user's git configuration.
GIT_TEST_ENV = {
    **{
        key: value
        for key, value in os.environ.items()
        if key not in build_metadata.GIT_REPOSITORY_ENV_VARS
    },
    "GIT_CONFIG_GLOBAL": os.devnull,
    "GIT_CONFIG_NOSYSTEM": "1",
}
SHA = "0123456789abcdef0123456789abcdef01234567"


def _git(cwd: Path, *args: str) -> str:
    return subprocess.check_output(
        ["git", "-C", str(cwd), *args],
        env=GIT_TEST_ENV,
        stderr=subprocess.DEVNULL,
        text=True,
    ).strip()


def _commit(repo: Path, message: str) -> str:
    _git(repo, "add", "-A")
    _git(
        repo,
        "-c",
        "user.name=Test",
        "-c",
        "user.email=test@example.com",
        "commit",
        "-q",
        "--allow-empty",
        "-m",
        message,
    )
    return _git(repo, "rev-parse", "HEAD")


def _init_repo(repo: Path, project_name: str | None) -> str:
    """Create a git repository with one commit and return its HEAD."""
    repo.mkdir(parents=True, exist_ok=True)
    _git(repo, "init", "-q")
    if project_name is not None:
        (repo / "pyproject.toml").write_text(f'[project]\nname = "{project_name}"\n')
    # The message keeps commits in different repositories distinct.
    return _commit(repo, str(repo))


def _make_package(parent: Path) -> Path:
    package_root = parent / "policyengine_uk"
    package_root.mkdir(parents=True, exist_ok=True)
    (package_root / "__init__.py").write_text("")
    return package_root


def _make_policyengine_uk_checkout(checkout: Path) -> tuple[Path, str]:
    package_root = _make_package(checkout)
    return package_root, _init_repo(checkout, "policyengine-uk")


def _install_with_direct_url(site_packages: Path, direct_url: object) -> Path:
    """Lay out an installed policyengine-uk with an installer record."""
    package_root = _make_package(site_packages)
    dist_info = site_packages / "policyengine_uk-2.0.0.dist-info"
    dist_info.mkdir()
    (dist_info / "METADATA").write_text(
        "Metadata-Version: 2.1\nName: policyengine-uk\nVersion: 2.0.0\n"
    )
    if direct_url is not None:
        (dist_info / "direct_url.json").write_text(
            direct_url if isinstance(direct_url, str) else json.dumps(direct_url)
        )
    return package_root


def test_git_sha_ignores_enclosing_repository(tmp_path):
    # The policyengine-uk-data build: policyengine-uk installed into a
    # virtualenv inside the uk-data checkout.
    uk_data = tmp_path / "policyengine-uk-data"
    _init_repo(uk_data, "policyengine-uk-data")
    package_root = _make_package(uk_data / ".venv/lib/python3.13/site-packages")

    assert _get_git_sha(package_root) is None


def test_git_sha_ignores_enclosing_policyengine_uk_checkout(tmp_path):
    # A non-editable install can be built from any commit, so the HEAD of a
    # policyengine-uk checkout that holds the virtualenv is not evidence.
    checkout = tmp_path / "policyengine-uk"
    _init_repo(checkout, "policyengine-uk")
    package_root = _make_package(checkout / ".venv/lib/python3.13/site-packages")

    assert _get_git_sha(package_root) is None


@pytest.mark.parametrize("project_name", ["deployment", None])
def test_git_sha_ignores_repository_that_vendors_the_package(tmp_path, project_name):
    # For example `pip install --target .` at the root of another repository.
    repo = tmp_path / "deployment"
    package_root = _make_package(repo)
    _init_repo(repo, project_name)

    assert _get_git_sha(package_root) is None


def test_git_sha_ignores_unusable_git_directory(tmp_path):
    # Git skips an empty .git directory and finds the enclosing repository.
    outer = tmp_path / "outer"
    _init_repo(outer, "outer")
    checkout = outer / "policyengine-uk"
    package_root = _make_package(checkout)
    (checkout / ".git").mkdir()
    (checkout / "pyproject.toml").write_text('[project]\nname = "policyengine-uk"\n')

    assert _get_git_sha(package_root) is None


UNREADABLE_PYPROJECTS = {
    "invalid TOML": b"[project\n",
    "Latin-1": 'authors = [{name = "Jos\xe9"}]\n'.encode("latin-1"),
    "UTF-16": '[project]\nname = "policyengine-uk"\n'.encode("utf-16"),
    "nested too deeply": b"a = " + b"[" * 100_000,
}


@pytest.mark.parametrize(
    "content", UNREADABLE_PYPROJECTS.values(), ids=UNREADABLE_PYPROJECTS.keys()
)
def test_git_sha_ignores_unreadable_pyproject(tmp_path, content):
    checkout = tmp_path / "policyengine-uk"
    package_root, _ = _make_policyengine_uk_checkout(checkout)
    (checkout / "pyproject.toml").write_bytes(content)

    assert _get_git_sha(package_root) is None


@pytest.mark.parametrize(
    "content", UNREADABLE_PYPROJECTS.values(), ids=UNREADABLE_PYPROJECTS.keys()
)
def test_git_sha_falls_back_to_installer_record_past_unreadable_pyproject(
    tmp_path, content
):
    # `pip install --target .` from git into a repository whose own
    # pyproject cannot be parsed.
    repo = tmp_path / "deployment"
    package_root = _install_with_direct_url(
        repo,
        {"url": "https://example.com", "vcs_info": {"vcs": "git", "commit_id": SHA}},
    )
    (repo / "pyproject.toml").write_bytes(content)
    _init_repo(repo, project_name=None)

    assert _get_git_sha(package_root) == SHA


@pytest.mark.skipif(not hasattr(os, "mkfifo"), reason="needs named pipes")
def test_git_sha_does_not_block_on_fifo_pyproject(tmp_path):
    checkout = tmp_path / "policyengine-uk"
    package_root = _make_package(checkout)
    _init_repo(checkout, project_name=None)
    fifo = checkout / "pyproject.toml"
    os.mkfifo(fifo)
    result = {}
    lookup = threading.Thread(
        target=lambda: result.update(sha=_get_git_sha(package_root)), daemon=True
    )
    lookup.start()
    lookup.join(timeout=30)
    if lookup.is_alive():
        # Release the blocked reader so the thread can finish.
        os.close(os.open(fifo, os.O_WRONLY | os.O_NONBLOCK))
    assert not lookup.is_alive()
    assert result["sha"] is None


def test_git_sha_reads_own_checkout_head(tmp_path):
    package_root, head = _make_policyengine_uk_checkout(tmp_path / "policyengine-uk")

    assert _get_git_sha(package_root) == head


@pytest.mark.parametrize("checkout_name", ["José", "日本語", "trailing space "])
def test_git_sha_reads_own_checkout_head_at_unusual_path(tmp_path, checkout_name):
    package_root, head = _make_policyengine_uk_checkout(tmp_path / checkout_name)

    assert _get_git_sha(package_root) == head


NON_UTF8_LOCALES = ("en_US.ISO8859-1", "en_IE.ISO8859-1", "de_DE.ISO8859-1")
LOCALE_PROBE = """
import importlib.util, sys
from pathlib import Path
spec = importlib.util.spec_from_file_location("probe", sys.argv[1])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
print(module._get_git_sha(Path(sys.argv[2])))
"""


def test_git_sha_reads_own_checkout_head_under_non_utf8_locale(tmp_path):
    # A non-ASCII checkout path must not depend on decoding git's output in
    # the locale encoding.
    package_root, head = _make_policyengine_uk_checkout(
        tmp_path / "José" / "policyengine-uk"
    )
    for name in NON_UTF8_LOCALES:
        env = {**GIT_TEST_ENV, "LC_ALL": name, "PYTHONUTF8": "0"}
        encoding = subprocess.check_output(
            [sys.executable, "-c", "import locale; print(locale.getencoding())"],
            env=env,
            text=True,
        ).strip()
        if encoding.replace("-", "").lower() != "utf8":
            break
    else:
        pytest.skip("no non-UTF-8 locale is installed")

    output = subprocess.check_output(
        [sys.executable, "-c", LOCALE_PROBE, str(BUILD_METADATA_PATH), package_root],
        env=env,
        text=True,
    )

    assert output.strip() == head


def test_git_sha_reads_own_checkout_nested_in_another_repository(tmp_path):
    outer = tmp_path / "policyengine-uk-data"
    outer_head = _init_repo(outer, "policyengine-uk-data")
    package_root, head = _make_policyengine_uk_checkout(
        outer / "vendor" / "policyengine-uk"
    )

    assert _get_git_sha(package_root) == head
    assert head != outer_head


def test_git_sha_reads_own_worktree_head(tmp_path):
    main = tmp_path / "policyengine-uk"
    _, main_head = _make_policyengine_uk_checkout(main)
    worktree = tmp_path / "policyengine-uk-feature"
    _git(main, "worktree", "add", "-q", "-b", "feature", str(worktree))
    worktree_head = _commit(worktree, "feature")

    assert (worktree / ".git").is_file()
    assert _get_git_sha(worktree / "policyengine_uk") == worktree_head
    assert worktree_head != main_head


def test_git_sha_ignores_git_environment_overrides(tmp_path, monkeypatch):
    outer = tmp_path / "outer"
    _init_repo(outer, "outer")
    package_root, head = _make_policyengine_uk_checkout(tmp_path / "policyengine-uk")
    monkeypatch.setenv("GIT_DIR", str(outer / ".git"))
    monkeypatch.setenv("GIT_WORK_TREE", str(outer))

    assert _get_git_sha(package_root) == head


def test_git_sha_is_none_before_first_commit(tmp_path):
    checkout = tmp_path / "policyengine-uk"
    package_root = _make_package(checkout)
    _git(checkout, "init", "-q")
    (checkout / "pyproject.toml").write_text('[project]\nname = "policyengine-uk"\n')

    assert _get_git_sha(package_root) is None


def test_git_sha_is_none_without_git_executable(tmp_path, monkeypatch):
    package_root, _ = _make_policyengine_uk_checkout(tmp_path / "policyengine-uk")

    def missing_git(*args, **kwargs):
        raise FileNotFoundError("git")

    monkeypatch.setattr(build_metadata.subprocess, "check_output", missing_git)

    assert _get_git_sha(package_root) is None


def test_git_sha_is_none_when_git_times_out(tmp_path, monkeypatch):
    package_root, _ = _make_policyengine_uk_checkout(tmp_path / "policyengine-uk")
    timeouts = []

    def slow_git(args, **kwargs):
        timeouts.append(kwargs.get("timeout"))
        raise subprocess.TimeoutExpired(args, kwargs.get("timeout"))

    monkeypatch.setattr(build_metadata.subprocess, "check_output", slow_git)

    assert _get_git_sha(package_root) is None
    assert timeouts and all(timeout is not None for timeout in timeouts)


def test_git_sha_reads_this_checkout_head():
    try:
        toplevel = Path(
            _git(BUILD_METADATA_PATH.parent, "rev-parse", "--show-toplevel")
        )
    except (OSError, subprocess.CalledProcessError):
        pytest.skip("policyengine-uk is not running from a git checkout")
    if not build_metadata._declares_package(toplevel / "pyproject.toml"):
        pytest.skip("the enclosing git checkout is not policyengine-uk")

    assert _get_git_sha() == _git(toplevel, "rev-parse", "HEAD")


def test_git_sha_reads_installer_record_for_git_install(tmp_path):
    package_root = _install_with_direct_url(
        tmp_path / "site-packages",
        {
            "url": "https://github.com/PolicyEngine/policyengine-uk",
            "vcs_info": {"vcs": "git", "commit_id": SHA},
        },
    )

    assert _get_git_sha(package_root) == SHA


def test_git_sha_prefers_installer_record_over_enclosing_repository(tmp_path):
    uk_data = tmp_path / "policyengine-uk-data"
    _init_repo(uk_data, "policyengine-uk-data")
    package_root = _install_with_direct_url(
        uk_data / ".venv/lib/python3.13/site-packages",
        {"url": "https://example.com", "vcs_info": {"vcs": "git", "commit_id": SHA}},
    )

    assert _get_git_sha(package_root) == SHA


@pytest.mark.parametrize(
    "direct_url",
    [
        None,
        "not json",
        [],
        {"url": "file:///src/policyengine-uk", "dir_info": {"editable": True}},
        {"url": "https://example.com/policyengine_uk.whl", "archive_info": {}},
        {"url": "https://example.com", "vcs_info": {"vcs": "hg", "commit_id": SHA}},
        {"url": "https://example.com", "vcs_info": {"vcs": "git"}},
        {"url": "https://example.com", "vcs_info": {"vcs": "git", "commit_id": "main"}},
        {"url": "https://example.com", "vcs_info": "git"},
    ],
)
def test_git_sha_ignores_installer_records_without_git_commit(tmp_path, direct_url):
    package_root = _install_with_direct_url(tmp_path / "site-packages", direct_url)

    assert _get_git_sha(package_root) is None


def test_git_sha_ignores_installer_record_of_another_copy(tmp_path, monkeypatch):
    other_site_packages = tmp_path / "other-site-packages"
    _install_with_direct_url(
        other_site_packages,
        {"url": "https://example.com", "vcs_info": {"vcs": "git", "commit_id": SHA}},
    )
    # A lookup across sys.path would find the other copy first.
    monkeypatch.syspath_prepend(str(other_site_packages))
    package_root = _make_package(tmp_path / "site-packages")

    assert _get_git_sha(package_root) is None


# Property: for any directory layout, the sha is the HEAD of a repository
# rooted at the package's parent whose pyproject names policyengine-uk, or None.

PATH_SEGMENTS = st.one_of(
    st.sampled_from(
        [
            ".venv",
            "venv",
            "lib",
            "python3.13",
            "site-packages",
            "dist-packages",
            "src",
            "vendor",
            "build",
            "policyengine-uk",
            "policyengine_uk",
            "José",
            "trailing space ",
        ]
    ),
    # No dots, so a segment can never be ".git", "." or "pyproject.toml".
    st.text(alphabet="abcdefghijklmnopqrstuvwxyz0123456789-_", min_size=1, max_size=8),
)
PROPERTY_SETTINGS = settings(
    max_examples=40,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
)


@PROPERTY_SETTINGS
@given(
    project_name=st.sampled_from(
        [None, "policyengine-uk", "policyengine_uk", "policyengine-uk-data"]
    ),
    segments=st.lists(PATH_SEGMENTS, max_size=4),
)
def test_git_sha_property_only_own_checkout_root(
    tmp_path_factory, project_name, segments
):
    repo = tmp_path_factory.mktemp("repo")
    package_root = _make_package(repo.joinpath(*segments))
    head = _init_repo(repo, project_name)
    is_own_checkout = not segments and project_name in {
        "policyengine-uk",
        "policyengine_uk",
    }

    assert _get_git_sha(package_root) == (head if is_own_checkout else None)


@PROPERTY_SETTINGS
@given(segments=st.lists(PATH_SEGMENTS, max_size=4))
def test_git_sha_property_nested_checkout_reports_itself(tmp_path_factory, segments):
    outer = tmp_path_factory.mktemp("outer")
    outer_head = _init_repo(outer, "policyengine-uk-data")
    package_root, head = _make_policyengine_uk_checkout(
        outer.joinpath(*segments, "checkout")
    )

    assert _get_git_sha(package_root) == head != outer_head


JSON_VALUES = st.recursive(
    st.none() | st.booleans() | st.integers() | st.text(max_size=8),
    lambda children: (
        st.lists(children, max_size=3)
        | st.dictionaries(st.text(max_size=8), children, max_size=3)
    ),
    max_leaves=8,
)
COMMIT_IDS = st.one_of(
    st.text(alphabet="0123456789abcdef", min_size=40, max_size=40),
    st.text(alphabet="0123456789abcdef", min_size=64, max_size=64),
    st.text(alphabet="0123456789abcdefABCDEF", max_size=70),
    JSON_VALUES,
)
DIRECT_URLS = st.one_of(
    JSON_VALUES,
    st.fixed_dictionaries(
        {
            "url": st.text(max_size=8),
            "vcs_info": st.one_of(
                JSON_VALUES,
                st.fixed_dictionaries(
                    {
                        "vcs": st.sampled_from(["git", "hg", "svn", "bzr", "GIT"]),
                        "commit_id": COMMIT_IDS,
                    }
                ),
            ),
        }
    ),
)


@PROPERTY_SETTINGS
@given(direct_url=DIRECT_URLS)
def test_git_sha_property_installer_record_never_invents_a_sha(
    tmp_path_factory, direct_url
):
    package_root = _install_with_direct_url(
        tmp_path_factory.mktemp("site-packages"), json.dumps(direct_url)
    )
    vcs_info = direct_url.get("vcs_info") if isinstance(direct_url, dict) else None
    commit_id = vcs_info.get("commit_id") if isinstance(vcs_info, dict) else None
    is_git_commit = (
        isinstance(vcs_info, dict)
        and vcs_info.get("vcs") == "git"
        and isinstance(commit_id, str)
        and len(commit_id) in {40, 64}
        and set(commit_id) <= set("0123456789abcdef")
    )

    assert _get_direct_url_git_sha(package_root) == (
        commit_id if is_git_commit else None
    )


@pytest.fixture(scope="module")
def reusable_checkout(tmp_path_factory):
    checkout = tmp_path_factory.mktemp("reusable") / "policyengine-uk"
    package_root, head = _make_policyengine_uk_checkout(checkout)
    return checkout, package_root, head


@PROPERTY_SETTINGS
@given(content=st.binary(max_size=200))
@example(content=b'[project]\nname = "policyengine-uk"\n')
@example(content='[project]\nname = "Jos\xe9"\n'.encode("latin-1"))
@example(content='[project]\nname = "policyengine-uk"\n'.encode("utf-16"))
@example(content=b"a = " + b"[" * 100_000)
@example(content=b"a = " + b"9" * 5_000)
def test_git_sha_property_any_pyproject_bytes_never_raise(reusable_checkout, content):
    checkout, package_root, head = reusable_checkout
    (checkout / "pyproject.toml").write_bytes(content)
    try:
        project = tomllib.loads(content.decode()).get("project")
        name = project.get("name") if isinstance(project, dict) else None
    except Exception:
        name = None

    declares_package = (
        isinstance(name, str)
        and re.sub(r"[-_.]+", "-", name).lower() == "policyengine-uk"
    )

    assert _get_git_sha(package_root) == (head if declares_package else None)
