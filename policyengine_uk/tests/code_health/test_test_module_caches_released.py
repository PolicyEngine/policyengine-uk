"""Test modules must release their module-level caches when they finish.

Property tests cache tax-benefit systems and simulations with
``functools.lru_cache`` so that each Hypothesis example does not build them
again. A module-level cache outlives the module's tests: it keeps everything
it holds for the rest of the test process, and a system also keeps the last
simulation built from it (``Simulation.__init__`` sets
``tax_benefit_system.simulation``). One such cache kept 13 systems, about
0.5 GiB, in a CI worker for the rest of its run (run 38165445604, #2357).

So a test module must call ``cache_clear()``, after the ``yield`` of a
module-scoped autouse fixture, on every functools cache that it:

- defines at module level (a decorated function, or
  ``name = lru_cache(...)(function)``);
- imports from another test file; or
- fills through a function it imports from another test file, where that
  function reaches the cache through that file's own module-level functions.

An imported cache counts separately because pytest collects the files in this
directory by bare name (it has no ``__init__.py``), so
``from policyengine_uk.tests.X import f`` loads a second copy of ``X`` with its
own caches, which ``X``'s fixtures never clear.

This is a static scan. It does not see cached methods, caches reached through
``import module`` rather than ``from module import name``, or whether a
``cache_clear()`` written after the ``yield`` runs (one in an ``except`` branch
counts).
"""

import ast
from collections.abc import Iterator
from pathlib import Path

TESTS = Path(__file__).resolve().parents[1]
CACHES = {"lru_cache", "cache"}
FUNCTIONS = (ast.FunctionDef, ast.AsyncFunctionDef)


def _is_functools_cache(node: ast.AST) -> bool:
    """``lru_cache``, ``cache``, ``functools.lru_cache``, called or not."""
    if isinstance(node, ast.Call):
        node = node.func
    if isinstance(node, ast.Attribute):
        return (
            node.attr in CACHES
            and isinstance(node.value, ast.Name)
            and node.value.id == "functools"
        )
    return isinstance(node, ast.Name) and node.id in CACHES


def module_functions(tree: ast.Module) -> dict[str, ast.AST]:
    return {node.name: node for node in tree.body if isinstance(node, FUNCTIONS)}


def cached_functions(tree: ast.Module) -> set[str]:
    """Module-level names bound to a functools cache."""
    cached = {
        name
        for name, function in module_functions(tree).items()
        if any(_is_functools_cache(d) for d in function.decorator_list)
    }
    for node in tree.body:
        # name = lru_cache(maxsize=1)(function) or name = cache(function)
        if (
            isinstance(node, ast.Assign)
            and isinstance(node.value, ast.Call)
            and (
                _is_functools_cache(node.value.func) or _is_functools_cache(node.value)
            )
        ):
            cached |= {t.id for t in node.targets if isinstance(t, ast.Name)}
    return cached


def reached_caches(tree: ast.Module, names: set[str]) -> set[str]:
    """Caches of this module that calling the named functions can fill: the
    names themselves, and any cache their bodies reach through the module's
    own functions."""
    functions = module_functions(tree)
    caches = cached_functions(tree)
    seen: set[str] = set()
    pending = [name for name in names if name in functions or name in caches]
    while pending:
        name = pending.pop()
        if name in seen:
            continue
        seen.add(name)
        if name in functions:
            pending += [
                node.id
                for node in ast.walk(functions[name])
                if isinstance(node, ast.Name)
                and (node.id in functions or node.id in caches)
            ]
    return seen & caches


def _own_nodes(function: ast.AST) -> Iterator[ast.AST]:
    """The function's nodes, without the bodies of functions nested in it."""
    pending = list(ast.iter_child_nodes(function))
    while pending:
        node = pending.pop()
        yield node
        if not isinstance(node, (*FUNCTIONS, ast.Lambda, ast.ClassDef)):
            pending.extend(ast.iter_child_nodes(node))


def _is_module_autouse_fixture(function: ast.AST) -> bool:
    for decorator in getattr(function, "decorator_list", []):
        if not isinstance(decorator, ast.Call):
            continue
        func = decorator.func
        name = func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", "")
        keywords = {
            keyword.arg: keyword.value.value
            for keyword in decorator.keywords
            if isinstance(keyword.value, ast.Constant)
        }
        if (
            name == "fixture"
            and keywords.get("scope") == "module"
            and keywords.get("autouse") is True
        ):
            return True
    return False


