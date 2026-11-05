"""No module under ``policyengine_uk/variables`` may read the clock.

A variable whose formula, label or class body reads the wall clock gives
different answers for the same inputs depending on when the simulation runs
(#2875: ``inflation_adjustment`` priced real incomes to the year
``datetime.datetime.now()`` returned). A formula that needs a reference year
reads it from the parameters instead, as the real income variables read
``gov.simulation.price_base_year``.

The test parses every module under ``policyengine_uk/variables`` with ``ast``
and fails on any expression that names a clock function, at module level, in
a class body or in a formula, whether the code calls it or only refers to it
(``default=datetime.now`` counts). It resolves ``import x``, ``import x as y``,
``from x import y`` and ``from x import y as z`` at module level and in nested
scopes, so ``import datetime as dt; dt.datetime.now()`` and
``from time import time as clock; clock()`` both fail. An ``import`` that
nothing reads the clock through passes.

The scan stays under ``variables``. Outside it,
``utils/aggregate_impact/measure.py`` times its own stages with ``time.time``,
which changes no output.

Limits: the detector does not follow names rebound by assignment
(``now = datetime.now``; a later ``now()`` passes, though the assignment
itself fails), ``getattr`` with a string, ``__import__``, ``importlib``, or a
clock read inside a helper module outside ``variables`` that a formula calls.
It treats an imported name as bound for the whole module, so a local variable
that shadows an import can raise a false alarm. ``time.localtime``,
``time.gmtime``, ``time.ctime`` and ``time.asctime`` read the clock only when
called without a time argument, and ``time.strftime`` only with one argument,
so the detector flags those forms only. It does not inspect string arguments,
so ``numpy.datetime64("now")`` and ``pandas.Timestamp("now")`` pass.
"""

import ast
from pathlib import Path

import pytest

VARIABLES_ROOT = Path(__file__).parents[2] / "variables"
PACKAGE_ROOT = VARIABLES_ROOT.parent

# Functions that read the clock whenever the code names them.
CLOCK_FUNCTIONS = {
    "datetime.datetime.now",
    "datetime.datetime.today",
    "datetime.datetime.utcnow",
    "datetime.date.today",
    "time.time",
    "time.time_ns",
    "time.monotonic",
    "time.monotonic_ns",
    "time.perf_counter",
    "time.perf_counter_ns",
    "time.process_time",
    "time.process_time_ns",
    "time.thread_time",
    "time.thread_time_ns",
    "pandas.Timestamp.now",
    "pandas.Timestamp.today",
    "pandas.Timestamp.utcnow",
}

# Functions that read the clock only when called with at most this many
# positional arguments and no keyword arguments.
CLOCK_FUNCTIONS_WITHOUT_TIME_ARGUMENT = {
    "time.localtime": 0,
    "time.gmtime": 0,
    "time.ctime": 0,
    "time.asctime": 0,
    "time.strftime": 1,
}


def _import_aliases(tree: ast.AST) -> dict[str, str]:
    """Map each name an import binds to the dotted name it stands for."""
    aliases = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.asname:
                    aliases[alias.asname] = alias.name
                else:
                    root = alias.name.split(".")[0]
                    aliases[root] = root
        elif isinstance(node, ast.ImportFrom) and node.module and not node.level:
            for alias in node.names:
                if alias.name == "*":
                    continue
                aliases[alias.asname or alias.name] = f"{node.module}.{alias.name}"
    return aliases


def _qualified_name(node: ast.AST, aliases: dict[str, str]) -> str | None:
    """The dotted name a ``Name`` or ``Attribute`` chain resolves to."""
    attributes = []
    while isinstance(node, ast.Attribute):
        attributes.append(node.attr)
        node = node.value
    if not isinstance(node, ast.Name) or node.id not in aliases:
        return None
    return ".".join([aliases[node.id], *reversed(attributes)])


