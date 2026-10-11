"""The conftest compiles each variable file once and shares the code.

policyengine-core compiles a system's variable files again for every new
system. Coverage's sys.monitoring core, which CI uses, keeps every code object
it has seen alive, so each Simulation used to leave its code objects behind.
The conftest makes every system run the code object compiled the first time.

Systems must still get their own modules, classes and functions, run the code
of the file's current source, and compute the same results. If
policyengine-core starts sharing the code itself, the upstream check skips
with a note to remove the workaround.
"""

import sys
from importlib.machinery import SourceFileLoader
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


def _income_tax_formula(simulation):
    variable = simulation.tax_benefit_system.variables["income_tax"]
    return variable.get_formula()


def _coverage_code_objects():
    """Code objects coverage's sys.monitoring core holds, or None if inactive."""
    try:
        import coverage
    except ImportError:
        return None
    cov = coverage.Coverage.current()
    collector = getattr(cov, "_collector", None)
    if collector is None:
        return None
    lists = [getattr(tracer, "code_objects", None) for tracer in collector.tracers]
    lists = [objects for objects in lists if objects is not None]
    return sum(len(objects) for objects in lists) if lists else None


def test_systems_share_code_but_not_modules_classes_or_functions():
    first = Simulation(situation=SITUATION)
    second = Simulation(situation=SITUATION)
    first_class = type(first.tax_benefit_system.variables["income_tax"])
    second_class = type(second.tax_benefit_system.variables["income_tax"])
    first_formula = _income_tax_formula(first)
    second_formula = _income_tax_formula(second)

    assert first_class is not second_class
    assert (
        sys.modules[first_class.__module__]
        is not (sys.modules[second_class.__module__])
    )
    assert first_formula is not second_formula
    assert first_formula.__globals__ is not second_formula.__globals__
    assert first_formula.__code__ is second_formula.__code__
    assert first.calculate("income_tax", 2026) == second.calculate("income_tax", 2026)


def test_shared_code_is_compiled_from_the_current_source(request):
    Simulation(situation=SITUATION)
    shared = _conftest(request)._variable_code
    variables_dir = Path(sys.modules["policyengine_uk"].__file__).parent / "variables"
    # Core reads a directory's __init__.py for metadata and runs every other file.
    files = {
        str(path) for path in variables_dir.rglob("*.py") if path.name != "__init__.py"
    }

    assert shared, "no variable code was shared"
    for (path, mtime_ns, size), code in shared.items():
        stat = Path(path).stat()
        assert (stat.st_mtime_ns, stat.st_size) == (mtime_ns, size), path
        source = Path(path).read_text(encoding="utf-8")
        assert code == compile(source, path, "exec", dont_inherit=True), path
    assert {path for path, _, _ in shared} >= files


def test_policyengine_core_still_compiles_each_system_again(request, monkeypatch):
    monkeypatch.setattr(SourceFileLoader, "get_code", _conftest(request)._get_code)
    first = _income_tax_formula(Simulation(situation=SITUATION))
    second = _income_tax_formula(Simulation(situation=SITUATION))
    if first.__code__ is second.__code__:
        pytest.skip(
            "policyengine-core now shares variable code between systems; "
            "remove _get_shared_variable_code from conftest.py and this file"
        )
    assert first.__code__ == second.__code__


def test_a_simulation_leaves_coverage_no_new_code_objects(request, monkeypatch):
    if _coverage_code_objects() is None:
        pytest.skip("coverage is not measuring with sys.monitoring")
    Simulation(situation=SITUATION).calculate("income_tax", 2026)

    before = _coverage_code_objects()
    Simulation(situation=SITUATION).calculate("income_tax", 2026)
    shared = _coverage_code_objects() - before
    monkeypatch.setattr(SourceFileLoader, "get_code", _conftest(request)._get_code)
    Simulation(situation=SITUATION).calculate("income_tax", 2026)
    unshared = _coverage_code_objects() - before - shared

    # Without sharing, a Simulation leaves about 2,500 code objects.
    assert unshared > 1_000, unshared
    assert shared < 100, shared
