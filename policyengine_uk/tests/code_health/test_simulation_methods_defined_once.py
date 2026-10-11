"""Each method of the simulation classes is defined once.

Pull requests often override methods of ``policyengine_uk.simulation.Simulation``
(``set_input``, ``delete_arrays``, ``clone`` and others). Two overrides of one
method, added at different places in the class, merge without a git conflict,
and the later definition replaces the earlier one: whatever the earlier one
did is lost without an error. Combine them into one method instead.

``ruff check`` reports this as F811, but CI checks formatting only, so this
test does. Property setters and deleters, and ``typing.overload`` stubs, name
a method again on purpose and are left out.
"""

import ast
from collections import Counter
from pathlib import Path

import pytest

PACKAGE = Path(__file__).resolve().parents[2]
MODULES = ["simulation.py", "microsimulation.py"]


def _names_again(decorator: ast.expr) -> bool:
    """Whether ``decorator`` defines a method under a name already used."""
    if isinstance(decorator, ast.Attribute):
        return decorator.attr in ("setter", "deleter", "getter")
    return isinstance(decorator, ast.Name) and decorator.id == "overload"


def methods_defined_more_than_once(source: str) -> dict:
    """The methods each class in ``source`` defines more than once, by
    class."""
    repeated = {}
    for node in ast.walk(ast.parse(source)):
        if not isinstance(node, ast.ClassDef):
            continue
        names = Counter(
            method.name
            for method in node.body
            if isinstance(method, (ast.FunctionDef, ast.AsyncFunctionDef))
            and not any(map(_names_again, method.decorator_list))
        )
        twice = sorted(name for name, count in names.items() if count > 1)
        if twice:
            repeated[node.name] = twice
    return repeated


@pytest.mark.parametrize("module", MODULES)
def test_each_method_of_the_simulation_classes_is_defined_once(module):
    repeated = methods_defined_more_than_once((PACKAGE / module).read_text())
    assert not repeated, (
        f"{module} defines these methods more than once, so only the last "
        f"definition of each takes effect: {repeated}. Combine them."
    )


def test_a_method_defined_twice_is_found():
    source = """
class Simulation:
    def set_input(self):
        pass

    @property
    def size(self):
        pass

    @size.setter
    def size(self, value):
        pass

    def set_input(self):
        pass
"""
    assert methods_defined_more_than_once(source) == {"Simulation": ["set_input"]}
