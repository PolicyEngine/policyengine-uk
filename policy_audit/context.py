"""Build bounded program context for one audit unit."""

from __future__ import annotations

from collections import deque
from pathlib import Path
import re
from typing import Any

import yaml

from policy_audit.errors import PolicyAuditError
from policy_audit.yaml_utils import load_yaml


def load_programs(release_root: Path) -> list[dict[str, Any]]:
    """Load the program registry from the selected release."""

    path = release_root / "policyengine_uk" / "programs.yaml"
    if not path.exists():
        return []
    try:
        data = load_yaml(path.read_text()) or {}
    except (OSError, yaml.YAMLError) as error:
        raise PolicyAuditError(f"Could not load program registry: {error}") from error
    programs = data.get("programs")
    if not isinstance(programs, list):
        raise PolicyAuditError("programs.yaml does not contain a programs list")
    return programs


def _source_policy_path(unit: dict[str, Any], source_kind: str) -> tuple[str, ...]:
    source_path = Path(unit["source_paths"][0])
    marker = "parameters" if source_kind == "parameter" else "variables"
    try:
        index = source_path.parts.index(marker)
    except ValueError:
        return ()
    relative = source_path.parts[index + 1 :]
    if not relative:
        return ()
    return (*relative[:-1], Path(relative[-1]).stem)


def _headline_directories(
    programs: list[dict[str, Any]],
    units: list[dict[str, Any]],
) -> dict[str, tuple[str, ...]]:
    variable_sources = {
        unit["members"][0]: _source_policy_path(unit, "variable")
        for unit in units
        if unit["kind"] == "variable" and unit.get("members")
    }
    directories: dict[str, tuple[str, ...]] = {}
    for program in programs:
        variable = program.get("variable")
        source = variable_sources.get(variable)
        if source:
            directories[program["id"]] = source[:-1]
    return directories


