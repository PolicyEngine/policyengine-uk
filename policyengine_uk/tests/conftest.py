import argparse
import gc
import hashlib
import os
import re
import sys
import weakref

import pytest
from policyengine_core.taxbenefitsystems import TaxBenefitSystem

DEFAULT_TEST_DATASET_URL = (
    "hf://policyengine/policyengine-uk-data-private/enhanced_frs_2023_24.h5@1.40.3"
)

if os.environ.get("HUGGING_FACE_TOKEN") and not os.environ.get(
    "POLICYENGINE_UK_DEFAULT_DATASET"
):
    os.environ["POLICYENGINE_UK_DEFAULT_DATASET"] = DEFAULT_TEST_DATASET_URL


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


def pytest_report_header(config):
    shard = config.getoption("shard", default=None)
    if shard is not None:
        return f"shard: {shard[0]} of {shard[1]}, chosen by node id"


def pytest_collection_modifyitems(config, items):
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

    has_default_dataset = bool(os.environ.get("POLICYENGINE_UK_DEFAULT_DATASET"))
    if has_default_dataset:
        return

    skip_microsimulation = pytest.mark.skip(
        reason=(
            "Requires POLICYENGINE_UK_DEFAULT_DATASET or HUGGING_FACE_TOKEN "
            "for microsimulation dataset access"
        )
    )
    for item in items:
        if "microsimulation" in item.keywords:
            item.add_marker(skip_microsimulation)


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


def pytest_configure(config):
    global _threshold_before
    _owners_at_start.update(_variable_module_owners())
    _threshold_before = gc.get_threshold()
    gc.set_threshold(GC_FIRST_GENERATION_THRESHOLD, *_threshold_before[1:])


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


@pytest.fixture(autouse=True)
def _release_variable_modules_of_dead_systems():
    yield
    release_dead_variable_modules()
