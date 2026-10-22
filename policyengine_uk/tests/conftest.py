import argparse
import ctypes
import gc
import hashlib
import importlib.util
import os
import re
import sys
import weakref
from dataclasses import dataclass
from importlib.machinery import SourceFileLoader
from pathlib import Path
from typing import Mapping, Optional

import pytest
from policyengine_core.taxbenefitsystems import TaxBenefitSystem

from policyengine_uk.utils.aggregate_impact.dataset import load_pin, materialise

# Microsimulation tests run on one certified dataset, pinned by commit and
# SHA-256 in certified_dataset.yaml. Found through the package, not beside this
# file: CI's own tests run copies of this conftest from other directories.
CERTIFIED_DATASET_PIN = (
    Path(importlib.util.find_spec("policyengine_uk").origin).parent
    / "tests"
    / "certified_dataset.yaml"
)
CERTIFIED_DATASET = load_pin(CERTIFIED_DATASET_PIN)
DEFAULT_TEST_DATASET_URL = CERTIFIED_DATASET.uri

DATASET_ENV_VAR = "POLICYENGINE_UK_DEFAULT_DATASET"
TOKEN_ENV_VAR = "HUGGING_FACE_TOKEN"
# Mandatory-data mode, for CI jobs that must run the microsimulation tests:
# with it set, a test that needs data fails when the certified dataset is
# unavailable, instead of being skipped, and runs only on that dataset.
REQUIRE_DATA_ENV_VAR = "POLICYENGINE_UK_REQUIRE_TEST_DATA"
_TRUE = {"1", "true", "yes", "on"}
_FALSE = {"", "0", "false", "no", "off"}


@dataclass(frozen=True)
class TestDataPlan:
    """What the microsimulation tests run on, decided from the environment."""

    __test__ = False  # not a test class

    action: str  # "run", "skip" or "fail"
    dataset: Optional[str]
    pinned: bool
    mandatory: bool
    reason: str


def plan_test_data(env: Mapping[str, str], pinned_uri: str) -> TestDataPlan:
    """Decide how microsimulation tests get their data.

    - An explicit ``POLICYENGINE_UK_DEFAULT_DATASET`` wins; in mandatory mode
      it must be the pinned certified dataset.
    - Otherwise a Hugging Face token selects the pinned certified dataset.
    - Otherwise the tests skip, or in mandatory mode fail.

    An unrecognised mandatory-mode value fails closed.
    """
    flag = str(env.get(REQUIRE_DATA_ENV_VAR, "")).strip().lower()
    explicit = env.get(DATASET_ENV_VAR) or None
    token = env.get(TOKEN_ENV_VAR) or None
    if flag not in _TRUE | _FALSE:
        return TestDataPlan(
            "fail",
            explicit,
            False,
            True,
            f"{REQUIRE_DATA_ENV_VAR}={env.get(REQUIRE_DATA_ENV_VAR)!r} is not a "
            "recognised true or false value",
        )
    mandatory = flag in _TRUE
    if explicit:
        pinned = explicit == pinned_uri
        if mandatory and not pinned:
            return TestDataPlan(
                "fail",
                explicit,
                False,
                True,
                f"mandatory-data mode runs only on the pinned certified dataset "
                f"{pinned_uri}, not {explicit}",
            )
        return TestDataPlan(
            "run",
            explicit,
            pinned,
            mandatory,
            "pinned certified dataset" if pinned else "dataset set explicitly",
        )
    if token:
        return TestDataPlan(
            "run", pinned_uri, True, mandatory, "pinned certified dataset"
        )
    if mandatory:
        return TestDataPlan(
            "fail",
            None,
            False,
            True,
            f"mandatory-data mode needs {TOKEN_ENV_VAR} (or {DATASET_ENV_VAR} set "
            "to the pinned certified dataset)",
        )
    return TestDataPlan(
        "skip",
        None,
        False,
        False,
        f"Requires {DATASET_ENV_VAR} or {TOKEN_ENV_VAR} for microsimulation "
        "dataset access",
    )


TEST_DATA_PLAN = plan_test_data(os.environ, DEFAULT_TEST_DATASET_URL)

if TEST_DATA_PLAN.action == "run" and not os.environ.get(DATASET_ENV_VAR):
    os.environ[DATASET_ENV_VAR] = TEST_DATA_PLAN.dataset


_verification: dict = {}


