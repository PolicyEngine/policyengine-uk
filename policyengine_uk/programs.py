"""The programme registry and the budget totals built from it.

``programs.yaml`` lists the programmes the model covers. Its ``budget`` fields
also define the budget totals: ``household_tax`` adds every term flagged
``budget: tax`` and ``household_benefits`` every term flagged
``budget: benefit``, in the order ``budget_order`` gives. The headline budget
impact is the change in ``household_tax`` less the change in
``household_benefits``.

This module reads only the YAML file, never the package's top level, so the
variable modules can import it while the tax-benefit system is being built.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache, reduce
from pathlib import Path
from typing import Optional

import yaml

REGISTRY_PATH = Path(__file__).parent / "programs.yaml"

BUDGET_KINDS = ("tax", "benefit")
# The kind of every `programs` entry, and the kinds a `budget_terms` entry
# may take.
PROGRAMME = "programme"
TERM_KINDS = ("programme_measure", PROGRAMME, "reform_measure", "public_service")
# The gov.contrib.benefit_uprating parameters, in the order
# household_benefits applies them, and the default for a benefit term.
UPRATING_PARAMETERS = ("all", "non_sp")


class RegistryError(ValueError):
    """``programs.yaml`` has malformed or inconsistent budget fields."""


@dataclass(frozen=True)
class BudgetProgram:
    """One term of the budget totals.

    Attributes:
        variable: the variable the total adds.
        label: a display name.
        budget: ``"tax"`` for a household_tax term, ``"benefit"`` for a
            household_benefits term.
        group: a key shared by terms that move together, or None.
        kind: ``"programme"``, ``"programme_measure"``, ``"reform_measure"``
            or ``"public_service"`` (see the header of ``programs.yaml``).
            Only the first two measure a programme.
        program: the id of the ``programs`` entry the term measures or
            changes, or None.
        dropped_when: path of a boolean parameter that removes the term from
            its total while true, or None.
        uprating: the gov.contrib.benefit_uprating parameters that scale the
            term; empty for taxes.
    """

    variable: str
    label: str
    budget: str
    group: Optional[str]
    kind: str
    program: Optional[str]
    dropped_when: Optional[str]
    uprating: tuple

    @property
    def is_tax(self) -> bool:
        return self.budget == "tax"

    @property
    def is_programme(self) -> bool:
        return self.kind in (PROGRAMME, "programme_measure")


@lru_cache(maxsize=1)
def load_registry() -> dict:
    """The parsed ``programs.yaml``."""
    return yaml.safe_load(REGISTRY_PATH.read_text())


def _term(entry: dict, kind: str, program: Optional[str]) -> BudgetProgram:
    variable = entry["variable"]
    budget = entry["budget"]
    if budget not in BUDGET_KINDS:
        raise RegistryError(
            f"{variable}: budget must be tax or benefit, not {budget!r}"
        )
    if "budget_uprating" in entry:
        if budget != "benefit":
            raise RegistryError(f"{variable}: only benefit terms take budget_uprating")
        uprating = tuple(entry["budget_uprating"])
        unknown = set(uprating) - set(UPRATING_PARAMETERS)
        if unknown:
            raise RegistryError(
                f"{variable}: unknown budget_uprating {sorted(unknown)}"
            )
    else:
        uprating = UPRATING_PARAMETERS if budget == "benefit" else ()
    group = entry.get("group")
    if group is not None and not isinstance(group, str):
        raise RegistryError(f"{variable}: group must be a string")
    return BudgetProgram(
        variable=variable,
        label=entry["name"],
        budget=budget,
        group=group,
        kind=kind,
        program=program,
        dropped_when=entry.get("budget_dropped_when"),
        uprating=uprating,
    )


@lru_cache(maxsize=1)
def budget_programs() -> tuple:
    """Every term of the budget totals, as ``BudgetProgram`` records.

    The household_tax terms come first, then the household_benefits terms,
    each in the order the total adds them. The result is the same on every
    call; it raises ``RegistryError`` if the registry's budget fields
    disagree with ``budget_order``.
    """
    return build_budget_programs(load_registry())


def build_budget_programs(registry: dict) -> tuple:
    """The budget terms of a parsed registry; see ``budget_programs``."""
    programme_ids = {entry["id"] for entry in registry["programs"]}
    terms = {}

    def add(term):
        if term.variable in terms:
            raise RegistryError(f"{term.variable} carries a budget flag twice")
        terms[term.variable] = term

    for entry in registry["programs"]:
        if "budget" in entry:
            if "variable" not in entry:
                raise RegistryError(f"{entry['id']}: a budget entry needs a variable")
            add(_term(entry, PROGRAMME, entry["id"]))
    for entry in registry.get("budget_terms", []):
        kind = entry.get("kind")
        if kind not in TERM_KINDS:
            raise RegistryError(f"{entry['variable']}: unknown kind {kind!r}")
        program = entry.get("program")
        if program is not None and program not in programme_ids:
            raise RegistryError(f"{entry['variable']}: unknown program {program!r}")
        if kind == "programme_measure" and program is None:
            raise RegistryError(
                f"{entry['variable']}: a programme_measure needs a program"
            )
        add(_term(entry, kind, program))

    ordered = []
    order = registry["budget_order"]
    for budget in BUDGET_KINDS:
        listed = order[budget]
        flagged = [t.variable for t in terms.values() if t.budget == budget]
        if len(set(listed)) != len(listed):
            raise RegistryError(f"budget_order.{budget} repeats a variable")
        if set(listed) != set(flagged):
            raise RegistryError(
                f"budget_order.{budget} and the entries flagged budget: {budget} "
                f"differ: only ordered {sorted(set(listed) - set(flagged))}, "
                f"only flagged {sorted(set(flagged) - set(listed))}"
            )
        ordered.extend(terms[variable] for variable in listed)
    return tuple(ordered)


def budget_variables(budget: str) -> list:
    """The variables a budget total adds, in order.

    ``budget`` is ``"tax"`` (household_tax) or ``"benefit"``
    (household_benefits). Returns a new list on each call.
    """
    if budget not in BUDGET_KINDS:
        raise ValueError(f"budget must be tax or benefit, not {budget!r}")
    return [term.variable for term in budget_programs() if term.budget == budget]


def _parameter_is_true(parameters_at_instant, path: str) -> bool:
    return bool(reduce(getattr, path.split("."), parameters_at_instant))


def budget_variables_in_effect(budget: str, parameters_at_instant) -> list:
    """The variables a budget total adds under the given parameters.

    Leaves out each term whose ``budget_dropped_when`` parameter is true,
    and keeps the order of ``budget_variables``.
    """
    return [
        term.variable
        for term in budget_programs()
        if term.budget == budget
        and not (
            term.dropped_when
            and _parameter_is_true(parameters_at_instant, term.dropped_when)
        )
    ]


def uprated_benefit_variables(benefits: list, uprating_parameter: str) -> list:
    """The entries of ``benefits`` that ``uprating_parameter`` scales.

    ``uprating_parameter`` is ``"all"`` or ``"non_sp"``, a child of
    gov.contrib.benefit_uprating. Keeps the order of ``benefits``.
    """
    if uprating_parameter not in UPRATING_PARAMETERS:
        raise ValueError(f"unknown uprating parameter {uprating_parameter!r}")
    scaled = {
        term.variable
        for term in budget_programs()
        if uprating_parameter in term.uprating
    }
    return [benefit for benefit in benefits if benefit in scaled]