def resolve_program(
    unit: dict[str, Any],
    programs: list[dict[str, Any]],
    units: list[dict[str, Any]],
    overrides: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Resolve program ownership without conflating downstream use."""

    overrides = overrides or {}
    override = overrides.get(unit["unit_id"])
    if override:
        program = next((item for item in programs if item.get("id") == override), None)
        if program is None:
            raise PolicyAuditError(
                f"Program override for {unit['unit_id']} names unknown program {override}"
            )
        return {"status": "confirmed", "method": "override", "program": program}

    if unit["kind"] == "parameter":
        parameter_path = unit["unit_id"].removeprefix("parameter:")
        candidates: list[tuple[int, dict[str, Any]]] = []
        for program in programs:
            prefix = program.get("parameter_prefix")
            if prefix and (
                parameter_path == prefix or parameter_path.startswith(f"{prefix}.")
            ):
                candidates.append((len(prefix.split(".")), program))
        if candidates:
            candidates.sort(key=lambda item: item[0], reverse=True)
            length, program = candidates[0]
            ties = [item for item in candidates if item[0] == length]
            if len(ties) > 1:
                return {
                    "status": "program_mapping_required",
                    "method": "ambiguous_parameter_prefix",
                    "candidates": [item[1]["id"] for item in ties],
                }
            status = "confirmed" if length >= 3 else "provisional"
            return {
                "status": status,
                "method": "parameter_prefix",
                "program": program,
            }

    if unit["kind"] == "variable":
        variable_name = unit["members"][0]
        exact = [
            program for program in programs if program.get("variable") == variable_name
        ]
        if len(exact) == 1:
            return {
                "status": "confirmed",
                "method": "headline_variable",
                "program": exact[0],
            }
        source = _source_policy_path(unit, "variable")
        directories = _headline_directories(programs, units)
        matches = [
            (len(directory), program)
            for program in programs
            for directory in [directories.get(program["id"])]
            if directory and source[: len(directory)] == directory
        ]
        if matches:
            matches.sort(key=lambda item: item[0], reverse=True)
            length, program = matches[0]
            ties = [item for item in matches if item[0] == length]
            if len(ties) == 1:
                return {
                    "status": "confirmed",
                    "method": "headline_source_directory",
                    "program": program,
                }
            return {
                "status": "program_mapping_required",
                "method": "ambiguous_source_directory",
                "candidates": [item[1]["id"] for item in ties],
            }

    return {
        "status": "program_mapping_required",
        "method": "unmapped",
        "candidates": [],
    }


def _component(unit: dict[str, Any], ownership: dict[str, Any]) -> str | None:
    program = ownership.get("program")
    if not program:
        return None
    source = _source_policy_path(unit, unit["kind"])
    if unit["kind"] == "parameter":
        prefix = tuple(str(program.get("parameter_prefix", "")).split("."))
        if prefix and source[: len(prefix)] == prefix:
            remainder = source[len(prefix) :]
            return ".".join(remainder) or program.get("name")
    if len(source) >= 2:
        return ".".join(source[-2:-1]) or program.get("name")
    return program.get("name")


def _parameter_matches(reference: str, parameter_path: str) -> bool:
    return (
        reference == parameter_path
        or reference.startswith(f"{parameter_path}.")
        or reference.startswith(f"{parameter_path}[")
        or parameter_path.startswith(f"{reference}.")
    )


def _shortest_path(
    start: str,
    destination: str,
    downstream: dict[str, set[str]],
) -> list[str]:
    queue: deque[list[str]] = deque([[start]])
    visited = {start}
    while queue:
        path = queue.popleft()
        current = path[-1]
        if current == destination:
            return path
        for next_name in sorted(downstream.get(current, set())):
            if next_name not in visited:
                visited.add(next_name)
                queue.append([*path, next_name])
    return []


def _related_tests(release_root: Path, needles: set[str]) -> list[str]:
    tests_root = release_root / "policyengine_uk" / "tests"
    matches: list[str] = []
    for path in sorted(tests_root.rglob("*")):
        if path.suffix not in {".py", ".yaml", ".yml"} or not path.is_file():
            continue
        try:
            text = path.read_text()
        except UnicodeDecodeError:
            continue
        if any(
            needle
            and re.search(
                rf"(?<![A-Za-z0-9_]){re.escape(needle)}(?![A-Za-z0-9_])", text
            )
            for needle in needles
        ):
            matches.append(path.relative_to(release_root).as_posix())
    return matches


def _related_documentation(release_root: Path, source_paths: list[str]) -> list[str]:
    documents: set[str] = set()
    for source_path in source_paths:
        current = (release_root / source_path).parent
        while current != release_root and release_root in current.parents:
            readme = current / "README.md"
            if readme.exists():
                documents.add(readme.relative_to(release_root).as_posix())
            if current.name in {"parameters", "variables"}:
                break
            current = current.parent
    return sorted(documents)


def build_program_context(
    release_root: Path,
    catalog: dict[str, Any],
    unit_id: str,
    overrides: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Return a bounded calculation and program context for one unit."""

    units = catalog["units"]
    by_id = {unit["unit_id"]: unit for unit in units}
    target = by_id.get(unit_id)
    if target is None:
        raise PolicyAuditError(f"Unknown audit unit: {unit_id}")
    programs = catalog["programs"]
    ownership = resolve_program(target, programs, units, overrides)

    variables = {
        unit["members"][0]: unit
        for unit in units
        if unit["kind"] == "variable" and unit.get("members")
    }
    downstream: dict[str, set[str]] = {}
    for variable_name, unit in variables.items():
        for dependency in unit.get("variable_dependencies", []):
            downstream.setdefault(dependency, set()).add(variable_name)

    if target["kind"] == "parameter":
        parameter_path = target["unit_id"].removeprefix("parameter:")
        direct_readers = {
            name
            for name, variable in variables.items()
            if any(
                _parameter_matches(reference, parameter_path)
                for reference in variable.get("parameter_references", [])
            )
        }
        starting_variables = set(direct_readers)
        calculation_variables = set(starting_variables)
    else:
        variable_name = target["members"][0]
        direct_readers = {variable_name}
        starting_variables = {variable_name}
        calculation_variables = set(starting_variables)
        calculation_variables.update(
            dependency
            for dependency in variables.get(variable_name, {}).get(
                "variable_dependencies", []
            )
            if dependency in variables
        )

    program = ownership.get("program")
    headline = program.get("variable") if program else None
    paths_to_headline: list[list[str]] = []
    if headline in variables:
        for variable_name in sorted(starting_variables):
            path = _shortest_path(variable_name, headline, downstream)
            if path:
                paths_to_headline.append(path)
                calculation_variables.update(path)
        calculation_variables.add(headline)

    external_consumers: list[dict[str, Any]] = []
    for variable_name in sorted(direct_readers):
        variable = variables[variable_name]
        consumer_owner = resolve_program(variable, programs, units, overrides)
        consumer_program = consumer_owner.get("program")
        if (
            consumer_program
            and program
            and consumer_program.get("id") != program.get("id")
        ):
            external_consumers.append(
                {
                    "variable": variable_name,
                    "program_id": consumer_program["id"],
                    "program_name": consumer_program["name"],
                }
            )

    slice_units = [target]
    slice_units.extend(
        variables[name]
        for name in sorted(calculation_variables)
        if variables[name]["unit_id"] != target["unit_id"]
    )
    source_paths = sorted(
        {path for unit in slice_units for path in unit.get("source_paths", [])}
    )
    needles = {
        unit_id.split(":", 1)[1],
        *target.get("members", []),
        *direct_readers,
    }

    return {
        "release_version": catalog["release_version"],
        "audit_unit": target,
        "owning_program": ownership,
        "component": _component(target, ownership),
        "direct_readers": sorted(direct_readers),
        "paths_to_headline_variable": paths_to_headline,
        "headline_path_status": (
            "resolved"
            if paths_to_headline
            else "dynamic_or_unresolved"
            if headline in variables
            else "no_registered_headline_variable"
        ),
        "calculation_slice": [
            {
                "unit_id": unit["unit_id"],
                "source_paths": unit["source_paths"],
                "variable_dependencies": unit.get("variable_dependencies", []),
                "parameter_references": unit.get("parameter_references", []),
            }
            for unit in slice_units
        ],
        "external_consumers": external_consumers,
        "related_tests": _related_tests(release_root, needles),
        "related_documentation": _related_documentation(release_root, source_paths),
        "scope_note": (
            "This context covers the target, its direct calculation inputs, shortest "
            "paths to the headline program variable, and external consumers. It does "
            "not certify the complete program."
        ),
    }