def verify_certified_dataset() -> Optional[str]:
    """Fetch the pinned dataset once per process and check its SHA-256.

    Returns None when the file matches, or why it could not be verified.
    """
    if "problem" not in _verification:
        try:
            materialise(CERTIFIED_DATASET)
            _verification["problem"] = None
        except Exception as error:  # noqa: BLE001 - every cause fails the tests
            _verification["problem"] = (
                f"The pinned certified dataset {CERTIFIED_DATASET.describe()} could "
                f"not be fetched and verified: {type(error).__name__}: {error}"
            )
    return _verification["problem"]


# Test files that read the unpinned latest dataset on purpose, to notice when
# a new data release breaks the model. They are data tests (they need
# credentials, and fail without them in mandatory mode), but what they run on
# is by design not the pinned certified dataset.
UNPINNED_BY_DESIGN = ("test_latest_data_smoke.py",)


def needs_data(item) -> bool:
    """Whether a test carries the microsimulation marker.

    The marker, not the keyword: keywords include directory names, which
    would sweep in the data-free tests under ``microsimulation/``.
    """
    return item.get_closest_marker("microsimulation") is not None


def runs_on_unpinned_data(item) -> bool:
    return item.path.name in UNPINNED_BY_DESIGN


def pytest_report_header(config):
    plan = TEST_DATA_PLAN
    mode = "mandatory" if plan.mandatory else "optional"
    target = CERTIFIED_DATASET.describe() if plan.pinned else (plan.dataset or "none")
    lines = [
        f"microsimulation data ({mode}): {plan.action} on {target} ({plan.reason})",
        "unpinned by design: " + ", ".join(UNPINNED_BY_DESIGN),
    ]
    shard = config.getoption("shard", default=None)
    if shard is not None:
        lines.append(f"shard: {shard[0]} of {shard[1]}, chosen by node id")
    return lines


@pytest.fixture(scope="module")
def cloned_uk_tax_benefit_system():
    """Load model code once, with independent model state per simulation."""
    import policyengine_uk.simulation as uk_simulation

    tax_benefit_system = uk_simulation.CountryTaxBenefitSystem()
    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.setattr(
            uk_simulation, "CountryTaxBenefitSystem", tax_benefit_system.clone
        )
        yield


