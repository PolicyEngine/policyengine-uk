"""Model code must not write in place into arrays read from the simulation.

policyengine-core returns the cached array itself from
``simulation.calculate(...)`` and ``entity("variable", period)``. Writing into
it (``x[mask] = y``, ``x += y``, ``x.fill(0)``, ``np.place(x, ...)``,
``out=x``) changes the cached value behind the engine's back: anything that
reads it before the next ``set_input`` sees half-updated values. Copy first
(``np.array(...)``) or build a new array (``np.where``), then store it with
``set_input``.

Two guards:

- A static scan of every function in the package. It tracks names bound to
  such a call, or to a no-copy alias of one (``np.asarray``, ``.values``,
  ``.view()``, ``x[:]``, plain reassignment), and fails on any in-place write
  to them. Statements are followed in source order and branches are not
  analysed separately, so it can over-report but not under-report for
  straight-line code. It cannot see aliasing through containers or helper
  functions. Writes into projections (``person.benunit("x", period)``) are
  allowed: core builds a new array for those.
- A run-time check that makes every cached array read-only as it is stored and
  runs a simulation through ``Simulation.__init__`` (which applies the UC
  rebalancing modifier), the PIP phase-in scenario, and the code that branches
  a simulation (marginal tax rates, labour supply responses and the capital
  gains realisation response).

Branches raise the stakes: since policyengine-core 3.32.12 a branch shares the
simulation's cached arrays and copies each one only when it first reads it, so
a write in place into one of them after branching also reaches any branch that
has not read it yet.
"""

import ast
from pathlib import Path

import numpy as np
import pytest
from policyengine_core.data_storage import InMemoryStorage

PACKAGE = Path(__file__).resolve().parents[2]
MODEL_CODE = ("scenarios", "variables", "reforms", "utils")

# Calls that return the cached array whatever their arguments.
CACHE_METHODS = {"calculate", "get_array"}
# Entity projections: core builds a new array (values[members_entity_id]).
PROJECTIONS = {"household", "benunit"}
# Methods and attributes that return a view of (or the same) array.
VIEW_METHODS = {"view", "reshape", "ravel", "squeeze", "to_numpy", "transpose"}
VIEW_ATTRIBUTES = {"values", "T"}
NO_COPY_FUNCTIONS = {"asarray", "asanyarray"}
INPLACE_METHODS = {"fill", "sort", "resize", "itemset", "put", "partition"}
INPLACE_FUNCTIONS = {"place", "putmask", "copyto", "put", "put_along_axis"}


def _cached_call(node: ast.AST) -> str | None:
    """Whether a call returns a cached array ("direct") or a new one."""
    if not isinstance(node, ast.Call):
        return None
    func = node.func
    if isinstance(func, ast.Attribute) and func.attr in CACHE_METHODS:
        return "direct"
    if not node.args or not (
        isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str)
    ):
        return None
    if isinstance(func, ast.Name):
        return "direct"  # person("variable", period)
    if isinstance(func, ast.Attribute):
        # benunit.members("variable", period) is the person array itself.
        return "projected" if func.attr in PROJECTIONS else "direct"
    return None


