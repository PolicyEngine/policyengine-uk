"""The conftest releases the variable modules of dead tax-benefit systems.

policyengine-core registers each system's variable modules in sys.modules
under the system's id and never removes them. The conftest's
``release_dead_variable_modules`` drops those of systems that no longer exist,
which keeps a long test process's memory flat. If core stops leaking the
modules (PolicyEngine/policyengine-core#520), the first test skips with a
note to remove the workaround, rather than failing every PR after a core
upgrade. If core keeps leaking but names the modules differently, it fails,
because the release would then silently do nothing.
"""

import gc
import sys
from pathlib import Path

import pytest

from policyengine_uk import Simulation

SITUATION = {
    "people": {"adult": {"age": {2026: 40}, "employment_income": {2026: 30_000}}},
    "benunits": {"benunit": {"members": ["adult"]}},
    "households": {"household": {"members": ["adult"]}},
}


def _conftest(request):
    path = Path(__file__).with_name("conftest.py")
    for plugin in request.config.pluginmanager.get_plugins():
        if getattr(plugin, "__file__", None) and Path(plugin.__file__) == path:
            return plugin
    raise AssertionError(f"{path} is not loaded as a plugin")


def _modules_of(owner: str) -> list:
    return [name for name in sys.modules if name.startswith(owner + "_")]


def test_dead_systems_modules_are_released_and_live_ones_kept(request):
    release_dead_variable_modules = _conftest(request).release_dead_variable_modules
    kept = Simulation(situation=SITUATION)
    kept_owner = str(id(kept.tax_benefit_system))
    dropped = Simulation(situation=SITUATION)
    dropped_owner = str(id(dropped.tax_benefit_system))
    expected = dropped.calculate("income_tax", 2026)

    # The module core loaded the income_tax variable from, for this system.
    module = type(dropped.tax_benefit_system.variables["income_tax"]).__module__
    if module not in sys.modules:
        pytest.skip(
            "policyengine-core no longer keeps variable modules in sys.modules "
            "(policyengine-core#520 fixed?); remove "
            "release_dead_variable_modules from conftest.py and this test"
        )
    # Core still keeps them, so the conftest pattern must still recognise them,
    # or the release would silently do nothing.
    assert module.startswith(dropped_owner + "_"), module
    assert _conftest(request)._VARIABLE_MODULE_NAME.match(module), module
    del dropped
    gc.collect()

    released = release_dead_variable_modules(max_owners=0)

    assert released >= 1
    assert not _modules_of(dropped_owner)
    assert _modules_of(kept_owner)
    assert kept.calculate("income_tax", 2026) == expected
    assert Simulation(situation=SITUATION).calculate("income_tax", 2026) == expected


def test_release_waits_until_enough_systems_own_modules(request):
    release_dead_variable_modules = _conftest(request).release_dead_variable_modules
    assert release_dead_variable_modules(max_owners=10**9) == 0
