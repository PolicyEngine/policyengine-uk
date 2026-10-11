"""The conftest releases the variable modules of dead tax-benefit systems.

policyengine-core registers each system's variable modules in sys.modules
under the system's id and never removes them. The conftest's
``release_dead_variable_modules`` drops those of systems that no longer exist,
which keeps a long test process's memory flat. If core stops leaking the
modules (PolicyEngine/policyengine-core#520), the first test skips with a
note to remove the workaround, rather than failing every PR after a core
upgrade. If core keeps leaking but names the modules differently, it fails,
because the release would then silently do nothing.

The conftest also freezes the objects that exist once the tests are collected
(gc.freeze()). gc.get_objects() leaves frozen objects out, so the release must
still count a frozen system as live. A frozen object that later becomes
garbage is never freed, so no system may die before the freeze: its variable
modules would be frozen, then released and leaked.
"""

import gc
import sys
import weakref
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


def test_frozen_systems_keep_their_modules(request):
    conftest = _conftest(request)
    # Built when policyengine_uk was imported, during collection, so frozen.
    from policyengine_uk.tax_benefit_system import system

    assert gc.get_threshold()[0] == conftest.GC_FIRST_GENERATION_THRESHOLD
    assert gc.get_freeze_count() > 0
    assert not any(obj is system for obj in gc.get_objects())
    module = type(system.variables["income_tax"]).__module__
    built_later = Simulation(situation=SITUATION).tax_benefit_system
    if type(built_later.variables["income_tax"]).__module__ not in sys.modules:
        pytest.skip("policyengine-core no longer keeps variable modules")

    conftest.release_dead_variable_modules(max_owners=0)

    kept = module in sys.modules
    assert kept, f"{module}, of a live frozen system, was released"


def test_systems_built_after_the_freeze_are_still_collected():
    simulation = Simulation(situation=SITUATION)
    system = weakref.ref(simulation.tax_benefit_system)
    assert any(obj is system() for obj in gc.get_objects())
    del simulation
    gc.collect()
    assert system() is None


def test_no_system_dies_before_the_freeze(request):
    dead = _conftest(request)._DEAD_AT_FREEZE
    assert not dead, (
        f"{len(dead)} tax-benefit system(s) were built and dropped while the "
        "tests were collected, so conftest.py froze their variable modules "
        "and they will never be freed. A test module probably builds a "
        "Simulation or CountryTaxBenefitSystem at import: build it in a "
        "fixture or on first use instead."
    )


def test_dead_systems_modules_are_released_while_a_test_runs(request):
    variable_module_owners = _conftest(request)._variable_module_owners
    max_owners = 8
    owners = set()
    for _ in range(3 * max_owners):
        Simulation(situation=SITUATION).calculate("income_tax", 2026)
        owners.add(len(variable_module_owners()))
    # The release runs as each new system starts loading, and keeps at most
    # max_owners systems' modules plus the new system's.
    assert max(owners) <= max_owners + 1, sorted(owners)