class _FunctionScanner:
    def __init__(self, path: Path, function: ast.FunctionDef):
        self.path = path
        self.function = function
        self.tracked: dict[str, int] = {}  # name -> line bound to a cached array
        self.findings: list[str] = []

    def is_cached(self, node: ast.AST) -> bool:
        """Whether an expression is a cached array or a no-copy alias of one."""
        if isinstance(node, ast.Name):
            return node.id in self.tracked
        if isinstance(node, ast.Attribute) and node.attr in VIEW_ATTRIBUTES:
            return self.is_cached(node.value)
        if isinstance(node, ast.Subscript) and isinstance(node.slice, ast.Slice):
            return self.is_cached(node.value)
        if isinstance(node, ast.Call):
            if _cached_call(node) == "direct":
                return True
            func = node.func
            if isinstance(func, ast.Attribute) and func.attr in VIEW_METHODS:
                return self.is_cached(func.value)
            name = func.attr if isinstance(func, ast.Attribute) else None
            if name is None and isinstance(func, ast.Name):
                name = func.id
            no_copy = name in NO_COPY_FUNCTIONS or (
                name == "array"
                and any(
                    k.arg == "copy"
                    and isinstance(k.value, ast.Constant)
                    and k.value.value is False
                    for k in node.keywords
                )
            )
            if no_copy and node.args:
                return self.is_cached(node.args[0])
        return False

    def report(self, node: ast.AST, how: str) -> None:
        self.findings.append(
            f"{self.path}:{node.lineno} in {self.function.name}(): "
            f"{how} to `{ast.unparse(node)}`, an array read from the simulation"
        )

    def written_array(self, target: ast.AST) -> ast.AST | None:
        """The cached array a subscript target writes into, if any."""
        if isinstance(target, ast.Subscript) and self.is_cached(target.value):
            return target.value
        return None

    def bind(self, target: ast.AST, value: ast.AST | None, line: int) -> None:
        if isinstance(target, ast.Name):
            if value is not None and self.is_cached(value):
                self.tracked[target.id] = line
            else:
                self.tracked.pop(target.id, None)
        elif isinstance(target, (ast.Tuple, ast.List)):
            for element in target.elts:
                self.bind(element, None, line)  # unpacked: not tracked
        elif isinstance(target, ast.Starred):
            self.bind(target.value, None, line)

    def scan_calls(self, statement: ast.stmt) -> None:
        """In-place calls in a statement's own expressions (not nested blocks)."""
        stack = [
            child
            for child in ast.iter_child_nodes(statement)
            if not isinstance(child, (ast.stmt, ast.excepthandler, ast.match_case))
        ]
        while stack:
            node = stack.pop()
            if isinstance(node, (ast.Lambda, ast.FunctionDef, ast.ClassDef)):
                continue
            stack.extend(ast.iter_child_nodes(node))
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            if isinstance(func, ast.Attribute):
                if func.attr in INPLACE_METHODS and self.is_cached(func.value):
                    self.report(func.value, f".{func.attr}()")
                if (
                    func.attr in INPLACE_FUNCTIONS
                    and node.args
                    and self.is_cached(node.args[0])
                ):
                    self.report(node.args[0], f"np.{func.attr}()")
            for keyword in node.keywords:
                if keyword.arg != "out":
                    continue
                outputs = (
                    keyword.value.elts
                    if isinstance(keyword.value, ast.Tuple)
                    else [keyword.value]
                )
                for output in outputs:
                    if self.is_cached(output):
                        self.report(output, "out=")

    def walk(self, statements: list[ast.stmt]) -> None:
        for statement in statements:
            if isinstance(
                statement, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
            ):
                continue  # scanned on its own
            self.scan_calls(statement)
            if isinstance(statement, (ast.Assign, ast.AnnAssign)):
                targets = (
                    statement.targets
                    if isinstance(statement, ast.Assign)
                    else [statement.target]
                )
                for target in targets:
                    array = self.written_array(target)
                    if array is not None:
                        self.report(array, "subscript assignment")
                for target in targets:
                    self.bind(target, statement.value, statement.lineno)
            elif isinstance(statement, ast.AugAssign):
                target = statement.target
                if isinstance(target, ast.Name) and target.id in self.tracked:
                    self.report(target, "augmented assignment")
                else:
                    array = self.written_array(target)
                    if array is not None:
                        self.report(array, "augmented subscript assignment")
            elif isinstance(statement, (ast.For, ast.AsyncFor)):
                self.bind(statement.target, None, statement.lineno)
            elif isinstance(statement, (ast.With, ast.AsyncWith)):
                for item in statement.items:
                    if item.optional_vars is not None:
                        self.bind(item.optional_vars, None, statement.lineno)
            blocks = [
                getattr(statement, field, None) or []
                for field in ("body", "orelse", "finalbody")
            ]
            blocks += [h.body for h in getattr(statement, "handlers", None) or []]
            blocks += [c.body for c in getattr(statement, "cases", None) or []]
            blocks = [b for b in blocks if b and isinstance(b[0], ast.stmt)]
            if blocks:
                # Any block may run or be skipped: a name stays tracked after
                # the statement if it is tracked on any path through it.
                before = dict(self.tracked)
                after = dict(before)
                for block in blocks:
                    self.tracked = dict(before)
                    self.walk(block)
                    after.update(self.tracked)
                self.tracked = after


def scan_source(source: str, path: Path | str = "<source>") -> list[str]:
    findings = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            scanner = _FunctionScanner(path, node)
            scanner.walk(node.body)
            findings += scanner.findings
    return findings


def package_files() -> list[Path]:
    return sorted(PACKAGE.rglob("*.py"))


def test_package_does_not_write_in_place_into_cached_arrays():
    findings = []
    for path in package_files():
        findings += scan_source(path.read_text(), path.relative_to(PACKAGE.parent))
    assert not findings, (
        "Copy arrays read from the simulation before writing into them "
        "(np.array(...)) or build a new array (np.where), then store it with "
        "set_input:\n" + "\n".join(findings)
    )


def test_scan_covers_model_code():
    scanned = {}
    for path in package_files():
        top = path.relative_to(PACKAGE).parts[0]
        scanned[top] = scanned.get(top, 0) + 1
    for directory in MODEL_CODE:
        assert scanned.get(directory, 0) > 0, directory
    assert scanned["variables"] > 500


