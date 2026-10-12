"""Building and running the model leaves the process's warning filters alone.

policyengine-core runs every variable file again each time a
``CountryTaxBenefitSystem`` is built, so a ``warnings.filterwarnings("ignore")``
at the top of one put a global "ignore" at the front of ``warnings.filters``
on every build. Until #1846 three LHA variable modules did that, and
``bi_household_phaseout`` did it inside its formula. That silenced every
warning in the process, including inside a ``pytest.warns`` block entered
before the build (#2377).

Invariants:

1. Building a ``CountryTaxBenefitSystem`` or a ``Simulation`` and calculating
   its variables leaves ``warnings.filters`` and numpy's error state as they
   were. Importing the package leaves numpy's error state alone and adds no
   filter that ignores a built-in warning category everywhere.
2. A warning raised after building reaches the caller, inside a
   ``pytest.warns`` block entered before the build and in a fresh process
   under Python's default filters.
3. No module in the package changes the warning filters outside
   ``warnings.catch_warnings()``, or numpy's error state at all (use
   ``np.errstate()``). A filter inside a formula only runs when that formula
   does, so building the model cannot show this one.
4. The divisions the filters used to hide raise no ``RuntimeWarning``,
   including when the denominator is zero.
"""

import ast
import json
import os
import subprocess
import sys
import textwrap
import warnings
from contextlib import contextmanager
from pathlib import Path

import numpy as np
import pytest

import policyengine_uk
from policyengine_uk import CountryTaxBenefitSystem, Simulation

YEAR = 2026
PACKAGE = Path(policyengine_uk.__file__).parent
PROBE = "probe raised after building the model"

# A privately renting couple with two children, sharing the house with two
# pensioners in their own benefit units, so the LHA size criteria, the
# Housing Benefit and Universal Credit maximum rent and the State Pension
# formulas all run.
SITUATION = {
    "people": {
        "parent_1": {
            "age": {YEAR: 40},
            "is_male": {YEAR: True},
            "employment_income": {YEAR: 12_000},
        },
        "parent_2": {"age": {YEAR: 38}},
        "boy": {"age": {YEAR: 11}, "is_male": {YEAR: True}},
        "girl": {"age": {YEAR: 7}},
        "pensioner_1": {"age": {YEAR: 70}, "state_pension_reported": {YEAR: 9_000}},
        "pensioner_2": {"age": {YEAR: 72}},
    },
    "benunits": {
        "family": {"members": ["parent_1", "parent_2", "boy", "girl"]},
        "pensioner_1": {"members": ["pensioner_1"]},
        "pensioner_2": {"members": ["pensioner_2"]},
    },
    "households": {
        "household": {
            "members": [
                "parent_1",
                "parent_2",
                "boy",
                "girl",
                "pensioner_1",
                "pensioner_2",
            ],
            "rent": {YEAR: 12_000},
            "tenure_type": {YEAR: "RENT_PRIVATELY"},
        }
    },
}

# A basic income that the household phase-out reduces. Without it every
# household's basic income is zero, the phase-out's zero-denominator case.
BASIC_INCOME = {
    "gov.contrib.ubi_center.basic_income.amount.flat": {"2020-01-01.2030-12-31": 50},
    "gov.contrib.ubi_center.basic_income.phase_out.household.rate": {
        "2020-01-01.2030-12-31": 0.2
    },
    "gov.contrib.ubi_center.basic_income.phase_out.household.threshold": {
        "2020-01-01.2030-12-31": 1_000
    },
}

# The variables whose modules or formulas set the filters, and the
# divisions those filters hid.
VARIABLES = [
    "LHA_eligible",
    "LHA_allowed_bedrooms",
    "LHA_category",
    "BRMA_LHA_rate",
    "LHA_cap",
    "uc_LHA_cap",
    "housing_benefit",
    "universal_credit",
    "basic_state_pension",
    "additional_state_pension",
    "state_pension",
    "bi_individual_phaseout",
    "bi_household_phaseout",
    "household_net_income",
]


def simulate(reform=None):
    simulation = Simulation(situation=SITUATION, reform=reform)
    for variable in VARIABLES:
        simulation.calculate(variable, YEAR)
    return simulation