# CI splits the suite over several runners with ``--shard K/N``. The shard of a
# test is a function of its node id alone, so the shards partition whatever is
# collected: every test runs in exactly one of them, including a test added
# later. The Test job checks that on each run (.github/check_test_shards.py).
def shard_of(nodeid: str, shards: int) -> int:
    """The shard, from 1 to ``shards``, that runs the test ``nodeid``.

    Uses SHA-256 rather than ``hash``, which Python salts per process: every
    runner and every pytest-xdist worker must give the same answer.
    """
    digest = hashlib.sha256(nodeid.encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big") % shards + 1


def parse_shard(value: str) -> tuple[int, int]:
    """Parse ``K/N`` into ``(K, N)``, requiring 1 <= K <= N."""
    match = re.fullmatch(r"([0-9]+)/([0-9]+)", value)
    if match:
        shard, shards = int(match.group(1)), int(match.group(2))
        if 1 <= shard <= shards:
            return shard, shards
    raise argparse.ArgumentTypeError(
        f"expected K/N with 1 <= K <= N, such as 1/3; got {value!r}"
    )


def pytest_addoption(parser):
    parser.addoption(
        "--shard",
        type=parse_shard,
        default=None,
        metavar="K/N",
        help="Run only shard K of N. Every test is in exactly one shard.",
    )


def pytest_collection_modifyitems(config, items):
    """Select this run's shard; without data, data tests skip unless mandatory."""
    shard = config.getoption("shard", default=None)
    if shard is not None:
        this_shard, shards = shard
        selected, deselected = [], []
        for item in items:
            if shard_of(item.nodeid, shards) == this_shard:
                selected.append(item)
            else:
                deselected.append(item)
        items[:] = selected
        if deselected:
            config.hook.pytest_deselected(items=deselected)

    if TEST_DATA_PLAN.action != "skip":
        return
    skip = pytest.mark.skip(reason=TEST_DATA_PLAN.reason)
    for item in items:
        if needs_data(item):
            item.add_marker(skip)


@pytest.hookimpl(tryfirst=True)
def pytest_runtest_setup(item):
    """Fail data tests in mandatory mode without data; verify pinned bytes.

    A failure here is reported as an error in the test's setup, so the run
    fails rather than passing with the test unexecuted. The hook runs before
    pytest's own skip handling, so a skip marker on a data test cannot turn
    missing data into a skip.
    """
    if not needs_data(item):
        return
    plan = TEST_DATA_PLAN
    if plan.action == "fail":
        pytest.fail(
            f"Mandatory-data mode: {plan.reason}. This test needs the certified "
            "dataset and must not be skipped.",
            pytrace=False,
        )
    if plan.action == "run" and plan.pinned and not runs_on_unpinned_data(item):
        problem = verify_certified_dataset()
        if problem:
            pytest.fail(problem, pytrace=False)


# Garbage collection. Most of the suite's time is in the property tests (the 51
# *_properties.py files took 74% of pytest worker time on 10 October 2026), and
# each of their examples builds a Simulation, which loads about 1,100 variable
# modules again and clones the parameter tree. Python's cycle collector starts
# a collection every 2,000 net allocations of tracked objects (the default in
# CPython 3.13, which CI uses), and its full collections walk every tracked
# object in the process, including the 430,000 or so present once
# policyengine_uk is imported. Each process that runs tests (every
# pytest-xdist worker) therefore:
#
# - starts a collection every 10,000 net allocations instead
#   (GC_FIRST_GENERATION_THRESHOLD, set at start-up; the other thresholds keep
#   the interpreter's defaults);
# - freezes every object that exists once the tests are collected
#   (gc.freeze(), about 1.6 million objects per worker): the modules, the
#   tax-benefit systems built at import and the collected tests. The collector
#   never scans frozen objects, so frozen objects in reference cycles that
#   later become garbage are not freed until they are unfrozen (objects outside
#   cycles still go with their last reference). A tax-benefit system and its
#   variable modules are such cycles, so no system may be built and dropped
#   while the tests are collected (test_variable_module_release.py checks
#   this); build one in a fixture or on first use, not at import. Objects
#   created by tests are collected as before.
#
# Measured on CI on 11 October 2026 (runs and numbers in PR #2317): the
# workers' CPU time, summed over the three shards, fell from 204 to 172
# minutes, and their time in the collector from 83 to 55; the slowest shard
# took 20 minutes instead of 24. The runner's memory was already full on two
# shards under every setting; on the third, the largest worker's peak rose from
# 5.3 to 5.7 GiB. Freezing alone saved nothing, the threshold alone saved 13
# minutes of worker CPU, and with a threshold of 25,000 two of the three
# runners shut down. Every test had the same outcome under each setting: this
# changes when memory is reclaimed, not which tests run or what they compute.
GC_FIRST_GENERATION_THRESHOLD = 10_000

# gc.get_objects() leaves out frozen objects, so release_dead_variable_modules
# looks up the systems that were frozen here.
_FROZEN_SYSTEMS = weakref.WeakSet()
# Owners of variable modules whose system was built and had died by the
# freeze, and the owners already loaded when the session started (a process
# that runs pytest more than once keeps the previous session's).
_DEAD_AT_FREEZE = set()
_owners_at_start = set()
_heap_frozen = False
_threshold_before = None


def _ignore_hypothesis_local_constants():
    """Stop Hypothesis drawing literal constants from policyengine_uk's code.

    Hypothesis biases its draws with literals from modules it counts as local,
    and it does not count anything under site-packages. Run from the source
    tree, policyengine_uk's modules are local; run from the installed wheel
    (Release test), they are not. The same derandomized seed then generates
    different examples in pull request checks and in Release test, so a
    failure can appear only at release (issue #2397). With no local constants,
    both draw the same examples. test_hypothesis_environment.py checks this
    still takes effect.
    """
    from hypothesis.internal.conjecture import providers

    if not hasattr(providers, "_get_local_constants"):
        raise RuntimeError(
            "hypothesis.internal.conjecture.providers._get_local_constants no "
            "longer exists; update _ignore_hypothesis_local_constants for this "
            "Hypothesis version."
        )
    no_local_constants = providers.Constants()
    providers._get_local_constants = lambda: no_local_constants
    providers.CONSTANTS_CACHE.cache.clear()


def pytest_configure(config):
    global _threshold_before
    _ignore_hypothesis_local_constants()
    _owners_at_start.update(_variable_module_owners())
    _threshold_before = gc.get_threshold()
    gc.set_threshold(GC_FIRST_GENERATION_THRESHOLD, *_threshold_before[1:])
    # The variable code and module hooks defined below. pytest_configure, unlike
    # pytest_sessionstart, also reaches a conftest that pytest finds only while
    # collecting (a bare `pytest` from the repository root).
    _install_variable_hooks()


@pytest.hookimpl(trylast=True)
def pytest_collection_finish(session):
    global _heap_frozen
    if _heap_frozen:
        return
    gc.collect()
    systems = [obj for obj in gc.get_objects() if isinstance(obj, TaxBenefitSystem)]
    _FROZEN_SYSTEMS.update(systems)
    _DEAD_AT_FREEZE.update(
        set(_variable_module_owners())
        - {str(id(system)) for system in systems}
        - _owners_at_start
    )
    gc.freeze()
    _heap_frozen = True


def pytest_unconfigure(config):
    # Undo the freeze and threshold for a process that runs pytest in-process
    # (an IDE, a REPL). gc.unfreeze() also unfreezes anything frozen before
    # the session.
    global _heap_frozen
    if _heap_frozen:
        gc.unfreeze()
        _FROZEN_SYSTEMS.clear()
        _heap_frozen = False
    _DEAD_AT_FREEZE.clear()
    _owners_at_start.clear()
    if _threshold_before is not None:
        gc.set_threshold(*_threshold_before)
    _remove_variable_hooks()


# policyengine-core loads every variable file of each new tax-benefit system as
# a module named "<id(system)>_<path hash>_<file name>" and registers it in
# sys.modules, where it stays after the system is garbage collected. Every
# Simulation builds its own system, so each one leaves about 1,000 modules
# (roughly 10 MB) behind, and the property tests build hundreds: running the
# suite serially used 99% of a 16 GB CI runner's memory. After each test, drop
# the modules of systems that no longer exist; live systems keep theirs.
# Remove this once policyengine-core stops leaking them
# (PolicyEngine/policyengine-core#520).
_VARIABLE_MODULE_NAME = re.compile(r"(\d+)_-?\d+_")


def _variable_module_owners() -> dict:
    """Map each owner id in loaded variable module names to those names."""
    owners = {}
    for name in list(sys.modules):
        match = _VARIABLE_MODULE_NAME.match(name)
        if match:
            owners.setdefault(match.group(1), []).append(name)
    return owners


def release_dead_variable_modules(max_owners: int = 8) -> int:
    """Remove dead tax-benefit systems' variable modules from sys.modules.

    Does nothing while at most ``max_owners`` systems own loaded variable
    modules, since finding the live systems scans every tracked object.
    Returns the number of modules removed.
    """
    owners = _variable_module_owners()
    if len(owners) <= max_owners:
        return 0
    gc.collect()
    live = {
        str(id(obj)) for obj in gc.get_objects() if isinstance(obj, TaxBenefitSystem)
    }
    live.update(str(id(system)) for system in _FROZEN_SYSTEMS)
    released = 0
    for owner, names in owners.items():
        if owner not in live:
            for name in names:
                if sys.modules.pop(name, None) is not None:
                    released += 1
    return released


# A test or a new system triggers the release only once more than ``max_new``
# systems own modules beyond those alive at the last release, so a process
# that keeps more than eight systems alive (an lru_cache of systems in a test
# module) doesn't scan every tracked object after every test and every build.
_live_owners = 0


def release_after_new_systems(max_new: int = 8) -> int:
    """Release dead systems' variable modules once more than ``max_new`` systems
    own modules beyond those alive at the last release. Returns the number
    removed."""
    global _live_owners
    if len(_variable_module_owners()) <= _live_owners + max_new:
        return 0
    released = release_dead_variable_modules(max_owners=0)
    _live_owners = len(_variable_module_owners())
    return released


@pytest.fixture(autouse=True)
def _release_variable_modules_of_dead_systems():
    yield
    release_after_new_systems()


# Coverage on CI is measured with sys.monitoring (COVERAGE_CORE=sysmon). That
# core keeps every code object it has seen alive until the process exits, so
# that it can key its records by id(code) (SysMonitor.code_objects in
# coverage/sysmon.py). policyengine-core compiles a system's variable files
# again for every new system, into new code objects, and every Simulation
# builds a new system, so each Simulation left about 2,500 code objects that
# were never freed. By the end of a CI shard each pytest-xdist worker's
# coverage held 0.8 to 1.5 million of them, and the shards peaked at 14.4 to
# 15.3 GiB of the runner's 15.6, using up to 1.8 GiB of swap (run 38159894687).
#
# A file's code object does not depend on the system that runs it, so each
# process compiles each variable file once and every later system runs that
# code object. Systems still get their own modules, classes and functions;
# only the immutable code is shared. In the same run this lowered the shards'
# peaks to 10.2 to 12.2 GiB with no swap, cut their pytest time by 15 to 21%,
# and left every test's outcome unchanged. Remove _get_variable_code once
# policyengine-core shares the code itself (PolicyEngine/policyengine-core#608).
_variable_code = {}
_get_code = SourceFileLoader.get_code
_get_code_was_own = "get_code" in SourceFileLoader.__dict__


def _get_variable_code(loader, fullname):
    """``SourceFileLoader.get_code``, compiling each variable file only once."""
    if not _VARIABLE_MODULE_NAME.match(fullname):
        return _get_code(loader, fullname)
    path = loader.get_filename(fullname)
    stat = os.stat(path)
    key = (path, stat.st_mtime_ns, stat.st_size)
    code = _variable_code.get(key)
    if code is None:
        code = _variable_code[key] = _get_code(loader, fullname)
    return code


# Dead systems' variable modules are also released as each new system starts
# adding its variables, not only after each test: in that run one property
# test had 165 systems' modules loaded at once, and Hypothesis can build many
# more while it shrinks a failing example. With an earlier form of this
# release, which scanned at every new system once more than eight systems
# owned modules, the shards peaked at 10.0-10.4 GiB (run 38165445604), against
# 10.2-12.2 with code sharing alone (run 38159894687). Keep this until
# policyengine-core stops leaking the modules
# (PolicyEngine/policyengine-core#520).
_add_variables_from_file = TaxBenefitSystem.add_variables_from_file
_adding_system = None


def _add_variables_from_file_releasing(system, file_path):
    """``TaxBenefitSystem.add_variables_from_file``, releasing dead systems'
    modules when a new system starts adding its variables."""
    global _adding_system
    if id(system) != _adding_system:
        # A system adds all its variable files in turn, so this is a new one.
        _adding_system = id(system)
        release_after_new_systems()
    return _add_variables_from_file(system, file_path)


def _install_variable_hooks():
    SourceFileLoader.get_code = _get_variable_code
    TaxBenefitSystem.add_variables_from_file = _add_variables_from_file_releasing


def _remove_variable_hooks():
    if _get_code_was_own:
        SourceFileLoader.get_code = _get_code
    elif "get_code" in SourceFileLoader.__dict__:
        # Inherited from SourceLoader: leave no copy on the subclass.
        del SourceFileLoader.get_code
    TaxBenefitSystem.add_variables_from_file = _add_variables_from_file


# Freed memory stays in the worker: on CI the worker that ran the
# microsimulation tests kept about 4 GiB of RSS after their simulations were
# gone (run 38159894687), though locally only the 0.74 GiB cached dataset was
# still referenced once they were deleted (tracemalloc). So after each test
# file's fixtures are torn down, ask glibc to return free heap memory to the
# system (malloc_trim(0)); memory still awaiting the cycle collector goes back
# at a later file. Elsewhere this does nothing. With this, and
# test_latest_data_smoke.py no longer keeping its dataset cached, the shards
# peaked at 8.0 to 8.2 GiB instead of 10.0 to 10.4, in about the same time
# (pytest wall 776 / 952 / 637 s against 788 / 902 / 581), and two shards
# would peak at 8.1 (run 38165445604). With everything in this file the three
# shards peaked at 7.6 to 8.7 GiB (run 38173323996).
try:
    _malloc_trim = ctypes.CDLL("libc.so.6").malloc_trim
    _malloc_trim.argtypes = [ctypes.c_size_t]
    _malloc_trim.restype = ctypes.c_int
except (OSError, AttributeError):
    _malloc_trim = None


@pytest.hookimpl(trylast=True)
def pytest_runtest_teardown(item, nextitem):
    # trylast: after pytest's own teardown, which finalizes the file's fixtures
    # when the next test is in another file.
    if _malloc_trim is not None and (nextitem is None or nextitem.path != item.path):
        _malloc_trim(0)