# Each snippet must be flagged. The first is the UC rebalancing modifier as it
# was before it copied the array.
FLAGGED = {
    "uc rebalancing before the fix": """
def add_universal_credit_reform(sim):
    for year in range(2026, 2030):
        current_health_element = sim.calculate("uc_LCWRA_element", year)
        has_health_element = current_health_element > 0
        current_health_element[has_health_element & ~new] = protected[mask]
        sim.set_input("uc_LCWRA_element", year, current_health_element)
""",
    "pip phase-in before the fix": """
def modify_simulation(sim):
    for year in range(2025, 2030):
        current_pip = sim.calculate("pip", year)
        current_pip[pip_seed < 0.25] = 0
        sim.set_input("pip", year, current_pip)
""",
    "formula subscript": """
def formula(person, period, parameters):
    income = person("employment_income", period)
    income[income < 0] = 0
    return income
""",
    "augmented assignment": """
def formula(person, period, parameters):
    income = person("employment_income", period)
    income += 1
    return income
""",
    "augmented subscript": """
def formula(person, period, parameters):
    income = person("employment_income", period)
    income[0] += 1
""",
    "group members": """
def formula(benunit, period, parameters):
    age = benunit.members("age", period)
    age[age > 100] = 100
""",
    "variable name not a literal": """
def modify(sim):
    for variable in VARIABLES:
        values = sim.calculate(variable, 2026)
        values[values < 0] = 0
""",
    "alias": """
def modify(sim):
    values = sim.calculate("pip", 2026)
    alias = values
    alias[0] = 0
""",
    "np.asarray": """
def modify(sim):
    values = np.asarray(sim.calculate("pip", 2026))
    values[0] = 0
""",
    "np.array copy=False": """
def modify(sim):
    values = np.array(sim.calculate("pip", 2026), copy=False)
    values[0] = 0
""",
    ".values": """
def modify(sim):
    values = sim.calculate("pip", 2026).values
    values[0] = 0
""",
    "write through .values": """
def modify(sim):
    series = sim.calculate("pip", 2026)
    series.values[0] = 0
""",
    "slice view": """
def modify(sim):
    view = sim.calculate("pip", 2026)[:]
    view[0] = 0
""",
    "fill": """
def modify(sim):
    values = sim.calculate("pip", 2026)
    values.fill(0)
""",
    "np.place": """
def modify(sim):
    values = sim.calculate("pip", 2026)
    np.place(values, values < 0, 0)
""",
    "out=": """
def formula(person, period, parameters):
    income = person("employment_income", period)
    np.maximum(income, 0, out=income)
""",
    "inside a branch": """
def modify(sim):
    values = sim.calculate("pip", 2026)
    if True:
        for i in range(3):
            values[i] = 0
""",
    "rebound on one branch only": """
def modify(sim, condition):
    values = sim.calculate("pip", 2026)
    if condition:
        values = values + 1
    values[0] = 0
""",
    "bound inside a branch": """
def modify(sim, condition):
    if condition:
        values = sim.calculate("pip", 2026)
    else:
        values = np.zeros(3)
    values[0] = 0
""",
    "annotated binding": """
def modify(sim):
    values: np.ndarray = sim.calculate("pip", 2026)
    values[0] = 0
""",
}

# None of these may be flagged.
ALLOWED = {
    "uc rebalancing after the fix": """
def add_universal_credit_reform(sim):
    for year in range(2026, 2030):
        current_health_element = np.array(sim.calculate("uc_LCWRA_element", year))
        has_health_element = current_health_element > 0
        current_health_element[has_health_element & ~new] = protected[mask]
        sim.set_input("uc_LCWRA_element", year, current_health_element)
""",
    ".copy()": """
def modify(sim):
    values = sim.calculate("pip", 2026).copy()
    values[0] = 0
""",
    "rebound to a new array": """
def formula(person, period, parameters):
    income = person("employment_income", period)
    income = income + 1
    income[0] = 0
""",
    "np.where": """
def formula(person, period, parameters):
    income = person("employment_income", period)
    capped = np.where(income > 0, income, 0)
    capped[0] = 1
""",
    "fancy index copy": """
def modify(sim):
    values = sim.calculate("pip", 2026)
    positive = values[values > 0]
    positive[0] = 0
""",
    "astype copy": """
def modify(sim):
    values = sim.calculate("pip", 2026).astype(float)
    values += 1
""",
    "projection": """
def formula(person, period, parameters):
    uc = person.benunit("universal_credit", period)
    uc[uc < 0] = 0
""",
    "loop variable rebinds": """
def modify(sim):
    values = sim.calculate("pip", 2026)
    for values in [np.zeros(3)]:
        values[0] = 1
""",
}