@contextmanager
def known_global_state():
    """Set the warning filters and numpy's error state so a change would show.

    ``filterwarnings("ignore")`` moves an identical filter already at the
    front back to the front, leaving the list as it was, so start from an
    "always" filter it would have to displace. pytest does not restore
    numpy's error state between tests, so set that too. Both are restored on
    exit.
    """
    with warnings.catch_warnings(record=True) as caught, np.errstate(all="warn"):
        warnings.simplefilter("always")
        yield caught


def test_building_the_system_leaves_warning_filters_and_numpy_unchanged():
    with known_global_state() as caught:
        filters = list(warnings.filters)
        numpy_error_state = np.geterr()

        CountryTaxBenefitSystem()

        assert warnings.filters == filters
        assert np.geterr() == numpy_error_state
        warnings.warn(PROBE, UserWarning)
    assert PROBE in [str(warning.message) for warning in caught]


@pytest.mark.parametrize("reform", [None, BASIC_INCOME], ids=["baseline", "reform"])
def test_simulating_leaves_warning_filters_and_numpy_unchanged(reform):
    with known_global_state():
        filters = list(warnings.filters)
        numpy_error_state = np.geterr()

        simulate(reform)

        assert warnings.filters == filters
        assert np.geterr() == numpy_error_state


def test_a_warning_raised_after_simulating_reaches_pytest_warns():
    # As on 11 October 2026, when pytest.warns recorded [] for a
    # ReformPeriodWarning raised after the variable modules were loaded.
    with pytest.warns(UserWarning, match=PROBE):
        simulate(BASIC_INCOME)
        warnings.warn(PROBE, UserWarning)


@pytest.mark.parametrize("reform", [None, BASIC_INCOME], ids=["baseline", "reform"])
def test_the_divisions_the_filters_hid_raise_no_runtime_warning(reform):
    with warnings.catch_warnings():
        warnings.simplefilter("error", RuntimeWarning)
        simulation = simulate(reform)
    household_basic_income = simulation.calculate(
        "bi_maximum", YEAR, map_to="household"
    )
    # The baseline has no basic income, so the phase-out divides by zero.
    assert (household_basic_income == 0).all() == (reform is None)


# Calls that change the process's warning filters, and are fine inside
# warnings.catch_warnings(), which restores the filters on exit.
WARNING_FILTER_CALLS = {"filterwarnings", "simplefilter", "resetwarnings"}
# Calls that change numpy's process-wide error state. np.errstate() is the
# scoped form, so these are never needed.
NUMPY_ERROR_STATE_CALLS = {"seterr", "seterrcall"}
DEFINITIONS = (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.ClassDef)


def _name(node: ast.AST):
    if isinstance(node, ast.Attribute):
        return node.attr
    if isinstance(node, ast.Name):
        return node.id
    return None


def _catches_warnings(node: ast.AST) -> bool:
    return isinstance(node, (ast.With, ast.AsyncWith)) and any(
        isinstance(item.context_expr, ast.Call)
        and _name(item.context_expr.func) == "catch_warnings"
        for item in node.items
    )


def global_warning_state_changes(source: str) -> list:
    """Lines that change warning filters or numpy's error state unscoped.

    A ``with warnings.catch_warnings():`` block scopes the filter calls in
    its body, but not those in a function defined there, which run later.
    """
    found = []

    def visit(node: ast.AST, scoped: bool) -> None:
        if isinstance(node, DEFINITIONS):
            scoped = False
        elif _catches_warnings(node):
            scoped = True
        if isinstance(node, ast.Call):
            name = _name(node.func)
            if name in NUMPY_ERROR_STATE_CALLS or (
                name in WARNING_FILTER_CALLS and not scoped
            ):
                found.append((node.lineno, name))
        elif (
            not scoped
            and isinstance(node, ast.Attribute)
            and node.attr == "filters"
            and _name(node.value) == "warnings"
        ):
            found.append((node.lineno, "warnings.filters"))
        for child in ast.iter_child_nodes(node):
            visit(child, scoped)

    visit(ast.parse(source), scoped=False)
    return found


