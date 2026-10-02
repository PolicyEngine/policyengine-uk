"""Build stable audit units from a released PolicyEngine UK source tree."""

from __future__ import annotations

import ast
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import yaml

from policy_audit.errors import PolicyAuditError
from policy_audit.repository import ReleaseCheckout, source_last_modified_dates
from policy_audit.yaml_utils import load_yaml


PARAMETER_NON_CHILD_KEYS = {
    "description",
    "documentation",
    "metadata",
    "reference",
    "values",
}


@dataclass
class AuditUnit:
    """One variable or logically grouped source parameter."""

    unit_id: str
    kind: str
    source_paths: list[str]
    members: list[str]
    classification: str
    model_last_modified_at: str | None
    variable_dependencies: list[str] = field(default_factory=list)
    parameter_references: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _parameter_members(node: Any, prefix: str) -> list[str]:
    if not isinstance(node, dict):
        return []
    members: list[str] = []
    if "values" in node:
        members.append(prefix)
    brackets = node.get("brackets")
    if isinstance(brackets, list):
        for index, bracket in enumerate(brackets):
            if not isinstance(bracket, dict):
                continue
            for child_name, child in bracket.items():
                if child_name in PARAMETER_NON_CHILD_KEYS:
                    continue
                child_prefix = f"{prefix}[{index}].{child_name}"
                child_members = _parameter_members(child, child_prefix)
                members.extend(child_members or [child_prefix])
    for child_name, child in node.items():
        if child_name in PARAMETER_NON_CHILD_KEYS or child_name == "brackets":
            continue
        if not isinstance(child, dict):
            continue
        child_prefix = f"{prefix}.{child_name}"
        child_members = _parameter_members(child, child_prefix)
        if child_members:
            members.extend(child_members)
    return members


def _parameter_classification(relative_path: Path) -> str:
    parts = relative_path.parts
    if "contrib" in parts:
        return "contributed_reform"
    if parts and parts[0] == "household":
        return "statistical_or_household"
    if any(part in {"economic_assumptions", "dynamic", "simulation"} for part in parts):
        return "assumption"
    if parts and parts[0] == "gov":
        return "policy_rule"
    return "other_parameter"


def _variable_classification(relative_path: Path) -> str:
    parts = relative_path.parts
    if "contrib" in parts:
        return "contributed_reform"
    if parts and parts[0] == "input":
        return "model_input"
    if parts and parts[0] == "gov":
        return "program_formula"
    if parts and parts[0] == "household":
        return "derived_or_statistical"
    return "other_variable"


def _attribute_chain(node: ast.AST, aliases: dict[str, str]) -> str | None:
    if isinstance(node, ast.Name):
        return aliases.get(node.id)
    if isinstance(node, ast.Call):
        function = node.func
        if isinstance(function, ast.Name) and function.id == "parameters":
            return ""
        return None
    if isinstance(node, ast.Attribute):
        parent = _attribute_chain(node.value, aliases)
        if parent is None:
            return None
        return f"{parent}.{node.attr}" if parent else node.attr
    if isinstance(node, ast.Subscript):
        return _attribute_chain(node.value, aliases)
    return None


def _string_values(node: ast.AST) -> list[str]:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return [node.value]
    if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
        values: list[str] = []
        for item in node.elts:
            values.extend(_string_values(item))
        return values
    return []


def _variable_details(class_node: ast.ClassDef) -> tuple[list[str], list[str]]:
    aliases: dict[str, str] = {}
    assignments = [
        node for node in ast.walk(class_node) if isinstance(node, ast.Assign)
    ]
    for _ in range(4):
        changed = False
        for assignment in assignments:
            chain = _attribute_chain(assignment.value, aliases)
            if chain is None:
                continue
            for target in assignment.targets:
                if isinstance(target, ast.Name) and aliases.get(target.id) != chain:
                    aliases[target.id] = chain
                    changed = True
        if not changed:
            break

    parameter_references: set[str] = set()
    variable_dependencies: set[str] = set()
    for node in ast.walk(class_node):
        if isinstance(node, ast.Attribute):
            chain = _attribute_chain(node, aliases)
            if chain and chain.startswith("gov."):
                parameter_references.add(chain)
        if isinstance(node, ast.Call):
            function_name = node.func.id if isinstance(node.func, ast.Name) else None
            if function_name != "parameters" and node.args:
                variable_dependencies.update(_string_values(node.args[0]))
            if function_name == "add" and len(node.args) >= 3:
                variable_dependencies.update(_string_values(node.args[2]))
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id in {
                    "adds",
                    "subtracts",
                    "defined_for",
                }:
                    variable_dependencies.update(_string_values(node.value))

    maximal_references = {
        reference
        for reference in parameter_references
        if not any(
            other != reference and other.startswith(f"{reference}.")
            for other in parameter_references
        )
    }
    variable_dependencies.discard(class_node.name)
    return sorted(variable_dependencies), sorted(maximal_references)