@pytest.mark.parametrize("source", FLAGGED.values(), ids=FLAGGED.keys())
def test_scan_flags_in_place_write(source):
    assert scan_source(source)


@pytest.mark.parametrize("source", ALLOWED.values(), ids=ALLOWED.keys())
def test_scan_allows_copy(source):
    assert scan_source(source) == []


YEARS = range(2025, 2030)


def _uc_and_pip_claimant() -> dict:
    return {
        "people": {
            "person": {
                "age": {year: 30 + year - 2025 for year in YEARS},
                "employment_income": {year: 0 for year in YEARS},
                "uc_limited_capability_for_WRA": {year: True for year in YEARS},
                "pip_dl_category": {year: "ENHANCED" for year in YEARS},
            }
        },
        "benunits": {"benunit": {"members": ["person"]}},
        "households": {"household": {"members": ["person"]}},
    }


@pytest.fixture
def read_only_cache(monkeypatch):
    """Make every array read-only as the simulation stores it."""
    original_put = InMemoryStorage.put

    def put(self, value, period, branch_name="default"):
        if isinstance(value, np.ndarray):
            value.flags.writeable = False
        return original_put(self, value, period, branch_name)

    monkeypatch.setattr(InMemoryStorage, "put", put)


@pytest.mark.parametrize("scenario", [None, "reform_pip_phase_in"])
def test_simulation_runs_with_read_only_cache(read_only_cache, scenario):
    from policyengine_uk import Simulation, scenarios

    sim = Simulation(
        situation=_uc_and_pip_claimant(),
        scenario=getattr(scenarios, scenario) if scenario else None,
    )
    for year in YEARS:
        sim.calculate("household_net_income", year)
    # The modifiers ran: the claimant has a health element and PIP.
    assert sim.calculate("uc_LCWRA_element", 2026)[0] > 0
    assert sim.calculate("pip", 2025)[0] > 0


def _earning_couple_with_gains() -> dict:
    members = ["adult_1", "adult_2", "child"]
    return {
        "people": {
            "adult_1": {
                "age": {year: 45 for year in YEARS},
                "employment_income": {year: 60_000 for year in YEARS},
                "capital_gains": {year: 50_000 for year in YEARS},
            },
            "adult_2": {
                "age": {year: 43 for year in YEARS},
                "employment_income": {year: 18_000 for year in YEARS},
            },
            "child": {"age": {year: 7 for year in YEARS}},
        },
        "benunits": {"benunit": {"members": members}},
        "households": {"household": {"members": members}},
    }


BRANCHING_SCENARIOS = {
    "labour_supply_responses": {
        "gov.simulation.labour_supply_responses.substitution_elasticity": 0.25,
        "gov.simulation.labour_supply_responses.income_elasticity": -0.05,
        "gov.hmrc.income_tax.allowances.personal_allowance.amount": 13_070,
    },
    "capital_gains_responses": {
        "gov.simulation.capital_gains_responses.elasticity": 1.0,
        "gov.hmrc.cgt.basic_rate": 0.20,
        "gov.hmrc.cgt.higher_rate": 0.40,
    },
}


@pytest.mark.parametrize(
    "case", ["marginal_rates", "labour_supply_responses", "capital_gains_responses"]
)
def test_branching_runs_with_read_only_cache(read_only_cache, case):
    from policyengine_uk import Simulation
    from policyengine_uk.model_api import Scenario

    if case == "marginal_rates":
        sim = Simulation(situation=_earning_couple_with_gains())
        for year in YEARS:
            sim.calculate("marginal_tax_rate", year)
            sim.calculate("marginal_tax_rate_on_capital_gains", year)
        # The branches ran: both earners face a rate, and so do the gains.
        assert {"adult_1_pay_rise", "adult_2_pay_rise"} <= set(sim.branches)
        assert (sim.calculate("marginal_tax_rate", 2026)[:2] > 0).all()
        assert sim.calculate("marginal_tax_rate_on_capital_gains", 2026)[0] > 0
        return
    changes = {
        name: {str(year): value for year in YEARS}
        for name, value in BRANCHING_SCENARIOS[case].items()
    }
    sim = Simulation(
        situation=_earning_couple_with_gains(),
        scenario=Scenario(parameter_changes=changes),
    )
    for year in YEARS:
        sim.calculate("household_net_income", year)
    if case == "labour_supply_responses":
        assert "lsr_measurement" in sim.branches
    else:
        # The measurement branches are deleted; the response shows they ran.
        assert sim.calculate("capital_gains_behavioural_response", 2026)[0] < 0