@pytest.mark.parametrize(
    "source, expected",
    [
        ('import warnings\nwarnings.filterwarnings("ignore")', [(2, "filterwarnings")]),
        (
            "def formula(person, period, parameters):\n"
            '    warnings.filterwarnings("ignore")',
            [(2, "filterwarnings")],
        ),
        (
            'from warnings import simplefilter\nsimplefilter("ignore")',
            [(2, "simplefilter")],
        ),
        ("warnings.resetwarnings()", [(1, "resetwarnings")]),
        (
            'warnings.filters.insert(0, ("ignore", None, Warning, None, 0))',
            [(1, "warnings.filters")],
        ),
        ('np.seterr(all="ignore")', [(1, "seterr")]),
        (
            'with np.errstate(all="ignore"):\n    np.seterr(all="ignore")',
            [(2, "seterr")],
        ),
        (
            "with warnings.catch_warnings():\n"
            '    def later():\n        warnings.simplefilter("ignore")',
            [(3, "simplefilter")],
        ),
        (
            "with warnings.catch_warnings():\n"
            '    warnings.filterwarnings("ignore", category=RuntimeWarning)\n'
            "    x = a / b",
            [],
        ),
        ('with np.errstate(divide="ignore"):\n    x = a / b', []),
        ("x = np.divide(a, b, out=np.zeros_like(a), where=b > 0)", []),
        ("filters = [1]\nlen(warnings.__name__)", []),
    ],
)
def test_the_scanner_finds_unscoped_global_warning_state(source, expected):
    assert global_warning_state_changes(source) == expected


def test_no_module_changes_the_warning_filters_or_numpy_error_state():
    files = [
        path
        for path in sorted(PACKAGE.rglob("*.py"))
        if PACKAGE / "tests" not in path.parents
    ]
    # Guards against scanning the wrong directory and passing vacuously.
    assert len(files) > 1_000
    found = [
        f"{path.relative_to(PACKAGE.parent)}:{line}: {name}"
        for path in files
        for line, name in global_warning_state_changes(path.read_text())
    ]
    assert found == [], (
        "Scope warning filters with warnings.catch_warnings() and numpy's "
        "error state with np.errstate(), or avoid the warning (for a guarded "
        "division, np.divide(..., where=)):\n" + "\n".join(found)
    )


# Code that runs only once per process, such as a module imported lazily
# while a simulation is built, cannot be checked in this process once an
# earlier test has imported it. Build and simulate in a fresh interpreter
# under Python's default filters, as an ordinary caller would.
FRESH_PROCESS_SCRIPT = textwrap.dedent(
    """
    import json
    import sys
    import warnings

    import numpy as np

    situation, reform, variables, year, probe = json.loads(sys.argv[1])
    numpy_error_state = np.geterr()
    filters_before_import = list(warnings.filters)

    # Importing the package builds a system, so take the snapshots above
    # before it, as well as the one below after it.
    from policyengine_uk import CountryTaxBenefitSystem, Simulation

    filters = list(warnings.filters)
    CountryTaxBenefitSystem()
    simulation = Simulation(situation=situation, reform=reform)
    for variable in variables:
        simulation.calculate(variable, year)

    assert warnings.filters == filters, [
        f for f in warnings.filters if f not in filters
    ]
    # Dependencies add filters for their own warning classes, or for a
    # given message or module. None may ignore a built-in category everywhere.
    added = [f for f in warnings.filters if f not in filters_before_import]
    broad = [
        (action, category.__name__)
        for action, message, category, module, _ in added
        if action == "ignore"
        and message is None
        and module is None
        and category.__module__ == "builtins"
    ]
    assert broad == [], broad
    assert np.geterr() == numpy_error_state, np.geterr()
    warnings.warn(probe, UserWarning)
    """
)


def test_a_warning_raised_after_simulating_reaches_a_fresh_process():
    arguments = json.dumps([SITUATION, BASIC_INCOME, VARIABLES, YEAR, PROBE])
    result = subprocess.run(
        [sys.executable, "-c", FRESH_PROCESS_SCRIPT, arguments],
        capture_output=True,
        text=True,
        env={k: v for k, v in os.environ.items() if k != "PYTHONWARNINGS"},
    )
    assert result.returncode == 0, result.stderr
    assert f"UserWarning: {PROBE}" in result.stderr