def _variable_classes(path: Path) -> list[tuple[str, list[str], list[str]]]:
    try:
        tree = ast.parse(path.read_text())
    except (OSError, SyntaxError) as error:
        raise PolicyAuditError(
            f"Could not parse variable source {path}: {error}"
        ) from error
    classes: list[tuple[str, list[str], list[str]]] = []
    for node in tree.body:
        if not isinstance(node, ast.ClassDef):
            continue
        bases = {base.id for base in node.bases if isinstance(base, ast.Name)}
        if "Variable" not in bases:
            continue
        dependencies, parameter_references = _variable_details(node)
        classes.append((node.name, dependencies, parameter_references))
    return classes


def build_inventory(release: ReleaseCheckout) -> list[AuditUnit]:
    """Build all source-backed audit units for a release."""

    package_root = release.root / "policyengine_uk"
    units: list[AuditUnit] = []
    modified_dates = source_last_modified_dates(release)

    parameter_root = package_root / "parameters"
    for path in sorted(parameter_root.rglob("*.yaml")):
        relative = path.relative_to(parameter_root)
        dotted_path = ".".join(relative.with_suffix("").parts)
        source_path = path.relative_to(release.root).as_posix()
        try:
            data = load_yaml(path.read_text()) or {}
        except yaml.YAMLError as error:
            raise PolicyAuditError(
                f"Could not parse parameter {path}: {error}"
            ) from error
        members = sorted(set(_parameter_members(data, dotted_path))) or [dotted_path]
        units.append(
            AuditUnit(
                unit_id=f"parameter:{dotted_path}",
                kind="parameter",
                source_paths=[source_path],
                members=members,
                classification=_parameter_classification(relative),
                model_last_modified_at=modified_dates.get(source_path),
            )
        )

    variable_root = package_root / "variables"
    for path in sorted(variable_root.rglob("*.py")):
        if path.name == "__init__.py":
            continue
        relative = path.relative_to(variable_root)
        source_path = path.relative_to(release.root).as_posix()
        modified = modified_dates.get(source_path)
        for name, dependencies, parameter_references in _variable_classes(path):
            units.append(
                AuditUnit(
                    unit_id=f"variable:{name}",
                    kind="variable",
                    source_paths=[source_path],
                    members=[name],
                    classification=_variable_classification(relative),
                    model_last_modified_at=modified,
                    variable_dependencies=dependencies,
                    parameter_references=parameter_references,
                )
            )

    unit_ids = [unit.unit_id for unit in units]
    duplicates = sorted(
        {unit_id for unit_id in unit_ids if unit_ids.count(unit_id) > 1}
    )
    if duplicates:
        raise PolicyAuditError(f"Duplicate audit unit identifiers: {duplicates}")
    return sorted(units, key=lambda unit: unit.unit_id)


def apply_parameter_groups(
    units: list[AuditUnit],
    groups: list[dict[str, Any]],
) -> list[AuditUnit]:
    """Combine multiple parameter documents into curated logical units."""

    by_id = {unit.unit_id: unit for unit in units}
    consumed: set[str] = set()
    grouped: list[AuditUnit] = []
    for index, group in enumerate(groups):
        if not isinstance(group, dict):
            raise PolicyAuditError(f"Parameter group {index} must be an object")
        unit_id = group.get("unit_id")
        member_unit_ids = group.get("units")
        if not isinstance(unit_id, str) or not unit_id.startswith("parameter:"):
            raise PolicyAuditError(
                f"Parameter group {index} must have a parameter: unit_id"
            )
        if not isinstance(member_unit_ids, list) or len(member_unit_ids) < 2:
            raise PolicyAuditError(
                f"Parameter group {unit_id} must name at least two source units"
            )
        source_units: list[AuditUnit] = []
        for member_unit_id in member_unit_ids:
            source_unit = by_id.get(member_unit_id)
            if source_unit is None or source_unit.kind != "parameter":
                raise PolicyAuditError(
                    f"Parameter group {unit_id} names unknown parameter "
                    f"{member_unit_id}"
                )
            if member_unit_id in consumed:
                raise PolicyAuditError(
                    f"Parameter source unit belongs to multiple groups: {member_unit_id}"
                )
            consumed.add(member_unit_id)
            source_units.append(source_unit)
        dates = [
            unit.model_last_modified_at
            for unit in source_units
            if unit.model_last_modified_at
        ]
        classifications = {unit.classification for unit in source_units}
        grouped.append(
            AuditUnit(
                unit_id=unit_id,
                kind="parameter",
                source_paths=sorted(
                    {path for unit in source_units for path in unit.source_paths}
                ),
                members=sorted(
                    {member for unit in source_units for member in unit.members}
                ),
                classification=(
                    classifications.pop()
                    if len(classifications) == 1
                    else "mixed_parameter_group"
                ),
                model_last_modified_at=max(dates) if dates else None,
            )
        )
    result = [unit for unit in units if unit.unit_id not in consumed]
    result.extend(grouped)
    unit_ids = [unit.unit_id for unit in result]
    if len(unit_ids) != len(set(unit_ids)):
        raise PolicyAuditError("A parameter group duplicates an existing audit unit id")
    return sorted(result, key=lambda unit: unit.unit_id)
