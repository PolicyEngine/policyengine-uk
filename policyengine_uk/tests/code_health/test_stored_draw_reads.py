"""pe-uk reads a stored draw only through Simulation.calculate.

``Simulation.calculate`` checks each read of a registered draw against the
supplied input policyengine-core reads (``utils/stored_draws.input_source``).
A read that goes to storage instead (``get_array``,
``_get_array_from_storage``, a holder) skips that check. This scan fails on
any such read of a registered draw in the package, named by a string or by
a module constant that holds the name. ``utils/stored_draws.py`` is the check
itself and reads storage on purpose.
"""

import ast
from pathlib import Path

from policyengine_uk.utils.stored_draws import REGISTERED_DRAW_NAMES

PACKAGE = Path(__file__).resolve().parents[2]
EXEMPT = {"utils/stored_draws.py"}
STORAGE_READS = {
    "get_array",
    "_get_array_from_storage",
    "get_holder",
    "get_stored_input",
    "stored_supplied_value",
    "supplied_input",
    "get_known_periods",
    "get_input_periods",
}


def _draw_constants(tree) -> set:
    """Module-level names bound to a registered draw's name."""
    names = set()
    for node in tree.body:
        if (
            isinstance(node, ast.Assign)
            and isinstance(node.value, ast.Constant)
            and node.value.value in REGISTERED_DRAW_NAMES
        ):
            names.update(t.id for t in node.targets if isinstance(t, ast.Name))
    return names


def _names_a_draw(node, constants) -> bool:
    return (isinstance(node, ast.Constant) and node.value in REGISTERED_DRAW_NAMES) or (
        isinstance(node, ast.Name) and node.id in constants
    )


def storage_reads(source: str) -> list:
    tree = ast.parse(source)
    constants = _draw_constants(tree)
    found = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            name = (
                func.attr
                if isinstance(func, ast.Attribute)
                else getattr(func, "id", None)
            )
            arguments = list(node.args) + [keyword.value for keyword in node.keywords]
            if name in STORAGE_READS and any(
                _names_a_draw(argument, constants) for argument in arguments
            ):
                found.append((node.lineno, name))
        if (
            isinstance(node, ast.Subscript)
            and isinstance(node.value, ast.Attribute)
            and node.value.attr == "_holders"
            and _names_a_draw(node.slice, constants)
        ):
            found.append((node.lineno, "_holders"))
    return found


def test_no_package_module_reads_a_draw_from_storage():
    found = []
    for path in sorted(PACKAGE.rglob("*.py")):
        relative = path.relative_to(PACKAGE).as_posix()
        if relative.startswith("tests/") or relative in EXEMPT:
            continue
        for line, name in storage_reads(path.read_text()):
            found.append(f"{relative}:{line} {name}")
    assert not found, (
        "These read a stored draw from storage, skipping the check in "
        "Simulation.calculate; read it with calculate instead:\n" + "\n".join(found)
    )


def test_the_scan_finds_direct_reads():
    source = (
        'DRAW = "pip_phase_in_draw"\n'
        "def read(sim, year):\n"
        "    sim.get_array(DRAW, year)\n"
        '    sim.get_holder("uc_new_claimant_health_element_draw")\n'
        '    population._holders["pip_phase_in_draw"]\n'
        "    holder._get_array_from_storage(DRAW, year)\n"
        "    sim.calculate(DRAW, year)\n"
    )
    assert sorted(name for _, name in storage_reads(source)) == sorted(
        ["get_array", "get_holder", "_holders", "_get_array_from_storage"]
    )
