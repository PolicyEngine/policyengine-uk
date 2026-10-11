"""Test modules must release their module-level caches when they finish.

Property tests cache tax-benefit systems and simulations with
``functools.lru_cache`` so that each Hypothesis example does not build them
again. A module-level cache outlives the module's tests: it keeps everything
it holds for the rest of the test process, and a system also keeps the last
simulation built from it (``Simulation.__init__`` sets
``tax_benefit_system.simulation``). One such cache kept 13 systems, about
0.5 GiB, in a CI worker for the rest of its run.

So every function a test module caches with ``functools.lru_cache`` or
``functools.cache``, whether it defines it or imports it from another test
module, must have its ``cache_clear()`` called after the ``yield`` of a
module-scoped autouse fixture in that module. An imported cache counts
separately: pytest imports test files by bare name, so a module that imports
from another test file loads a second copy of it, with its own caches.
"""

import ast
from pathlib import Path

TESTS = Path(__file__).resolve().parents[1]
CACHE_DECORATORS = {"lru_cache", "cache"}


def _name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Call):
        node = node.func
    if isinstance(node, ast.Attribute):
        return node.attr
    if isinstance(node, ast.Name):
        return node.id
    return None


def cached_functions(tree: ast.Module) -> set[str]:
    """Module-level functions decorated with a functools cache."""
    return {
        node.name
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and any(_name(d) in CACHE_DECORATORS for d in node.decorator_list)
    }


def _keyword(call: ast.Call, name: str):
    for keyword in call.keywords:
        if keyword.arg == name and isinstance(keyword.value, ast.Constant):
            return keyword.value.value
    return None


def _is_module_autouse_fixture(function: ast.FunctionDef) -> bool:
    for decorator in function.decorator_list:
        if (
            isinstance(decorator, ast.Call)
            and _name(decorator) == "fixture"
            and _keyword(decorator, "scope") == "module"
            and _keyword(decorator, "autouse") is True
        ):
            return True
    return False


def released_caches(tree: ast.Module) -> set[str]:
    """Names whose cache_clear() comes after the yield of a module-scoped
    autouse fixture, including a yield inside ``with`` or ``try``."""
    released = set()
    for function in tree.body:
        if not (
            isinstance(function, ast.FunctionDef)
            and _is_module_autouse_fixture(function)
        ):
            continue
        yields = [
            node.lineno for node in ast.walk(function) if isinstance(node, ast.Yield)
        ]
        if not yields:
            continue
        for node in ast.walk(function):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == "cache_clear"
                and isinstance(node.func.value, ast.Name)
                and node.lineno > min(yields)
            ):
                released.add(node.func.value.id)
    return released


def imported_test_modules(tree: ast.Module) -> dict[Path, list[str]]:
    """Other test files this module imports names from."""
    imports = {}
    for node in tree.body:
        if isinstance(node, ast.ImportFrom) and node.module:
            module = node.module.removeprefix("policyengine_uk.tests.")
            path = TESTS / (module.replace(".", "/") + ".py")
            if path.exists():
                imports[path] = [alias.name for alias in node.names]
    return imports


def parse(path: Path) -> ast.Module:
    return ast.parse(path.read_text(), filename=str(path))


def unreleased_caches(path: Path) -> list[str]:
    tree = parse(path)
    caches = cached_functions(tree)
    for imported, names in imported_test_modules(tree).items():
        caches |= cached_functions(parse(imported)) & set(names)
    return sorted(caches - released_caches(tree))


def test_every_test_module_cache_is_released():
    findings = {
        str(path.relative_to(TESTS)): missing
        for path in sorted(TESTS.rglob("*.py"))
        if (missing := unreleased_caches(path))
    }
    assert not findings, (
        "Clear these caches after the yield of a module-scoped autouse "
        f"fixture in the module that uses them: {findings}"
    )


def test_the_scan_finds_caches_and_releases():
    source = """
import functools
from functools import cache, lru_cache

import pytest


@lru_cache(maxsize=None)
def systems(value):
    return value


@cache
def simulation():
    return 1


@functools.lru_cache
def template():
    return 2


def not_cached():
    return 3


@pytest.fixture(scope="module", autouse=True)
def release():
    systems.cache_clear()  # before the yield: does not count
    yield
    simulation.cache_clear()


@pytest.fixture(autouse=True, scope="module")
def release_after_a_yield_inside_with():
    with open(__file__):
        try:
            yield
        finally:
            template.cache_clear()
"""
    tree = ast.parse(source)
    assert cached_functions(tree) == {"systems", "simulation", "template"}
    assert released_caches(tree) == {"simulation", "template"}

    function_scoped = source.replace('scope="module"', 'scope="function"')
    assert released_caches(ast.parse(function_scoped)) == set()
    not_autouse = source.replace("autouse=True", "autouse=False")
    assert released_caches(ast.parse(not_autouse)) == set()


def test_the_scan_follows_imports_from_other_test_files():
    tree = ast.parse(
        "from policyengine_uk.tests.test_state_pension_age import (\n"
        "    YEARS,\n"
        "    differential_simulation,\n"
        ")\n"
    )
    imported = imported_test_modules(tree)
    assert imported == {
        TESTS / "test_state_pension_age.py": ["YEARS", "differential_simulation"]
    }
    caches = cached_functions(parse(TESTS / "test_state_pension_age.py"))
    assert "differential_simulation" in caches