def released_caches(tree: ast.Module) -> set[str]:
    """Names whose cache_clear() comes after the yield of a module-scoped
    autouse fixture, including a yield inside ``with`` or ``try``."""
    released = set()
    for function in module_functions(tree).values():
        if not _is_module_autouse_fixture(function):
            continue
        nodes = list(_own_nodes(function))
        yields = [node.lineno for node in nodes if isinstance(node, ast.Yield)]
        if not yields:
            continue
        for node in nodes:
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == "cache_clear"
                and isinstance(node.func.value, ast.Name)
                and node.lineno > min(yields)
            ):
                released.add(node.func.value.id)
    return released


def imported_test_files(tree: ast.Module, path: Path) -> dict[Path, dict[str, str]]:
    """Other test files this module imports names from: for each file, the
    imported names and what this module calls them."""
    imports: dict[Path, dict[str, str]] = {}
    for node in tree.body:
        if not isinstance(node, ast.ImportFrom):
            continue
        module = (node.module or "").removeprefix("policyengine_uk.tests.")
        if not module:
            continue
        relative = Path(*module.split(".")).with_suffix(".py")
        bases = [path.parents[node.level - 1]] if node.level else [TESTS, path.parent]
        for base in bases:
            if (base / relative).is_file():
                imports.setdefault(base / relative, {}).update(
                    {alias.name: alias.asname or alias.name for alias in node.names}
                )
                break
    return imports


def parse(path: Path) -> ast.Module:
    return ast.parse(path.read_text(), filename=str(path))


def unreleased_caches(path: Path) -> list[str]:
    tree = parse(path)
    caches = cached_functions(tree)
    for imported, names in imported_test_files(tree, path).items():
        if imported == path:
            continue
        # A cache this module fills without importing it is reported under
        # its own name: import it to clear it.
        caches |= {
            names.get(cache, cache)
            for cache in reached_caches(parse(imported), set(names))
        }
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


SCANNED = """
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
async def template():
    return 2


def build():
    return 3


assigned = lru_cache(maxsize=1)(build)
wrapped = cache(build)
not_a_functools_cache = registry.cache(build)


def helper():
    return indirect()


def indirect():
    return simulation()


def pure():
    return build()


@pytest.fixture(scope="module", autouse=True)
def release():
    systems.cache_clear()  # before the yield: does not count
    yield

    def never_called():
        wrapped.cache_clear()  # in a nested function: does not count

    simulation.cache_clear()


@pytest.fixture(autouse=True, scope="module")
def release_after_a_yield_inside_with():
    with open(__file__):
        try:
            yield
        finally:
            template.cache_clear()
"""


def test_the_scan_finds_caches_and_releases():
    tree = ast.parse(SCANNED)
    assert cached_functions(tree) == {
        "systems",
        "simulation",
        "template",
        "assigned",
        "wrapped",
    }
    assert released_caches(tree) == {"simulation", "template"}

    function_scoped = SCANNED.replace('scope="module"', 'scope="function"')
    assert released_caches(ast.parse(function_scoped)) == set()
    not_autouse = SCANNED.replace("autouse=True", "autouse=False")
    assert released_caches(ast.parse(not_autouse)) == set()


def test_the_scan_follows_functions_to_the_caches_they_fill():
    tree = ast.parse(SCANNED)
    assert reached_caches(tree, {"helper"}) == {"simulation"}
    assert reached_caches(tree, {"systems", "pure"}) == {"systems"}
    assert reached_caches(tree, {"pure", "not_defined_here"}) == set()


def test_the_scan_follows_imports_from_other_test_files(tmp_path):
    (tmp_path / "test_source.py").write_text(SCANNED)
    user = tmp_path / "test_user.py"
    for imports, expected in [
        # An imported cache, under the name this module gives it.
        ("from test_source import systems as cached_systems", ["cached_systems"]),
        # A cache filled through an imported helper, which is not imported.
        ("from test_source import helper", ["simulation"]),
        ("from .test_source import helper, simulation", ["simulation"]),
        ("from test_source import pure", []),
    ]:
        user.write_text(imports + "\n")
        assert unreleased_caches(user) == expected, imports

    user.write_text(
        "import pytest\n"
        "from test_source import helper, simulation as shared\n\n\n"
        '@pytest.fixture(scope="module", autouse=True)\n'
        "def release():\n"
        "    yield\n"
        "    shared.cache_clear()\n"
    )
    assert unreleased_caches(user) == []


def test_the_scan_resolves_this_directorys_imports():
    tree = ast.parse(
        "from policyengine_uk.tests.test_state_pension_age import (\n"
        "    YEARS,\n"
        "    differential_simulation as cached,\n"
        ")\n"
    )
    assert imported_test_files(tree, TESTS / "test_x.py") == {
        TESTS / "test_state_pension_age.py": {
            "YEARS": "YEARS",
            "differential_simulation": "cached",
        }
    }