def clock_reads(source: str) -> list[tuple[int, str]]:
    """Each clock read in ``source`` as (line, dotted function name)."""
    tree = ast.parse(source)
    aliases = _import_aliases(tree)
    reads = []
    conditional = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            name = _qualified_name(node.func, aliases)
            limit = CLOCK_FUNCTIONS_WITHOUT_TIME_ARGUMENT.get(name)
            if limit is not None:
                conditional[id(node.func)] = (
                    len(node.args) <= limit
                    and not node.keywords
                    and not any(isinstance(arg, ast.Starred) for arg in node.args)
                )
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Name, ast.Attribute)):
            continue
        if isinstance(node.ctx, (ast.Store, ast.Del)):
            continue
        name = _qualified_name(node, aliases)
        if name in CLOCK_FUNCTIONS:
            reads.append((node.lineno, name))
        elif name in CLOCK_FUNCTIONS_WITHOUT_TIME_ARGUMENT:
            if conditional.get(id(node), False):
                reads.append((node.lineno, name))
    return sorted(reads)


DETECTOR_CASES = [
    # Reads the clock.
    ("import datetime\nx = datetime.datetime.now()", ["datetime.datetime.now"]),
    ("import datetime\nx = datetime.date.today()", ["datetime.date.today"]),
    (
        "from datetime import datetime\nx = datetime.utcnow()",
        ["datetime.datetime.utcnow"],
    ),
    (
        "from datetime import datetime\nx = datetime.today()",
        ["datetime.datetime.today"],
    ),
    ("from datetime import date\nx = date.today()", ["datetime.date.today"]),
    ("import datetime as dt\nx = dt.datetime.now().year", ["datetime.datetime.now"]),
    ("from datetime import datetime as D\nx = D.now()", ["datetime.datetime.now"]),
    ("import time\nx = time.time()", ["time.time"]),
    ("import time\nx = time.time_ns()", ["time.time_ns"]),
    ("from time import time\nx = time()", ["time.time"]),
    ("from time import time_ns as clock\nx = clock()", ["time.time_ns"]),
    ("import time as t\nx = t.perf_counter()", ["time.perf_counter"]),
    ("import time\nx = time.localtime()", ["time.localtime"]),
    ("import time\nx = time.strftime('%Y')", ["time.strftime"]),
    ("import pandas as pd\nx = pd.Timestamp.now()", ["pandas.Timestamp.now"]),
    # A reference without a call still reads the clock when used.
    ("from datetime import datetime\nf = datetime.now", ["datetime.datetime.now"]),
    (
        "import datetime\n"
        "class v:\n"
        "    label = f'{datetime.datetime.now().year} prices'\n",
        ["datetime.datetime.now"],
    ),
    (
        "class v:\n"
        "    def formula(household, period, parameters):\n"
        "        import datetime\n"
        "        return datetime.datetime.now().year\n",
        ["datetime.datetime.now"],
    ),
    # Does not read the clock.
    ("import datetime\nimport time\nimport numpy as np", []),
    ("import datetime\nx = datetime.date(2026, 1, 1)", []),
    ("import datetime\nx = datetime.datetime(2026, 1, 1).year", []),
    ("from datetime import date\nx = date.fromisoformat('2026-01-01')", []),
    ("import time\nx = time.localtime(0)", []),
    ("import time\nx = time.strftime('%Y', (2026, 1, 1, 0, 0, 0, 0, 1, 0))", []),
    ("now = 1\nx = now", []),
    ("x = household.now()\ny = parameters.time", []),
]


@pytest.mark.parametrize(
    "source, expected",
    DETECTOR_CASES,
    ids=[f"case-{i}" for i in range(len(DETECTOR_CASES))],
)
def test_detector(source, expected):
    assert [name for _, name in clock_reads(source)] == expected


def test_variables_do_not_read_the_clock():
    paths = sorted(VARIABLES_ROOT.rglob("*.py"))
    assert len(paths) > 100, "The scan found too few variable modules."
    found = {}
    for path in paths:
        reads = clock_reads(path.read_text())
        if reads:
            found[str(path.relative_to(PACKAGE_ROOT))] = reads
    assert not found, (
        "These modules under policyengine_uk/variables read the clock, so "
        "their variables change with the date a simulation runs. Read a "
        f"reference date from the parameters instead: {found}"
    )
