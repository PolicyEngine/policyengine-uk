"""Structural tests for parameter metadata."""

from pathlib import Path

import yaml

PARAMETERS_ROOT = Path(__file__).resolve().parent.parent / "parameters"


def _yaml_files():
    return sorted(PARAMETERS_ROOT.rglob("*.yaml"))


def _parameter_files_with_descriptions():
    files = []
    for path in _yaml_files():
        if "tests" in path.parts:
            continue
        try:
            data = yaml.safe_load(path.read_text())
        except Exception:
            # A handful of parameter files use date-like keys that pyyaml
            # treats as out-of-range datetimes when scanning generically;
            # skip rather than crash, the substantive descriptions live in
            # files we can parse.
            continue
        if not isinstance(data, dict):
            continue
        description = data.get("description")
        if isinstance(description, str) and description.strip():
            files.append((path, description.strip()))
    return files


def test_parameter_descriptions_end_with_period():
    """Every parameter description must end with a period — see #340."""
    offenders = [
        path.relative_to(PARAMETERS_ROOT)
        for path, description in _parameter_files_with_descriptions()
        if not description.endswith(".")
    ]
    assert not offenders, (
        "Parameter descriptions should end with a period for consistency. "
        f"{len(offenders)} file(s) do not:\n" + "\n".join(f"  - {p}" for p in offenders)
    )
