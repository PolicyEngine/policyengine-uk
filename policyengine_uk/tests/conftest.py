import argparse
import gc
import hashlib
import os
import re
import sys

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


def release_dead_variable_modules(max_owners: int = 8) -> int:
    """Remove dead tax-benefit systems' variable modules from sys.modules.

    Does nothing while at most ``max_owners`` systems own loaded variable
    modules, since finding the live systems scans every tracked object.
    Returns the number of modules removed.
    """
    owners = {}
    for name in list(sys.modules):
        match = _VARIABLE_MODULE_NAME.match(name)
        if match:
            owners.setdefault(match.group(1), []).append(name)
    if len(owners) <= max_owners:
        return 0
    gc.collect()
    live = {
        str(id(obj)) for obj in gc.get_objects() if isinstance(obj, TaxBenefitSystem)
    }
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
