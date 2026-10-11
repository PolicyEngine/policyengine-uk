import gc
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Optional

import pytest
from policyengine_core.taxbenefitsystems import TaxBenefitSystem

from policyengine_uk.utils.aggregate_impact.dataset import load_pin, materialise

# Microsimulation tests run on one certified dataset, pinned by commit and
# SHA-256 in certified_dataset.yaml.
CERTIFIED_DATASET_PIN = Path(__file__).with_name("certified_dataset.yaml")
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
    return [
        f"microsimulation data ({mode}): {plan.action} on {target} ({plan.reason})",
        "unpinned by design: " + ", ".join(UNPINNED_BY_DESIGN),
    ]


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


def pytest_collection_modifyitems(config, items):
    """Without data, microsimulation tests skip, unless data is mandatory."""
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
