"""Structural tests for parameter metadata."""

from pathlib import Path
from datetime import date

import pytest
import yaml

PARAMETERS_ROOT = Path(__file__).resolve().parent.parent / "parameters"


class _DescriptionLoader(yaml.SafeLoader):
    """Inspect prose without constructing datetime objects for policy date keys."""


_DescriptionLoader.add_constructor(
    "tag:yaml.org,2002:timestamp",
    lambda loader, node: loader.construct_scalar(node),
)


def _yaml_files():
    return sorted(PARAMETERS_ROOT.rglob("*.yaml"))


def _parameter_files_with_descriptions():
    files = []
    errors = []
    for path in _yaml_files():
        if "tests" in path.parts:
            continue
        try:
            data = yaml.load(path.read_text(), Loader=_DescriptionLoader)
        except (OSError, UnicodeError, yaml.YAMLError) as error:
            errors.append(f"{path.relative_to(PARAMETERS_ROOT)}: {error}")
            continue
        if data is None and path.name == "index.yaml":
            data = {}
        if not isinstance(data, dict):
            errors.append(f"{path.relative_to(PARAMETERS_ROOT)}: expected a mapping")
            continue
        required = "values" in data or "brackets" in data
        if "values" in data and "brackets" in data:
            errors.append(
                f"{path.relative_to(PARAMETERS_ROOT)}: both values and brackets"
            )
        if "values" in data and not isinstance(data["values"], dict):
            errors.append(
                f"{path.relative_to(PARAMETERS_ROOT)}: values must be a mapping"
            )
        if "brackets" in data and not isinstance(data["brackets"], list):
            errors.append(
                f"{path.relative_to(PARAMETERS_ROOT)}: brackets must be a list"
            )
        if "description" not in data and not required:
            continue
        description = data.get("description")
        if not isinstance(description, str) or not description.strip():
            errors.append(
                f"{path.relative_to(PARAMETERS_ROOT)}: description must be a nonempty string"
            )
            continue
        files.append((path, description.strip()))
    assert not errors, "Invalid parameter description metadata:\n" + "\n".join(errors)
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


@pytest.mark.parametrize(
    "contents",
    [
        "description: Missing final punctuation\nvalues:\n  0000-01-01: 1\n",
        "description: [invalid YAML\n",
        "values:\n  2026-01-01: 1\n",
        "description: '  '\nvalues:\n  2026-01-01: 1\n",
        "description: true\nvalues:\n  2026-01-01: 1\n",
        "description: 2\nvalues:\n  2026-01-01: 1\n",
        "description: null\nvalues:\n  2026-01-01: 1\n",
        "description: [A description.]\nvalues:\n  2026-01-01: 1\n",
        "brackets: []\n",
        "- Not a parameter mapping.\n",
        "description: A scale.\nbrackets: {}\n",
        "description: A value.\nvalues: []\n",
        "description: Ambiguous record.\nvalues: {}\nbrackets: []\n",
    ],
    ids=[
        "zero-year-punctuation",
        "malformed-yaml",
        "missing-scalar-description",
        "blank-description",
        "boolean-description",
        "numeric-description",
        "null-description",
        "list-description",
        "missing-scale-description",
        "sequence-root",
        "invalid-brackets-shape",
        "invalid-values-shape",
        "ambiguous-value-and-scale",
    ],
)
def test_description_checker_reports_invalid_file(tmp_path, monkeypatch, contents):
    parameter = tmp_path / "invalid.yaml"
    parameter.write_text(contents)
    monkeypatch.setitem(globals(), "PARAMETERS_ROOT", tmp_path)

    with pytest.raises(AssertionError, match="invalid.yaml"):
        test_parameter_descriptions_end_with_period()


@pytest.mark.parametrize(
    "filename,contents,expected_description",
    [
        (
            "value.yaml",
            "description: A dated value.\nvalues:\n  0000-01-01: 1\n",
            "A dated value.",
        ),
        (
            "value.yaml",
            "description: A dated value.\nvalues:\n  2026-01-01: true\n",
            "A dated value.",
        ),
        (
            "scale.yaml",
            "description: A scale.\nbrackets:\n  - threshold: {2026-01-01: 0}\n    rate: {2026-01-01: 0.2}\n",
            "A scale.",
        ),
        ("index.yaml", "metadata: {label: A container}\n", None),
        ("table.yaml", "CHILD:\n  values: {2026-01-01: 1}\n", None),
        (
            "table.yaml",
            "description: A table.\nCHILD:\n  values: {2026-01-01: 1}\n",
            "A table.",
        ),
        (
            "value.yaml",
            "<<: &defaults\n  description: An inherited description.\nvalues: {2026-01-01: 1}\n",
            "An inherited description.",
        ),
        (
            "value.yaml",
            "description: Superseded text\ndescription: Effective text.\nvalues: {2026-01-01: 1}\n",
            "Effective text.",
        ),
    ],
    ids=[
        "zero-year",
        "ordinary-date",
        "scale",
        "index",
        "nested-table",
        "described-table",
        "yaml-merge",
        "duplicate-description",
    ],
)
def test_description_checker_preserves_supported_shapes(
    tmp_path, monkeypatch, filename, contents, expected_description
):
    parameter = tmp_path / filename
    parameter.write_text(contents)
    monkeypatch.setitem(globals(), "PARAMETERS_ROOT", tmp_path)

    test_parameter_descriptions_end_with_period()
    expected = (
        [] if expected_description is None else [(parameter, expected_description)]
    )
    assert _parameter_files_with_descriptions() == expected


def test_description_check_keeps_global_safe_loader_types(tmp_path, monkeypatch):
    sample = "when: 2026-01-01\nenabled: true\namount: 2.5\noptional: null\n"
    before = yaml.safe_load(sample)
    parameter = tmp_path / "value.yaml"
    parameter.write_text("description: A dated value.\nvalues: {0000-01-01: 1}\n")
    monkeypatch.setitem(globals(), "PARAMETERS_ROOT", tmp_path)

    test_parameter_descriptions_end_with_period()

    assert yaml.safe_load(sample) == before
    assert isinstance(before["when"], date)
    assert before["enabled"] is True
    assert isinstance(before["amount"], float)
    assert before["optional"] is None
    with pytest.raises(ValueError, match="year 0"):
        yaml.safe_load("when: 0000-01-01\n")
