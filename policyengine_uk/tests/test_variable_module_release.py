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
still count a frozen system as live. Frozen objects in reference cycles that
later become garbage are not freed until they are unfrozen, so no system may be
built and dropped while the tests are collected: its variable modules would be
frozen, then released and leaked for the rest of the session.
"""

import gc
import sys
import weakref
from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

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


def test_dead_systems_modules_are_released_while_a_test_runs(request, monkeypatch):
    conftest = _conftest(request)
    max_new = 8
    # Find the systems alive now; other test modules may keep many (caches).
    monkeypatch.setattr(conftest, "_live_owners", 0)
    conftest.release_after_new_systems(max_new=0)
    live = len(conftest._variable_module_owners())
    scans = []
    release = conftest.release_dead_variable_modules
    monkeypatch.setattr(
        conftest,
        "release_dead_variable_modules",
        lambda **kwargs: scans.append(kwargs) or release(**kwargs),
    )
    owners = []
    for _ in range(max_new + 3):
        Simulation(situation=SITUATION).calculate("income_tax", 2026)
        owners.append(len(conftest._variable_module_owners()))
    # Released as each new system starts adding its variables, so at most
    # max_new dead systems' modules beyond the live ones, plus the newest
    # system's. Without the release the last count would be live + 11.
    assert scans, "no release ran while the systems were built"
    assert max(owners) <= live + max_new + 1, (live, owners)


# Model of the release's bookkeeping, without building systems: each step
# builds a system that stays alive or dies at once, kills live systems, or
# runs the release. After every release, at most max_new owners are beyond
# those alive at the last scan, and a scan happens exactly when more are.
_steps = st.lists(
    st.one_of(
        st.tuples(st.just("build"), st.booleans()),
        st.tuples(st.just("die"), st.integers(0, 5)),
        st.tuples(st.just("release"), st.just(0)),
    ),
    max_size=60,
)


@settings(max_examples=200, deadline=None)
@given(steps=_steps, max_new=st.integers(0, 10))
def test_release_scans_only_past_max_new_new_owners(request, steps, max_new):
    conftest = _conftest(request)
    live, dead, scans = 1, 0, []

    def owners():
        return {str(i): [] for i in range(live + dead)}

    def release_dead(max_owners):
        nonlocal dead
        released, dead = dead, 0
        scans.append(max_owners)
        return released

    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.setattr(conftest, "_variable_module_owners", owners)
        monkeypatch.setattr(conftest, "release_dead_variable_modules", release_dead)
        monkeypatch.setattr(conftest, "_live_owners", 0)
        for action, value in steps:
            if action == "build":
                live, dead = (live + 1, dead) if value else (live, dead + 1)
            elif action == "die":
                moved = min(value, live)
                live, dead = live - moved, dead + moved
            else:
                last_live = conftest._live_owners
                due = live + dead > last_live + max_new
                before = len(scans)
                released = conftest.release_after_new_systems(max_new=max_new)
                assert (len(scans) > before) == due
                if due:
                    assert scans[-1] == 0 and dead == 0 and released >= 0
                    assert conftest._live_owners == live
                else:
                    assert released == 0
                assert live + dead <= conftest._live_owners + max_new
